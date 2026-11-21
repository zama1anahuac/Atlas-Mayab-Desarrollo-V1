// Pruebas reproducibles del motor exacto utilizado por el frontend (sin DOM ni navegador).
'use strict';
const fs=require('fs');const assert=require('assert');const path=require('path');
const root=path.resolve(__dirname,'..');
const engine=require(path.join(root,'site','assets','engine.js'));
const data=JSON.parse(fs.readFileSync(path.join(root,'site','data','atlas.json'),'utf8'));
const core=engine.create(data),f=(g={})=>core.filterCo({grade:'sustentadas',...g});
let passed=0;
function test(name,callback){callback();passed++;console.log('OK',name)}
test('Modelo 3×3 con 30 conceptos',()=>assert.equal(new Set(data.conceptos.map(c=>c.nivel+'-'+c.etapa)).size,9));
test('249 propuestas y 365 preguntas, 1157 rutas',()=>assert.deepEqual([data.investigaciones.length,data.preguntas.length,data.rutas.length],[249,365,1157]));
test('58 vínculos CO nuevos D/R',()=>assert.equal(f().length,58));
test('68 vínculos parciales separados',()=>assert.equal(f({grade:'parcial'}).length,68));
test('126 vínculos CO completos',()=>assert.equal(f({grade:'todos'}).length,126));
test('Filtro ORG/RES restringe vínculos',()=>assert(0<f({level:'ORG',stage:'RES'}).length && f({level:'ORG',stage:'RES'}).length<58));
test('Concepto CO con cero enlaces no se rellena',()=>{
 const ids=new Set(data.vinculos_co.map(l=>l.concepto_id));const empty=data.conceptos.find(c=>!ids.has(c.id));assert(empty);assert.equal(f({concept:empty.id,grade:'todos'}).length,0);
});
test('Búsqueda inexistente CO devuelve cero',()=>assert.equal(f({query:'xyz___ninguno___xyz'}).length,0));
test('Búsqueda sin acentos y casefold estable',()=>assert(engine.norm('ORGANIZACIÓN').includes('organizacion')));
test('249 propuestas en catálogo general por ID único',()=>assert.equal(new Set(core.filterAtlas({}).map(r=>r.prop)).size,249));
test('Filtro general y tema restringen rutas',()=>{
 const t=data.investigaciones[0].tema_general;const r=core.filterAtlas({tema:t});assert(r.length>0 && r.length<1157);
});
test('Recorrido completo no genera combinaciones',()=>{
 const r=core.allRoutes[0],f={tema:r.p.tema_general,subtema:r.p.tema_id,problema:r.p.problema_id,pregunta:r.q.id,alcance:r.alcance,sector:r.sector_id,territorio:r.territorio};
 const matches=core.filterAtlas(f);assert(matches.length>=1 && matches.every(z=>z.prop===r.prop && z.pregunta===r.pregunta && z.sector_id===r.sector_id));
 const impossible=core.filterAtlas({...f,sector:'ID-SECTOR-INEXISTENTE'});assert.equal(impossible.length,0);
});
test('Cascada de pregunta+sector solo propone opciones existentes',()=>{
 const r=core.allRoutes[0], opts=core.cascadeOptions({tema:r.p.tema_general,subtema:r.p.tema_id,problema:r.p.problema_id,pregunta:r.q.id,alcance:r.alcance});
 assert(opts.sector.includes(r.sector_id));
});
test('Filter search general inexistente',()=>assert.equal(core.filterAtlas({query:'xyz___ninguno___xyz'}).length,0));
test('Todos los vínculos CO tienen concepto y cita',()=>{
 const ids=new Set(data.conceptos.map(c=>c.id));assert(data.vinculos_co.every(l=>ids.has(l.concepto_id)&&l.cita&&l.justificacion));
});
test('Sector y alcance CO requieren ruta real',()=>{
 const original=f();assert(original.length===58);const xx=f({sector:'sector-imposible'});assert.equal(xx.length,0);
});
test('0 causalidades concluidas',()=>assert.equal(data.preguntas.filter(q=>q.alcance==='CAU'&&q.estado_causal!=='candidata_no_validada').length,0));
console.log('RESULTADO',passed,'pruebas lógicas exitosas');
