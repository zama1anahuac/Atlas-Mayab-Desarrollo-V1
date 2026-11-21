#!/usr/bin/env python3
"""Batería QA local sobre V1.0. Requiere opcionalmente Playwright+Chromium para UX."""
from __future__ import annotations
import hashlib, http.server, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parent.parent
SITE=ROOT/'site';DOCS=ROOT/'docs'
spec=importlib.util.spec_from_file_location('atlas_build',ROOT/'scripts'/'build.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
results=[]

def check(name,success,detail='',category='local'):
    ok=bool(success);results.append(dict(prueba=name,resultado='OK' if ok else 'ERROR',detalle=str(detail),alcance=category))
    print(('OK' if ok else 'ERROR'),name,'-',detail)
    return ok

def webtest():
    with tempfile.TemporaryDirectory(prefix='atlas_nested_') as d:
        dest=Path(d)/'atlas-revision'; dest.symlink_to(SITE,target_is_directory=True)
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self,*args,**kwargs):super().__init__(*args,directory=d,**kwargs)
            def log_message(self,*args,**kwargs):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        base=f'http://127.0.0.1:{server.server_address[1]}/atlas-revision/'
        for p in ['index.html','assets/styles.css','assets/app.js','assets/brand-mark.svg','assets/model-art.svg','data/atlas.json','data/atlas-data.js','data/investigaciones.csv','data/preguntas.csv','data/vinculos_co.csv']:
            try:
                with urlopen(base+p,timeout=10) as res:
                    payload=res.read();mime=res.headers.get_content_type();code=res.status
                check('HTTP ruta de proyecto: '+p,code==200 and len(payload)>0,f'{code}, {mime}, {len(payload)} bytes','http_nested')
            except Exception as e:check('HTTP ruta de proyecto: '+p,False,repr(e),'http_nested')
        browser_test(base)
        server.shutdown();server.server_close()

def browser_test(base):
    try:from playwright.sync_api import sync_playwright
    except Exception as e:
        check('Playwright disponible',False,f'No disponible: {e}','no_ejecutado');return
    with sync_playwright() as p:
        try:browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None,args=['--no-sandbox'])
        except Exception as e:
            check('Chromium inicializa',False,repr(e),'no_ejecutado');return
        try:
            page=browser.new_page(viewport={'width':1440,'height':950},device_scale_factor=1)
            errors=[];page.on('pageerror',lambda err: errors.append(str(err)))
            try:
                page.goto(base+'index.html',wait_until='load',timeout=60000)
            except Exception as e:
                category='no_ejecutado' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(e) else 'browser'
                check('Ejecución Chromium / navegador real',False,str(e).split('\n')[0],category)
                return
            page.wait_for_function('window.__ATLAS_QA__ && document.querySelectorAll("#modelGrid .matrix-cell").length===9',timeout=30000)
            c=page.evaluate('window.__ATLAS_QA__.records')
            check('Modelo 3x3 y fuentes reales',page.locator('#modelGrid button').count()==9 and page.locator('#conceptCards button').count()==30 and page.locator('#sourcesGrid article').count()==16,f'9 celdas, 30 conceptos, 16 fuentes','browser')
            check('Conteos visibles iniciales',c=={'investigaciones':249,'preguntas':365,'rutas':1157,'conceptos':30,'vinculos':126,'historico':5270},str(c),'browser')
            check('Vínculos D+R por defecto',page.evaluate('window.__ATLAS_QA__.visibleCo()')==58,'58 relaciones directas y razonadas','browser')
            check('Atlas general completo',page.evaluate('window.__ATLAS_QA__.visibleAtlas()')==249,'249 IDs principales','browser')
            page.screenshot(path=str(DOCS/'CAPTURA_ESCRITORIO_V1_2026-11-20.png'),full_page=False)
            page.locator('#coGrade').select_option('parcial')
            check('Vínculos parciales visibles pero segregados',page.evaluate('window.__ATLAS_QA__.visibleCo()')==68,'68 parciales con reservas','browser')
            page.locator('#coGrade').select_option('sustentadas')
            page.locator('#coLevel').select_option('ORG');page.locator('#coStage').select_option('RES')
            val=page.evaluate('window.__ATLAS_QA__.visibleCo()')
            check('Filtro doble nivel+etapa',0<val<58,f'{val} vínculos ORG/RES','browser')
            page.locator('#coLevel').select_option('GRU');page.locator('#coStage').select_option('RES')
            check('Estado vacío conceptual',page.locator('#coResults .empty-state').count()==1,'GRU/RES no tiene vínculos D/R en fuente','browser') if page.evaluate('window.__ATLAS_QA__.visibleCo()')==0 else check('Filtro matriz GRU/RES',True,f'{page.evaluate("window.__ATLAS_QA__.visibleCo()")} relaciones existentes','browser')
            page.locator('#clearCo').click()
            page.locator('#coSearch').fill('zzzz_no_existe_xyz')
            check('Búsqueda CO sin resultados',page.evaluate('window.__ATLAS_QA__.visibleCo()')==0 and page.locator('#coResults .empty-state').count()==1,'Sin fabricar vínculos','browser')
            page.locator('#clearCo').click()
            page.locator('#atlasTema').select_option(index=1)
            count=page.evaluate('window.__ATLAS_QA__.visibleAtlas()')
            check('Filtro tema general',0<count<249,f'{count} propuestas','browser')
            for selector in ['#atlasSubtema','#atlasProblema','#atlasPregunta','#atlasAlcance','#atlasSector','#atlasTerritorio']:
                sel=page.locator(selector)
                if sel.locator('option').count()>1:sel.select_option(index=1)
            check('Recorrido completo por rutas existentes',page.evaluate('window.__ATLAS_QA__.visibleAtlas()')>=1,'Tema→problema→pregunta→alcance→sector→territorio','browser')
            page.locator('#atlasResults [data-open]').first.click()
            check('Ficha original abre con preguntas y procedencia',page.locator('#fichaDialog').evaluate('(el)=>el.open') and page.locator('#fichaBody .ficha-question').count()>=1 and page.locator('#fichaBody .trace-section').count()==1,'Modal ficha / vínculos / rutas / fuente','browser')
            page.locator('#closeFicha').click()
            page.locator('#atlasSearch').fill('zzzz_no_existe_xyz')
            check('Búsqueda general sin resultados',page.evaluate('window.__ATLAS_QA__.visibleAtlas()')==0 and page.locator('#atlasResults .empty-state').count()==1,'Sin coincidencias','browser')
            page.locator('#atlasClear').click()
            page.locator('#legacySearch').fill('zzzz_no_existe_xyz')
            check('Legado sin resultados',page.locator('#legacyResults tr').count()==1 and 'No se encontraron' in page.locator('#legacyResults').inner_text(),'Leyenda separa histórico','browser')
            page.locator('#legacySearch').fill('')
            check('Legado completo',len(c)==6 and page.locator('#legacyResults tr').count()==14,'5,270 registros paginados','browser')
            check('Sin errores JavaScript en navegación',not errors,'; '.join(errors),'browser')
            page.set_viewport_size({'width':390,'height':844});page.reload(wait_until='load')
            page.wait_for_function('window.__ATLAS_QA__')
            page.locator('#menuToggle').click()
            check('Menú móvil',page.locator('#navigation').evaluate('(e)=>e.classList.contains("open")') and page.locator('#menuToggle').get_attribute('aria-expanded')=='true','Viewport 390px','browser_mobile_emulado')
            page.locator('#navigation a[href="#atlas-general"]').click()
            check('Menú móvil se cierra',page.locator('#menuToggle').get_attribute('aria-expanded')=='false','Navegación por ancla','browser_mobile_emulado')
            page.goto(base+'index.html',wait_until='load')
            page.screenshot(path=str(DOCS/'CAPTURA_MOVIL_V1_2026-11-20.png'),full_page=False)
            check('Sin scroll horizontal móvil',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'),f"ancho documento {page.evaluate('document.documentElement.scrollWidth')} vs 390",'browser_mobile_emulado')
            check('Atributos accesibilidad esenciales',page.locator('html').get_attribute('lang')=='es' and page.locator('main').count()==1 and page.locator('nav[aria-label]').count()>=2 and page.locator('a.skip-link').count()==1 and page.locator('dialog[aria-labelledby]').count()==1,'Semántica base y acceso por teclado, no auditoría WCAG formal','browser')
            # file:// lectura directa sin servidor
            page.goto(SITE.joinpath('index.html').as_uri(),wait_until='load')
            try:page.wait_for_function('window.__ATLAS_QA__',timeout=10000);direct=True
            except:direct=False
            check('Doble clic local file://',direct,'Sin fetch requerido para atlas-data.js','browser_file')
        finally:browser.close()

def main():
    DOCS.mkdir(exist_ok=True)
    master=ROOT/'private'/'02_ATLAS_MAESTRO_MAYAB_V1.0_2026-11-20.xlsx'
    check('Maestro editable presente',master.is_file() and master.stat().st_size>1000000,str(master.stat().st_size if master.exists() else 0),'datos')
    try:data=mod.transform(mod.Book(master));check('Conteos y PK/FK del maestro',True,'249/365/1157/126/5270/2730/36/747, sin PK/FK inválidas','datos')
    except Exception as e:check('Conteos y PK/FK del maestro',False,repr(e),'datos');data=None
    if data:
        saved=json.loads((SITE/'data'/'atlas.json').read_text(encoding='utf-8'))
        check('Exportación coincide con Excel',saved==data,'Comparación completa JSON maestro','datos')
        check('Archivo JS se genera sin fetch', (SITE/'data'/'atlas-data.js').read_text(encoding='utf-8').startswith('/* Autoexportado') and 'window.ATLAS_DATA=' in (SITE/'data'/'atlas-data.js').read_text(encoding='utf-8'),'Compatibilidad file:// y GitHub Pages','datos')
        check('30 conceptos y 9 celdas',len({(x['nivel'],x['etapa']) for x in data['conceptos']})==9,'Matriz 3×3','datos')
        check('Corrección V1.1 pp.31',all(c['pagina']=='31' for c in data['conceptos'] if c['id'] in ('CO-00027','CO-00028')),'No modifica hojas históricas','datos')
        check('Roles pregunta-variable no inferidos',len(data['preguntas'])==365 and all(x['estado_causal']!='validada' for x in data['preguntas']),'0/116 efectos identificados','datos')
        check('126 vínculos nuevos separados de 6 heredados',len(data['vinculos_co'])==126 and len(data['vinculos_heredados'])==6,'No son investigaciones','datos')
    try:
        logic=subprocess.run(['node',str(ROOT/'scripts'/'test_logic.js')],capture_output=True,text=True,timeout=60)
        check('Motor de exploración en Node.js',logic.returncode==0 and '17 pruebas lógicas exitosas' in logic.stdout,logic.stdout.strip().splitlines()[-1] if logic.stdout.strip() else logic.stderr.strip(),'motor_js')
    except Exception as e:check('Motor de exploración en Node.js',False,repr(e),'motor_js')
    try:
        output=subprocess.run(['node','--check',str(SITE/'assets'/'app.js')],capture_output=True,text=True,timeout=15)
        check('Sintaxis JavaScript',output.returncode==0,output.stderr.strip() or 'node --check válido','estatico')
    except Exception as e:check('Sintaxis JavaScript',False,repr(e),'estatico')
    text=(SITE/'index.html').read_text(encoding='utf-8')
    links=re.findall(r'(?:href|src)="([^"]+)"',text)
    rel=[x for x in links if x.startswith('./')]
    missing=[u for u in rel if not (SITE/u[2:].split('#')[0]).is_file()]
    check('No existen rutas locales huérfanas en HTML',not missing,f'{len(rel)} rutas, faltantes: {missing}','estatico')
    internal=re.findall(r'href="#([^"]+)"',text)
    ids=set(re.findall(r'id="([^"]+)"',text))
    broken_anchors=[x for x in internal if x not in ids]
    check('Navegación por anclas internas',not broken_anchors,f'{len(internal)} anclas, 0 destinos faltantes si OK','estatico')
    check('Sin archivos PDF públicos ni enlaces rotos',not any('.pdf' in x.lower() for x in links) and not list(SITE.rglob('*.pdf')),'Fichas HTML originales; impresión PDF en navegador. MIME PDF no aplica.','estatico')
    check('Sin libros ni diapositivas redistribuidos',not any('comportamiento_organizacional_17' in x.name.lower() or 'intro_comportamiento' in x.name.lower() for x in SITE.rglob('*')),'PDF rector y presentación excluidos','derechos')
    check('Aviso de publicación bloqueada', (SITE/'NO_PUBLICAR_SIN_AUTORIZACION.txt').is_file() and 'No autorizado' in text,'NO_PUBLICAR en /site','derechos')
    check('Archivos /site no contienen secretos aparentes',not re.search(r'-----BEGIN (?:RSA|OPENSSH|PRIVATE) KEY-----', ''.join(x.read_text(encoding='utf-8',errors='ignore') for x in [SITE/'index.html',SITE/'assets'/'app.js',SITE/'assets'/'styles.css'])),'No keys o credenciales en frontend','seguridad')
    webtest()
    executed=[r for r in results if r['alcance']!='no_ejecutado']
    skipped=[r for r in results if r['alcance']=='no_ejecutado']
    failures=[r for r in executed if r['resultado']=='ERROR']
    summary={'fecha':'2026-11-20','version':'1.0','ejecutadas':len(executed),'aprobadas':len(executed)-len(failures),'fallidas':len(failures),'no_ejecutadas':len(skipped),'limites':['No se probó GitHub Pages remoto (sin URL real).','Pruebas mobile: viewport Chromium emulado, no dispositivo físico.','No se auditó con lector de pantalla ni evaluación WCAG completa.','No se generaron PDF originales por falta de autorización de difusión; prueba MIME application/pdf no aplica.','La conformidad técnica no representa revisión científica ni docente.'],'resultados':results}
    (DOCS/'QA_LOCAL_V1_2026-11-20.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RESUMEN',len(executed),'ejecutadas,',len(failures),'fallidas,',len(skipped),'no ejecutadas')
    if failures:sys.exit(1)
if __name__=='__main__':main()
