#!/usr/bin/env python3
"""Genera manifiesto SHA256 determinista del árbol de entrega, excluyendo el manifiesto mismo."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs'/'MANIFIESTO_V1_2026-11-20.json'
files=[]
for p in sorted(ROOT.rglob('*')):
    if p.is_file() and p!=OUT and not p.name.endswith('.pyc') and '__pycache__' not in p.parts:
        rel=p.relative_to(ROOT).as_posix()
        with p.open('rb') as fp: digest=hashlib.file_digest(fp,'sha256').hexdigest()
        files.append({'ruta':rel,'tamano_bytes':p.stat().st_size,'sha256':digest,'visibilidad':'sitio_tecnico_no_autorizado_publicar' if rel.startswith('site/') else 'privado_o_control'})
obj={'version':'1.0','corte':'2026-11-20','caracter':'Entrega técnica privada, no aprobada, no publicar','archivos_incluidos':len(files),'bytes_total_sin_manifest':sum(f['tamano_bytes'] for f in files),'algoritmo':'SHA-256','nota':'Este manifiesto se excluye de su propia lista para evitar autorreferencia; el ZIP se calcula aparte','files':files}
OUT.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manifiesto',len(files),'archivos',sum(f['tamano_bytes'] for f in files),'bytes')
