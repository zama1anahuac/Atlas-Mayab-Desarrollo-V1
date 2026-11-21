/* Atlas Mayab: motor funcional puro, compartido con frontend y QA Node.js. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object' && module.exports) module.exports=api;
  if(root) root.ATLAS_ENGINE=api;
})(typeof window==='undefined'?null:window, function(){
  'use strict';
  const norm=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es');
  function create(d){
    const props=new Map(d.investigaciones.map(p=>[p.original,p]));
    const questions=new Map(d.preguntas.map(q=>[q.id,q]));
    const concepts=new Map(d.conceptos.map(c=>[c.id,c]));
    const byProp=new Map(),byQuestion=new Map();
    const routes=d.rutas.map(r=>({...r,p:props.get(r.prop),q:questions.get(r.pregunta)}));
    for(const r of routes){
      if(!byProp.has(r.prop))byProp.set(r.prop,[]);byProp.get(r.prop).push(r);
      if(!byQuestion.has(r.pregunta))byQuestion.set(r.pregunta,[]);byQuestion.get(r.pregunta).push(r);
    }
    function linkRoutes(l){return l.tipo==='PREGUNTA'?(byQuestion.get(l.pregunta)||[]):(byProp.get(l.prop)||[])}
    function filterCo(f){
      return d.vinculos_co.filter(l=>{
        if((f.level&&l.nivel!==f.level)||(f.stage&&l.etapa!==f.stage)||(f.concept&&l.concepto_id!==f.concept))return false;
        if(f.grade==='sustentadas'&&l.grado==='parcial')return false;
        if(f.grade&&f.grade!=='sustentadas'&&f.grade!=='todos'&&l.grado!==f.grade)return false;
        const rs=linkRoutes(l);
        if((f.scope||f.sector)&&!rs.some(r=>(!f.scope||r.alcance===f.scope)&&(!f.sector||r.sector_id===f.sector)))return false;
        if(f.query){
          const p=props.get(l.prop),q=questions.get(l.pregunta),c=concepts.get(l.concepto_id);
          const haystack=[l.id,l.justificacion,l.cita,l.grado,p?.id,p?.original,p?.titulo,p?.problema,q?.texto,c?.nombre,...rs.map(r=>r.sector)].join(' ');
          if(!norm(haystack).includes(norm(f.query)))return false;
        }
        return true;
      });
    }
    function routeValue(r,key){
      if(key==='tema')return r.p.tema_general;
      if(key==='subtema')return r.p.tema_id;
      if(key==='problema')return r.p.problema_id;
      if(key==='pregunta')return r.q.id;
      if(key==='alcance')return r.alcance;
      if(key==='sector')return r.sector_id;
      if(key==='territorio')return r.territorio;
      return '';
    }
    function filterAtlas(f){
      const keys=['tema','subtema','problema','pregunta','alcance','sector','territorio'];
      const search=norm(f.query);
      return routes.filter(r=>{
        if(keys.some(key=>f[key]&&routeValue(r,key)!==f[key]))return false;
        if(f.estado&&r.p.estado_co!==f.estado)return false;
        if(search){
          const haystack=[r.p.id,r.p.original,r.p.titulo,r.p.tema_general,r.p.tema_especifico,r.p.problema,r.q.texto,r.q.id,r.sector,r.territorio].join(' ');
          if(!norm(haystack).includes(search))return false;
        }
        return true;
      });
    }
    function cascadeOptions(f){
      let candidates=routes;
      const result={};
      for(const key of ['tema','subtema','problema','pregunta','alcance','sector','territorio']){
        result[key]=[...new Set(candidates.map(r=>routeValue(r,key)).filter(Boolean))];
        if(f[key])candidates=candidates.filter(r=>routeValue(r,key)===f[key]);
      }
      return result;
    }
    return {filterCo,filterAtlas,cascadeOptions,linkRoutes,routeValue,allRoutes:routes};
  }
  return Object.freeze({create,norm});
});
