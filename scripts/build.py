#!/usr/bin/env python3
"""Atlas Mayab V1: exportación determinista desde el Excel maestro. Python estándar solamente.
El Excel maestro conserva 20 hojas originales V1.1 y tablas auxiliares MA.*.
NO publicar sin revisión de permisos, privacidad e identidad institucional.
Uso: python scripts/build.py   [--check]
"""
from __future__ import annotations
import csv, hashlib, io, json, re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parent.parent
MASTER=ROOT/'private'/'02_ATLAS_MAESTRO_MAYAB_V1.0_2026-11-20.xlsx'
OUT=ROOT/'site'/'data'
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RID='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
DATE='2026-11-20'
VERSION='1.0'
EXPECTED={'investigaciones':249,'preguntas':365,'rutas':1157,'conceptos':30,'vinculos_co':126,'vinculos_heredados':6,'historico':5270,'descartes':2730,'agenda':36,'cotejos':747}

class Book:
    def __init__(self, path:Path):
        self.path=Path(path); self.z=zipfile.ZipFile(self.path)
        if self.z.testzip() is not None: raise ValueError('XLSX CRC defectuoso')
        self.shared=[]
        if 'xl/sharedStrings.xml' in self.z.namelist():
            rt=ET.fromstring(self.z.read('xl/sharedStrings.xml'))
            self.shared=[''.join(t.text or '' for t in si.iter(NS+'t')) for si in rt.findall(NS+'si')]
        root=ET.fromstring(self.z.read('xl/workbook.xml'))
        rel=ET.fromstring(self.z.read('xl/_rels/workbook.xml.rels'))
        relationships={item.get('Id'):item.get('Target').lstrip('/') for item in rel}
        self.sheets={}
        for sheet in root.find(NS+'sheets'):
            path=relationships.get(sheet.get(RID+'id'))
            if not path:continue
            path=path if path.startswith('xl/') else 'xl/'+path
            self.sheets[sheet.get('name')]=path
    @staticmethod
    def col_idx(ref):
        s=re.match('^[A-Z]+',ref).group(0); n=0
        for c in s:n=n*26+ord(c)-64
        return n-1
    def table(self,name):
        if name not in self.sheets: raise ValueError(f'Falta hoja {name} en maestro')
        root=ET.fromstring(self.z.read(self.sheets[name]))
        lines=[]
        for row in root.iter(NS+'row'):
            values={}
            for cell in row.findall(NS+'c'):
                index=self.col_idx(cell.get('r'))
                v=cell.find(NS+'v'); t=cell.get('t'); inline=cell.find(NS+'is')
                if t=='s' and v is not None: value=self.shared[int(v.text)]
                elif t=='inlineStr' and inline is not None: value=''.join(x.text or '' for x in inline.iter(NS+'t'))
                elif v is not None:value=v.text or ''
                else:value=''
                values[index]=value
            if values: lines.append((int(row.get('r')),values))
        if not lines:return []
        headers=lines[0][1]
        items=[]
        for rownum, values in lines[1:]:
            if not any(str(x).strip() for x in values.values()):continue
            item={str(header):str(values.get(index,'')).strip() for index,header in headers.items() if header}
            item['_row']=rownum
            items.append(item)
        return items

def unique(rows,key,table):
    ids=[row.get(key,'') for row in rows]
    if not all(ids):raise ValueError(f'{table} tiene IDs vacíos')
    if len(ids)!=len(set(ids)):raise ValueError(f'{table} tiene IDs duplicados')

def req(ok,msg):
    if not ok:raise ValueError(msg)

def safe_csv_cell(v):
    s=str(v if v is not None else '')
    if s.startswith(('=','+','-','@','\t','\r')):return "'"+s
    return s

def save_csv(path,records,fields):
    with open(path,'w',encoding='utf-8-sig',newline='') as fp:
        writer=csv.DictWriter(fp,fields,extrasaction='ignore');writer.writeheader()
        for r in records:writer.writerow({f:safe_csv_cell(r.get(f,'')) for f in fields})

def transform(book:Book):
    p0=book.table('01_PROPUESTAS_249'); q0=book.table('02_PREGUNTAS_365')
    r0=book.table('03_RUTAS_1157'); c0=book.table('05_CONCEPTOS_30')
    l0=book.table('15_VINCULOS_CO_V11');h0=book.table('04_ENLACES_CO_6')
    pr0=book.table('13_PROPUESTAS_CO_V11');qr0=book.table('14_PREGUNTAS_CO_V11')
    historic=book.table('06_HISTORICO_5270'); disc=book.table('07_DESCARTES_2730')
    agenda=book.table('08_AGENDA_36'); compare=book.table('09_COTEJOS_747')
    sources=book.table('10_FUENTES')+book.table('19_FUENTES_NUEVAS_V11')
    for k,a in [('investigaciones',p0),('preguntas',q0),('rutas',r0),('conceptos',c0),('vinculos_co',l0),('vinculos_heredados',h0),('historico',historic),('descartes',disc),('agenda',agenda),('cotejos',compare)]:
        req(len(a)==EXPECTED[k],f'Conteo inválido {k}: {len(a)} ≠ {EXPECTED[k]}')
    for arr,key,n in [(p0,'id_propuesta','propuestas'),(q0,'id_pregunta','preguntas'),(r0,'id_relacion','rutas'),(c0,'ID_CONCEPTO','conceptos'),(l0,'id_relacion_documental','links nuevos'),(h0,'ID_RELACION_NUEVO','links antiguos'),(pr0,'id_propuesta_original','revisión propuestas'),(qr0,'id_pregunta_original','revisión preguntas'),(compare,'id_enlace','cotejos'),(historic,'Folio','históricos'),(disc,'Folio','descartes')]:unique(arr,key,n)
    unique(sources,'id_fuente','fuentes')
    ids_sources={s['id_fuente'] for s in sources}
    historical_ids={h['Folio'] for h in historic}
    pd={x['id_propuesta']:x for x in p0}; qd={x['id_pregunta']:x for x in q0}
    cd={x['ID_CONCEPTO']:x for x in c0}
    pdr={x['id_propuesta_original']:x for x in pr0};qdr={x['id_pregunta_original']:x for x in qr0}
    req(set(pd)==set(pdr),'Diferencia de IDs propuesta V1.1 vs V1')
    req(set(qd)==set(qdr),'Diferencia de IDs pregunta V1.1 vs V1')
    req(len({x['id_investigacion_normalizado'] for x in p0})==249,'Crosswalk investigación no único')
    for q in q0:req(q['id_propuesta'] in pd,'Pregunta huérfana '+q['id_pregunta'])
    for route in r0:
        req(route['id_propuesta'] in pd and route['id_pregunta'] in qd,'Ruta huérfana '+route['id_relacion'])
        req(qd[route['id_pregunta']]['id_propuesta']==route['id_propuesta'],'Ruta propuesta-pregunta no coincidente '+route['id_relacion'])
        req(route['alcance']==qd[route['id_pregunta']]['alcance'],'Ruta alcance incorrecto '+route['id_relacion'])
    req(len({(r['id_propuesta'],r['id_pregunta'],r['id_sector']) for r in r0})==1157,'Triples rutas repetidos')
    for r in compare:
        req(r['id_propuesta'] in pd,'Cotejo PROP sin FK '+r['id_enlace'])
        req(r['folio_IY'] in historical_ids,'Cotejo folio histórico sin FK '+r['id_enlace'])
    for a in agenda:req(a['ID propuesta'] in pd,'Propuesta de agenda no contenida en 249: '+a['ID propuesta'])
    for x in l0:
        req(x['id_propuesta_origen'] in pd and x['id_concepto_co'] in cd,'Vínculo CO FK inexistente '+x['id_relacion_documental'])
        if x['tipo_origen']=='PREGUNTA':req(x['id_pregunta_origen'] in qd and qd[x['id_pregunta_origen']]['id_propuesta']==x['id_propuesta_origen'],'Vínculo pregunta FK inválido '+x['id_relacion_documental'])
        elif x['tipo_origen']!='PROPUESTA':raise ValueError('Tipo de vínculo desconocido '+x['tipo_origen'])
        co=cd[x['id_concepto_co']]
        req(x['nivel']==co['Nivel'] and x['etapa']==co['Etapa'],'Vínculo nivel/etapa erróneo '+x['id_relacion_documental'])
        req(x['grado_correspondencia'] in ('directo','razonado','parcial'),'Grado CO inesperado '+x['id_relacion_documental'])
        parent = pdr[x['id_propuesta_origen']] if x['tipo_origen']=='PROPUESTA' else qdr[x['id_pregunta_origen']]
        if x['grado_correspondencia'] in ('directo','razonado'):
            req(parent['estado_co_v11'] in ('directo','razonado'),'Vínculo sobresale de estado general '+x['id_relacion_documental'])
        req(x['justificacion_individual'] and x['localizador_libro_impreso'] and x['fuentes_id'],'Vínculo sin respaldo específico '+x['id_relacion_documental'])
        for f in x['fuentes_id'].split(';'):
            req(f.strip() in ids_sources,'Vínculo sin fuente catalogada '+x['id_relacion_documental']+': '+f)
    for x in h0:req(x['ID_PROP_ORIGEN'] in pd and x['ID_CONCEPTO'] in cd,'Vínculo heredado inválido')
    for x in q0:req(x['alcance'] in ('DES','CAU'),'Alcance fuera contrato')
    req(Counter(x['alcance'] for x in q0)=={'DES':249,'CAU':116},'Distribución 249/116 inválida')
    req(Counter(x['id_propuesta'] for x in q0 if x['alcance']=='DES')=={id:1 for id in pd},'Cada propuesta debe tener una DES única')
    req({(x['Nivel'],x['Etapa']) for x in c0}=={(n,s) for n in ('IND','GRU','ORG') for s in ('INS','PRO','RES')},'Matriz 3x3 incompleta')
    req(Counter(x['estado_co_v11'] for x in pr0)=={'directo':7,'razonado':7,'parcial':18,'pendiente':18,'fuera_del_modelo':199},'Desglose V1.1 propuestas diferente')
    req(Counter(x['estado_co_v11'] for x in qr0)=={'directo':13,'razonado':12,'parcial':25,'pendiente':25,'fuera_del_modelo':290},'Desglose V1.1 preguntas diferente')
    req(Counter(x['grado_correspondencia'] for x in l0)=={'directo':39,'razonado':19,'parcial':68},'Desglose vínculos CO diferente')
    # Verificación bibliográfica V1.1 (p. 31) preservando la fuente de V1 sin editarla.
    concepts=[]
    for x in c0:
        pag=x['Página impresa']; corrected=x['ID_CONCEPTO'] in ('CO-00027','CO-00028')
        if corrected: pag='31'
        concepts.append(dict(id=x['ID_CONCEPTO'],nombre=x['Concepto normalizado'],etapa=x['Etapa'],nivel=x['Nivel'],definicion=x['Definición parafraseada'],indicador=x['Indicador posible NO validado'],unidad=x['Unidad de análisis'],capitulo=x['Capítulo'],pagina=pag,diapositiva=x['Diapositiva'],estado='pendiente_revision_docente',cita=f"Robbins y Judge (2017), cap. {x['Capítulo']}, p. {pag} impresa",correccion_v11='Corregida en revisión documental V1.1, p. 3 del informe' if corrected else '',pagina_heredada=x['Página impresa'] if corrected else '',hoja_origen=x['hoja_origen'],fila_origen=x['fila_origen']))
    investigations=[]; themes={}; problems={}
    for x in p0:
        state=pdr[x['id_propuesta']]; inv_id=x['id_investigacion_normalizado']
        req(inv_id==state['id_investigacion_normalizado'],'Crosswalk inconsistente '+x['id_propuesta'])
        themes[x['id_tema_especifico']]={'id':x['id_tema_especifico'],'linea':x['id_linea'],'general':x['tema_general'],'nombre':x['tema_especifico']}
        problems[x['id_problema']]={'id':x['id_problema'],'tema_id':x['id_tema_especifico'],'texto':x['problema']}
        investigations.append(dict(id=inv_id,original=x['id_propuesta'],linea=x['id_linea'],tema_id=x['id_tema_especifico'],tema_general=x['tema_general'],tema_especifico=x['tema_especifico'],problema_id=x['id_problema'],problema=x['problema'],titulo=x['titulo_original'],sector_principal_id=x['id_sector_principal'],sector_principal=x['sector_original'],territorio=x['territorio'],unidad=x['unidad_analisis'],indicadores=x['variables_originales'],metodo=x['metodo'],evidencia=x['evidencia'],fuentes_ids=x['fuentes'],estado_co=state['estado_co_v11'],justificacion=state['justificacion_individual'],evidencia_requerida=state['evidencia_requerida'],procedimiento=state['procedimiento_dictamen'],estado_academico=state['estado_academico'],estado_publicacion=state['estado_publicacion'],concepto_principal=state['id_concepto_principal'],fuente_libro=state['libro_localizador_impreso'],diapositiva=state['diapositiva_docente'],archivo_origen=x['archivo_origen'],hoja_origen=x['hoja_origen'],fila_origen=x['fila_origen'],hash_fila=x['hash_fila_datos_origen'],version_dictamen='V1.1',fecha_corte=DATE))
    questions=[]
    for x in q0:
        st=qdr[x['id_pregunta']]
        req(x['id_propuesta']==st['id_propuesta_original'],'Crosswalk pregunta V1.1 inconsistente '+x['id_pregunta'])
        questions.append(dict(id=x['id_pregunta'],prop=x['id_propuesta'],inv=x['id_investigacion_normalizado'],alcance=x['alcance'],texto=x['texto_base'],unidad=x['unidad_analisis_fuente'],indicadores=x['indicadores_sugeridos_fuente'],x=x['exposicion'],y=x['resultado'],confusores=x['confusores'],temporalidad=x['temporalidad_contrafactual'],diseno=x['diseno_candidato'],estado_co=st['estado_co_v11'],concepto_principal=st['id_concepto_principal'],justificacion=st['justificacion_individual'],cita=st['libro_localizador_impreso'],diapositiva=st['diapositiva_docente'],hipotesis_no_verificada=st['hipotesis_documental_no_verificada'],comparacion_exigida=st['comparacion_exigida'],temporalidad_exigida=st['temporalidad_exigida'],supuestos=st['supuestos_y_limitaciones'],evidencia_necesaria=st['evidencia_necesaria'],veredicto_causal=st['veredicto_causal'],estado_academico=st['estado_academico'],estado_causal='candidata_no_validada' if x['alcance']=='CAU' else 'no_aplica',hoja_origen=x['hoja_origen'],fila_origen=x['fila_origen'],hash_fila=x['hash_fila_datos_origen']))
    routes=[dict(id=x['id_relacion'],prop=x['id_propuesta'],pregunta=x['id_pregunta'],alcance=x['alcance'],sector_id=x['id_sector'],sector=x['sector'],territorio=x['territorio'],contexto=x['pregunta_contextualizada'],fuentes=x['fuentes'],hoja_origen=x['hoja_origen'],fila_origen=x['fila_origen'],hash_fila=x['hash_fila_datos_origen']) for x in r0]
    sector_map={}
    conflict=[]
    for x in routes:
        if x['sector_id'] in sector_map and sector_map[x['sector_id']]['nombre']!=x['sector']:conflict.append(x['sector_id'])
        sector_map[x['sector_id']]={'id':x['sector_id'],'nombre':x['sector']}
    req(not conflict, f'Etiquetas sector diferentes para mismos IDs {set(conflict)}')
    links=[dict(id=x['id_relacion_documental'],tipo=x['tipo_origen'],prop=x['id_propuesta_origen'],pregunta=x['id_pregunta_origen'],concepto_id=x['id_concepto_co'],nivel=x['nivel'],etapa=x['etapa'],grado=x['grado_correspondencia'],senal=x['señal_evidencia'],justificacion=x['justificacion_individual'],fuentes_ids=x['fuentes_id'],cita=x['localizador_libro_impreso'],diapositiva=x['localizador_diapositiva'],procedimiento=x['procedimiento'],revision=x['revision_academica'],visibilidad=x['explorador2_local'],publicacion=x['publicacion'],causalidad=x['causalidad'],version=x['version'],fecha=x['fecha']) for x in l0]
    heritage_links=[dict(id=x['ID_RELACION_NUEVO'],prop=x['ID_PROP_ORIGEN'],concepto_id=x['ID_CONCEPTO'],grado=x['Estado'].lower(),justificacion=x['Justificación específica'],cita=x['Fuente y página'],diapositiva=x['Diapositiva'],revision=x['Dictamen'],hoja_origen=x['hoja_origen'],fila_origen=x['fila_origen']) for x in h0]
    ref_sources=[]
    for x in sources:
        ref_sources.append(dict(id=x['id_fuente'],tipo=x['tipo'],apa=x['referencia_apa7'],localizador=x['localizador'],url=x['url_verificada'],doi=x['doi'],limite=x.get('limites',x.get('limitaciones','')),verificacion=x['alcance_verificacion']))
    hist=[dict(folio=x['Folio'],tema=x['Tema'],problema=x['Problema'],sector=x['Sector'],titulo=x['Título de investigación']) for x in historic]
    themes=sorted(themes.values(),key=lambda r:(r['general'],r['nombre'],r['id']))
    problems=sorted(problems.values(),key=lambda r:r['id'])
    sectors=sorted(sector_map.values(),key=lambda r:r['nombre'])
    territories=sorted({r['territorio'] for r in routes if r['territorio']})
    return dict(meta=dict(version=VERSION,corte=DATE,uso='Investigación académica preliminar para revisión docente',publicacion='NO AUTORIZADA',aviso='Ninguna pregunta causal representa un efecto probado. Los enlaces CO son provisionales.',conteos=EXPECTED,clasificacion_investigaciones=dict(Counter(x['estado_co'] for x in investigations)),clasificacion_preguntas=dict(Counter(x['estado_co'] for x in questions)),clasificacion_vinculos=dict(Counter(x['grado'] for x in links)),estado_causal='0 de 116 candidatas con identificación validada',municipios='Sin catálogo normalizado aprobado; territorio literal preservado'),investigaciones=investigations,preguntas=questions,rutas=routes,conceptos=concepts,vinculos_co=links,vinculos_heredados=heritage_links,temas=themes,problemas=problems,sectores=sectors,territorios=territories,fuentes=ref_sources,historico=hist)

def write_outputs(data):
    OUT.mkdir(parents=True,exist_ok=True)
    json_text=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
    (OUT/'atlas.json').write_text(json_text,encoding='utf-8')
    (OUT/'atlas-data.js').write_text('/* Autoexportado: no editar. Fuente: Excel maestro; v1.0. */\nwindow.ATLAS_DATA='+json_text.rstrip()+';\n',encoding='utf-8')
    save_csv(OUT/'investigaciones.csv',data['investigaciones'],['id','original','tema_general','tema_especifico','problema','titulo','estado_co','territorio','sector_principal'])
    save_csv(OUT/'preguntas.csv',data['preguntas'],['id','prop','alcance','texto','estado_co','estado_causal'])
    save_csv(OUT/'vinculos_co.csv',data['vinculos_co'],['id','tipo','prop','pregunta','concepto_id','nivel','etapa','grado','cita','diapositiva','justificacion'])
    print('Exportados JSON/JS/3 CSV deterministas')
    print('Conteos:',', '.join(f'{k}={len(data[k])}' for k in EXPECTED if k in data))
    return hashlib.sha256(json_text.encode()).hexdigest()

def main():
    req(MASTER.is_file(),f'No existe maestro {MASTER}')
    data=transform(Book(MASTER))
    # --check valida la copia de Excel sin sobreescribir las exportaciones
    if '--check' not in sys.argv:
        print('SHA256 atlas.json:',write_outputs(data))
    else:
        existing=json.loads((OUT/'atlas.json').read_text(encoding='utf-8'))
        req(data==existing,'JSON publicado NO coincide con Excel maestro: ejecutar build.py')
        print('OK, datos públicos iguales a maestro; conteos, PK, FK, 3×3, estados y referencias conformes')
    return data
if __name__=='__main__':main()
