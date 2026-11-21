#!/usr/bin/env python3
"""Pruebas de la interfaz en Chromium con DOM y assets inyectados en memoria.
No navega a URLs (el sandbox bloquea localhost y file://). Valida interacción real del
navegador, CSS y teclado; NO equivale a un despliegue HTTP o GitHub Pages real.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import re,base64,json,sys
ROOT=Path(__file__).resolve().parent.parent
SITE=ROOT/'site'
DOCS=ROOT/'docs'
assert SITE.is_dir()
checks=[]
def ck(test,good,detail=''):
 checks.append({'prueba':test,'estado':'OK' if good else 'ERROR','detalle':detail})
 print(('OK' if good else 'ERROR'),test,detail)

def prepare(page):
 html=(SITE/'index.html').read_text(encoding='utf-8')
 html=re.sub(r'<script[^>]*src="[^"]+"[^>]*></script>','',html)
 # Assets are embedded as data URIs so visual checks still contain the correct original SVG.
 for img in ['assets/brand-mark.svg','assets/model-art.svg']:
  blob=(SITE/img).read_bytes()
  html=html.replace('./'+img,'data:image/svg+xml;base64,'+base64.b64encode(blob).decode('ascii'))
 page.set_content(html,wait_until='load')
 page.add_style_tag(content=(SITE/'assets/styles.css').read_text(encoding='utf-8'))
 for item in ['data/atlas-data.js','assets/engine.js','assets/app.js']:
  page.add_script_tag(content=(SITE/item).read_text(encoding='utf-8'))
 page.wait_for_function('typeof window.__ATLAS_QA__ === "object"')

def run():
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  page=browser.new_page(viewport={'width':1366,'height':900},device_scale_factor=1)
  errors=[]
  page.on('pageerror',lambda err:errors.append(str(err)))
  prepare(page)
  qa=lambda name:page.evaluate('window.__ATLAS_QA__.'+name+'()')
  ck('Inicialización navegador Chromium real',page.locator('h1').count()==1 and page.title().startswith('Atlas Mayab'))
  ck('Matriz 3×3 y 30 constructos',page.locator('.matrix-cell').count()==9 and page.locator('.concept-card').count()==30)
  ck('CO por defecto: 58 vínculos directos/razonados',qa('visibleCo')==58,str(qa('visibleCo')))
  ck('Atlas general: 249 propuestas únicas',qa('visibleAtlas')==249,str(qa('visibleAtlas')))
  ck('Catálogo histórico paginado',page.locator('#legacyResults tr').count()==14)
  ck('Imagen original renderizable',page.locator('.hero-visual img').evaluate('(el)=>el.complete && el.naturalWidth>0'))
  page.locator('.skip-link').focus()
  ck('Enlace saltar al contenido visible con foco',page.locator('.skip-link').evaluate('(el)=>document.activeElement===el && el.getBoundingClientRect().top>=0'))
  page.locator('#coGrade').select_option('parcial')
  ck('CO con reservas: 68 vínculos parciales',qa('visibleCo')==68)
  page.locator('#coGrade').select_option('sustentadas')
  page.locator('#coLevel').select_option('ORG')
  page.locator('#coStage').select_option('RES')
  x=qa('visibleCo')
  ck('CO filtra nivel + etapa reales',0<x<58,str(x))
  page.locator('#coLevel').select_option('GRU')
  page.locator('#coStage').select_option('RES')
  ck('CO caso vacío sin vínculos inventados',qa('visibleCo')==0 and page.locator('#coResults .empty-state').count()==1)
  page.locator('#clearCo').click()
  page.locator('#coSearch').fill('zzzz_no_coincide_987654')
  ck('CO buscador sin resultados',qa('visibleCo')==0 and page.locator('.empty-state').count()>=1)
  page.locator('#clearCo').click()
  page.locator('#modelGrid .model-row').nth(2).locator('button').nth(1).click()
  ck('CO matriz gráfica interactiva',qa('activeCo')['level']=='ORG' and qa('activeCo')['stage']=='PRO')
  page.locator('#clearCo').click()
  page.locator('#modelGrid .model-row').first.locator('button').first.focus()
  page.keyboard.press('Enter')
  ck('Matriz operable por teclado Enter',qa('activeCo')['level']=='IND' and qa('activeCo')['stage']=='INS')
  page.locator('#clearCo').click()
  page.locator('#atlasTema').select_option(index=1)
  before=qa('visibleAtlas')
  ck('General tema restringe',0<before<249,str(before))
  for key in ['atlasSubtema','atlasProblema','atlasPregunta','atlasAlcance','atlasSector','atlasTerritorio']:
   loc=page.locator('#'+key)
   if loc.locator('option').count()>1:loc.select_option(index=1)
  ck('Recorrido completo a través de rutas reales',qa('visibleAtlas')>=1,str(qa('visibleAtlas')))
  page.locator('#atlasResults [data-open]').first.click()
  ck('Ficha abierta con preguntas y procedencia',page.locator('#fichaDialog').evaluate('(el)=>el.open') and page.locator('#fichaBody .ficha-question').count()>=1 and page.locator('.trace-section').count()==1)
  ck('Ficha oculta salto CO si la propuesta carece de vínculos',page.locator('#goCoFromFicha').is_hidden() if page.locator('#fichaBody').inner_text().find('Sin correspondencia')>=0 else True,'El primer filtro no garantiza un caso sin vínculo')
  page.locator('#goAtlasFromFicha').click()
  ck('Ficha enlaza a Atlas general sin ID nuevo',qa('visibleAtlas')==1 and not page.locator('#fichaDialog').evaluate('(el)=>el.open'))
  page.locator('#atlasClear').click()
  page.locator('#atlasSearch').fill('PROP-011')
  page.locator('#atlasResults [data-open]').first.click()
  ck('Sin vínculo CO no muestra botón de salto',page.locator('#goCoFromFicha').is_hidden())
  page.locator('#closeFicha').click()
  page.locator('#atlasClear').click()
  page.locator('#atlasSearch').fill('PROP-101')
  ck('Búsqueda de ID original',qa('visibleAtlas')==1,str(qa('visibleAtlas')))
  page.locator('#atlasResults [data-open]').first.click()
  ck('Ficha con CO propone salto a Explorador 2',page.locator('#goCoFromFicha').is_visible())
  import fitz
  pdf_bytes=page.pdf(format='A4',print_background=True)
  pdf_text=' '.join(p.get_text() for p in fitz.open(stream=pdf_bytes,filetype='pdf'))
  ck('Impresión a PDF de ficha original',pdf_bytes.startswith(b'%PDF') and len(pdf_bytes)>5000 and 'PROP-101' in pdf_text,f'{len(pdf_bytes)} bytes, test de exportación sin archivo público')
  p=page.locator('#fichaBody .ficha-question').count()
  ck('Preguntas en ficha no duplicadas por vínculos',p==len([q for q in json.loads((SITE/'data/atlas.json').read_text(encoding='utf-8'))['preguntas'] if q['prop']=='PROP-101']),str(p))
  page.locator('#goCoFromFicha').click()
  n=qa('visibleCo')
  ck('Transición Atlas general → CO mismo ID',qa('activeCo')['query']=='PROP-101' and n>0,str(n))
  ck('Transición muestra reservas parciales',qa('activeCo')['grade']=='todos')
  page.locator('#coResults [data-open]').first.click()
  ck('Ficha vuelve desde CO al mismo ID',page.locator('#fichaBody').inner_text().find('PROP-101')>=0)
  page.locator('#closeFicha').click()
  page.locator('#clearCo').click()
  page.locator('#atlasClear').click()
  page.locator('#atlasSearch').fill('zzzz_no_existe_98765')
  ck('General estado vacío sin filas inventadas',qa('visibleAtlas')==0 and page.locator('#atlasResults .empty-state').count()==1)
  page.locator('#atlasClear').click()
  page.locator('#legacySearch').fill('zzzz_no_existe_98765')
  ck('Archivo histórico estado vacío',page.locator('#legacyResults tr').count()==1 and 'No se encontraron' in page.locator('#legacyResults').inner_text())
  page.locator('#legacySearch').fill('')
  page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
  page.screenshot(path=str(DOCS/'REVISION_PANTALLA_ESCRITORIO_V1_2026-11-20.png'),full_page=False)
  ck('Sin errores JS en flujo escritorio',not errors,'; '.join(errors))
  for width in [320,375,390,768,1024,1366]:
   page.set_viewport_size({'width':width,'height':850})
   dim=page.evaluate('({content:document.documentElement.scrollWidth,window:window.innerWidth})')
   ck(f'Viewport {width}px sin scroll horizontal',dim['content']<=dim['window']+1,str(dim))
   if width==390:
    page.locator('#menuToggle').click()
    ck('Menú móvil revela navegación y aria-expanded',page.locator('#navigation').evaluate('(el)=>el.classList.contains("open")') and page.locator('#menuToggle').get_attribute('aria-expanded')=='true')
    page.locator('#navigation a[href="#atlas-general"]').click()
    ck('Cierra menú móvil al navegar',page.locator('#menuToggle').get_attribute('aria-expanded')=='false')
    page.locator('#atlasResults [data-open]').first.click()
    ck('Ficha móvil dentro de pantalla',page.locator('#fichaDialog').evaluate('(e)=>e.getBoundingClientRect().width <= innerWidth && e.getBoundingClientRect().height <= innerHeight+1'))
    page.keyboard.press('Escape')
    ck('Cerrar ficha con Escape',not page.locator('#fichaDialog').evaluate('(e)=>e.open'))
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
    page.screenshot(path=str(DOCS/'REVISION_PANTALLA_MOVIL_V1_2026-11-20.png'),full_page=False)
  ck('Sin fallos JavaScript durante vistas móviles',not errors,'; '.join(errors))
  # Robust graceful failure: not silently empty when dataset missing.
  blank=browser.new_page()
  html=(SITE/'index.html').read_text(encoding='utf-8')
  html=re.sub(r'<script[^>]*src="[^"]+"[^>]*></script>','',html)
  blank.set_content(html)
  blank.add_script_tag(content=(SITE/'assets/app.js').read_text(encoding='utf-8'))
  ck('Aviso comprensible ante falta de base de datos','No fue posible cargar' in blank.locator('#coResultCount').inner_text())
  blank.close();browser.close()
 result={'metodo':'Chromium con DOM, CSS, SVG y scripts reales inyectados en memoria; sin navegación real por bloqueo del entorno','fecha':'2026-11-20','conteo':len(checks),'exitosas':sum(x['estado']=='OK' for x in checks),'fallidas':[x for x in checks if x['estado']!='OK'],'pruebas':checks,'limites':['No valida solicitudes HTTP de navegador ni URL GitHub Pages real','Dispositivo móvil emulado, no hardware físico','No se ejecutaron pruebas de lector de pantalla','La carga mediante file:// no se pudo probar extremo a extremo']}
 (DOCS/'QA_NAVEGADOR_03_V1_2026-11-20.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('RESUMEN',result['exitosas'],'/',result['conteo'])
 if result['fallidas']:sys.exit(1)
if __name__=='__main__':run()
