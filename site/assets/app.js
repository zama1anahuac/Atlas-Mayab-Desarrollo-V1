/* Atlas Mayab V1.0 | Diseño y lógica originales | No autorizado para publicar. */
'use strict';
(() => {
  const D = window.ATLAS_DATA;
  const $ = (sel) => document.querySelector(sel);
  const esc = (val) => String(val == null ? '' : val).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const plain = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es');
  const format = n => Number(n).toLocaleString('es-MX');
  const LEVEL = {IND:'Individual',GRU:'Grupal',ORG:'Organizacional'};
  const STAGE = {INS:'Insumos',PRO:'Procesos',RES:'Resultados'};
  const STATUS = {directo:'Directo',razonado:'Razonado',parcial:'Parcial',pendiente:'Pendiente',fuera_del_modelo:'Fuera del modelo'};
  const state = {co:{level:'',stage:'',concept:'',grade:'sustentadas',query:'',scope:'',sector:'',page:1},atlas:{tema:'',subtema:'',problema:'',pregunta:'',alcance:'',sector:'',territorio:'',estado:'',query:'',page:1},legacy:{query:'',page:1}};
  const PER_CO=9, PER_ATLAS=9, PER_LEGACY=14;
  const n = (x) => String(x || '');
  const badge = (v) => `<span class="status-tag status-${esc(v||'pendiente')}">${esc(STATUS[v] || v || 'Pendiente')}</span>`;
  const textOr = (v) => v ? esc(v) : '<span class="muted">No especificado</span>';
  const sourcesInline = a => a && a.trim() ? esc(a) : 'Localizador por verificar';
  const linkMethod = l => (l.procedimiento || '').includes('curaduria') ? 'Curaduría documental específica' : (l.procedimiento || '').includes('cotejo_especifico_pregunta') ? 'Cotejo documental pregunta–indicador' : 'Cribado semiautomatizado por registro';
  const safeUrl = (str) => {try {const u=new URL(str);return ['https:','http:'].includes(u.protocol) ? u.href : '';} catch{return ''}};
  if (!D || !Array.isArray(D.investigaciones) || !window.ATLAS_ENGINE) {
    const message='No fue posible cargar la base documental. Comprueba los archivos de /site/data y /site/assets.';
    const target=$('#coResultCount'); if(target) target.textContent=message;
    const general=$('#atlasResultCount'); if(general) general.textContent=message;
    return;
  }
  const engine = window.ATLAS_ENGINE.create(D);
  const byProp=new Map(D.investigaciones.map(p=>[p.original,p]));
  const byInv=new Map(D.investigaciones.map(p=>[p.id,p]));
  const byQuestion=new Map(D.preguntas.map(q=>[q.id,q]));
  const byConcept=new Map(D.conceptos.map(c=>[c.id,c]));
  const questionsByProp=new Map(), routesByProp=new Map(), routesByQuestion=new Map(), coByProp=new Map();
  for (const q of D.preguntas) {if(!questionsByProp.has(q.prop))questionsByProp.set(q.prop,[]);questionsByProp.get(q.prop).push(q)}
  const routes=D.rutas.map(r=>({ ...r, p:byProp.get(r.prop), q:byQuestion.get(r.pregunta)}));
  for (const r of routes) {
    if(!routesByProp.has(r.prop))routesByProp.set(r.prop,[]);routesByProp.get(r.prop).push(r);
    if(!routesByQuestion.has(r.pregunta))routesByQuestion.set(r.pregunta,[]);routesByQuestion.get(r.pregunta).push(r);
  }
  for (const rel of D.vinculos_co){if(!coByProp.has(rel.prop))coByProp.set(rel.prop,[]);coByProp.get(rel.prop).push(rel)}
  function getLinkRoutes(rel) {return rel.tipo==='PREGUNTA' ? (routesByQuestion.get(rel.pregunta)||[]) : (routesByProp.get(rel.prop)||[])}
  function distinct(array,fn){return [...new Set(array.map(fn).filter(Boolean))]}
  function sortStrings(a,b){return a.localeCompare(b,'es',{sensitivity:'base'})}
  function htmlEmpty(title,sub){return `<div class="empty-state"><span aria-hidden="true" class="empty-glyph">◇</span><h4>${esc(title)}</h4><p>${esc(sub)}</p></div>`}
  function option(el, value,label) {const op=document.createElement('option');op.value=value;op.textContent=label;op.title=label;el.appendChild(op)}
  function resetOptions(sel,values,label,selected,formatter=(x)=>x){
    const old=sel.value;
    sel.replaceChildren();option(sel,'',label);
    values.forEach(v=>option(sel,v,formatter(v)));
    sel.value=values.includes(selected) ? selected : '';
    return old !== sel.value;
  }
  function pagination(el,current,total,cb){
    const pages=Math.ceil(total / (el.id==='legacyPager'?PER_LEGACY:el.id==='coPager'?PER_CO:PER_ATLAS));
    el.replaceChildren();if(pages<=1)return;
    const b=(label,target,disabled,active=false)=>{const node=document.createElement('button');node.type='button';node.textContent=label;node.disabled=disabled;node.className='page-button'+(active?' active':'');node.setAttribute('aria-label',label==='‹'?'Página anterior':label==='›'?'Página siguiente':'Página '+label);if(active)node.setAttribute('aria-current','page');node.addEventListener('click',()=>cb(target));el.appendChild(node)};
    b('‹',current-1,current<=1);
    const start=Math.max(1,Math.min(current-2,pages-4));const end=Math.min(pages,start+4);
    if(start>1)b('1',1,false);
    if(start>2){const s=document.createElement('span');s.textContent='…';el.appendChild(s)}
    for(let i=start;i<=end;i++) b(String(i),i,false,i===current);
    if(end<pages-1){const s=document.createElement('span');s.textContent='…';el.appendChild(s)}
    if(end<pages)b(String(pages),pages,false);
    b('›',current+1,current>=pages);
  }
  function bindOpen(el){el.addEventListener('click',(ev)=>{const btn=ev.target.closest('[data-open]');if(btn)openFicha(btn.dataset.open)})}
  document.querySelectorAll('#heroInv,#heroQuestions,#heroLinks,#heroConcepts').forEach((el,i)=>{
    const vals=[D.investigaciones.length,D.preguntas.length,D.vinculos_co.length,D.conceptos.length];el.textContent=format(vals[i]);
  });
  // === Explorador CO ===
  const cellTypes=['IND','GRU','ORG'];const stageTypes=['INS','PRO','RES'];
  const matrix=$('#modelGrid');
  function renderMatrix(){
    matrix.innerHTML='';
    for(const lev of cellTypes){
      const row=document.createElement('div');row.className='model-row';
      row.innerHTML=`<div class="row-label" aria-hidden="true">${LEVEL[lev]}</div>`;
      for (const stage of stageTypes){
        const cs=D.conceptos.filter(c=>c.nivel===lev&&c.etapa===stage);
        const links=D.vinculos_co.filter(c=>c.nivel===lev&&c.etapa===stage);
        const chosen=state.co.level===lev&&state.co.stage===stage;
        const btn=document.createElement('button');btn.type='button';btn.className=`matrix-cell ${stage.toLowerCase()}${chosen?' selected':''}`;
        btn.setAttribute('aria-pressed',chosen?'true':'false');btn.setAttribute('aria-label',`${LEVEL[lev]}, ${STAGE[stage]}, ${cs.length} conceptos, ${links.length} relaciones; seleccionar celda`);
        btn.innerHTML=`<strong>${cs.length.toString().padStart(2,'0')}</strong><span>conceptos</span><small>${links.length} vínculos</small>`;
        btn.addEventListener('click',()=>{
          const toggle=chosen;state.co.level=toggle?'':lev;state.co.stage=toggle?'':stage;state.co.concept='';state.co.page=1;
          $('#coLevel').value=state.co.level;$('#coStage').value=state.co.stage;renderCo();
        });row.appendChild(btn)
      }
      matrix.appendChild(row)
    }
  }
  function renderConcepts(){
    const list=D.conceptos.filter(c=>(!state.co.level||c.nivel===state.co.level)&&(!state.co.stage||c.etapa===state.co.stage));
    $('#conceptCount').textContent=`${list.length} de 30 conceptos · selección ${state.co.level?LEVEL[state.co.level]:'todos los niveles'} / ${state.co.stage?STAGE[state.co.stage]:'todas las etapas'}`;
    $('#conceptCards').innerHTML=list.map(c=>{
      const links=D.vinculos_co.filter(l=>l.concepto_id===c.id);
      const usable=links.filter(l=>l.grado!=='parcial').length;
      const active=c.id===state.co.concept;
      return `<button type="button" class="concept-card ${active?'active':''}" data-concept="${esc(c.id)}" aria-pressed="${active}"><span class="concept-code">${esc(c.id)} <span>${esc(LEVEL[c.nivel])} · ${esc(STAGE[c.etapa])}</span></span><strong>${esc(c.nombre)}</strong><span class="concept-description">${esc(c.definicion)}</span><span class="concept-bottom">${usable} directos/razonados <span>·</span> ${links.length} vínculos totales</span></button>`
    }).join('') || htmlEmpty('Sin conceptos en la celda','Prueba con otro nivel o etapa. No se crean conceptos para llenar espacios.');
    $('#conceptCards').querySelectorAll('[data-concept]').forEach(btn=>btn.addEventListener('click',()=>{
      state.co.concept=state.co.concept===btn.dataset.concept?'':btn.dataset.concept;state.co.page=1;renderCo();
    }));
  }
  function coFilterLinks(){return engine.filterCo(state.co)}
  function renderCo(){
    renderMatrix();renderConcepts();
    const arr=coFilterLinks(),count=arr.length;
    const proposals=new Set(arr.map(x=>x.prop));const questions=new Set(arr.filter(x=>x.pregunta).map(x=>x.pregunta));
    $('#coResultCount').textContent=`${format(count)} correspondencia${count!==1?'s':''} documentales`;
    $('#coResultSub').textContent=`${proposals.size} propuestas distintas · ${questions.size} preguntas con vínculo explícito`;
    const active=[state.co.level&&LEVEL[state.co.level],state.co.stage&&STAGE[state.co.stage],state.co.concept&&byConcept.get(state.co.concept)?.nombre,state.co.grade==='sustentadas'?'Solo directos y razonados':state.co.grade==='todos'?'Incluye parciales':STATUS[state.co.grade],state.co.scope&&'Alcance '+state.co.scope,state.co.sector&&D.sectores.find(s=>s.id===state.co.sector)?.nombre].filter(Boolean);
    $('#activeCoFilters').textContent=active.join('  /  ');
    const pages=Math.max(1,Math.ceil(count/PER_CO));state.co.page=Math.min(state.co.page,pages);
    const page=arr.slice((state.co.page-1)*PER_CO,state.co.page*PER_CO);
    $('#coResults').innerHTML=page.map(l=>{
      const p=byProp.get(l.prop);const q=byQuestion.get(l.pregunta);const c=byConcept.get(l.concepto_id);
      const routeCount=getLinkRoutes(l).length;
      return `<article class="result-card ${l.grado==='parcial'?'partial-card':''}"><div class="card-head"><span class="mono">${esc(l.id)}</span>${badge(l.grado)}</div><div class="card-subtitle">${esc(LEVEL[l.nivel])} <span>·</span> ${esc(STAGE[l.etapa])} <span>·</span> ${esc(l.tipo==='PREGUNTA'?'Vínculo a pregunta':'Vínculo a propuesta')}</div><h4>${esc(c.nombre)}</h4><p class="result-title">${esc(p.titulo)}</p>${q?`<p class="co-question"><span>Pregunta vinculada:</span> ${esc(q.texto)}</p>`:''}<div class="card-cite"><strong>Fuente:</strong> ${esc(l.cita)}${l.diapositiva?' · Diap. '+esc(l.diapositiva):''}<br><strong>Procedimiento:</strong> ${esc(linkMethod(l))}. Pendiente de revisión docente.</div><div class="card-footer"><span>${routeCount} ruta${routeCount!==1?'s':''} sectorial${routeCount!==1?'es':''} disponible${routeCount!==1?'s':''}</span><button type="button" data-open="${esc(p.id)}" class="card-action">Ver ficha <span aria-hidden="true">↗</span></button></div></article>`
    }).join('') || htmlEmpty('No hay correspondencias para esta combinación','Las categorías sin vínculos permanecen vacías. Puedes incluir relaciones parciales o modificar los filtros.');
    pagination($('#coPager'),state.co.page,count,(p)=>{state.co.page=p;renderCo();$('#coResultCount').scrollIntoView({block:'nearest',behavior:'smooth'})});
  }
  $('#coSearch').addEventListener('input',e=>{state.co.query=e.target.value;state.co.page=1;renderCo()});
  $('#coLevel').addEventListener('change',e=>{state.co.level=e.target.value;state.co.concept='';state.co.page=1;renderCo()});
  $('#coStage').addEventListener('change',e=>{state.co.stage=e.target.value;state.co.concept='';state.co.page=1;renderCo()});
  $('#coGrade').addEventListener('change',e=>{state.co.grade=e.target.value;state.co.page=1;renderCo()});
  $('#coAlcance').addEventListener('change',e=>{state.co.scope=e.target.value;state.co.page=1;renderCo()});
  $('#coSector').addEventListener('change',e=>{state.co.sector=e.target.value;state.co.page=1;renderCo()});
  for(const sec of D.sectores)option($('#coSector'),sec.id,sec.nombre);
  $('#clearMatrix').addEventListener('click',()=>{state.co.level='';state.co.stage='';state.co.concept='';$('#coLevel').value='';$('#coStage').value='';renderCo()});
  $('#clearCo').addEventListener('click',()=>{Object.assign(state.co,{level:'',stage:'',concept:'',grade:'sustentadas',query:'',scope:'',sector:'',page:1});$('#coSearch').value='';$('#coLevel').value='';$('#coStage').value='';$('#coGrade').value='sustentadas';$('#coAlcance').value='';$('#coSector').value='';renderCo()});
  bindOpen($('#coResults'));
  // === Explorador general, opciones derivadas secuencialmente de rutas existentes ===
  const ATLAS_KEYS=['tema','subtema','problema','pregunta','alcance','sector','territorio'];
  const ATLAS_SELECT={tema:'#atlasTema',subtema:'#atlasSubtema',problema:'#atlasProblema',pregunta:'#atlasPregunta',alcance:'#atlasAlcance',sector:'#atlasSector',territorio:'#atlasTerritorio'};
  function routeValue(route,key){
    if(key==='tema')return route.p.tema_general;
    if(key==='subtema')return route.p.tema_id;
    if(key==='problema')return route.p.problema_id;
    if(key==='pregunta')return route.q.id;
    if(key==='alcance')return route.alcance;
    if(key==='sector')return route.sector_id;
    if(key==='territorio')return route.territorio;
    return '';
  }
  function optionLabel(key,value){
    if(key==='subtema')return (D.temas.find(x=>x.id===value)?.nombre||value)+' · '+value;
    if(key==='problema')return (D.problemas.find(x=>x.id===value)?.texto||value).slice(0,120);
    if(key==='pregunta')return value+' · '+(byQuestion.get(value)?.texto||'').slice(0,100);
    if(key==='sector')return D.sectores.find(x=>x.id===value)?.nombre||value;
    if(key==='alcance')return value==='DES'?'Descriptivo':'Causal candidata';
    return value;
  }
  const labels={tema:'Todos los temas',subtema:'Todos los temas específicos',problema:'Todos los problemas',pregunta:'Todas las preguntas',alcance:'DES y CAU',sector:'Todos los sectores',territorio:'Todos los territorios'};
  function cascade(){
    let candidate=routes;
    for(const key of ATLAS_KEYS){
      const possible=distinct(candidate,r=>routeValue(r,key)).sort(key==='alcance'?undefined:sortStrings);
      const el=$(ATLAS_SELECT[key]);
      const selected=state.atlas[key];
      resetOptions(el,possible,labels[key],selected,v=>optionLabel(key,v));
      state.atlas[key]=el.value;
      if(state.atlas[key]) candidate=candidate.filter(r=>routeValue(r,key)===state.atlas[key]);
    }
  }
  function atlasMatches(){return engine.filterAtlas(state.atlas)}
  function renderAtlas(){
    cascade();const all=atlasMatches();
    const matchMap=new Map();
    for(const r of all){if(!matchMap.has(r.prop))matchMap.set(r.prop,[]);matchMap.get(r.prop).push(r)}
    const ids=[...matchMap.keys()].sort((a,b)=>byProp.get(a).id.localeCompare(byProp.get(b).id));
    $('#atlasResultCount').textContent=`${format(ids.length)} propuesta${ids.length!==1?'s':''}`;
    $('#atlasResultSub').textContent=`${format(all.length)} rutas reales · ${new Set(all.map(x=>x.pregunta)).size} preguntas en el filtro`;
    const trail=ATLAS_KEYS.filter(k=>state.atlas[k]).map(k=>optionLabel(k,state.atlas[k]));
    $('#atlasTrail').innerHTML=trail.length?'<span>RUTA SELECCIONADA</span> '+trail.map(t=>`<b>${esc(t)}</b>`).join('<i aria-hidden="true">→</i>'):'<span>RUTA ABIERTA</span> Elige filtros de forma progresiva o explora el catálogo completo.';
    const pages=Math.max(1,Math.ceil(ids.length/PER_ATLAS));state.atlas.page=Math.min(state.atlas.page,pages);
    $('#atlasResults').innerHTML=ids.slice((state.atlas.page-1)*PER_ATLAS,state.atlas.page*PER_ATLAS).map(id=>{
      const p=byProp.get(id),m=matchMap.get(id),qNames=distinct(m,r=>r.q.texto),sectors=distinct(m,r=>r.sector);
      return `<article class="atlas-item"><div class="atlas-item-top"><span class="mono">${esc(p.id)} · ${esc(p.original)}</span>${badge(p.estado_co)}</div><h3>${esc(p.titulo)}</h3><p class="atlas-item-meta">${esc(p.tema_general)} <span>·</span> ${esc(p.tema_especifico)}</p><p class="atlas-problem"><strong>Problema:</strong> ${esc(p.problema)}</p><p class="atlas-question"><strong>Pregunta en recorrido:</strong> ${esc(qNames[0]||'Sin pregunta')}${qNames.length>1?' <span class="muted">+'+(qNames.length-1)+' preguntas</span>':''}</p><div class="atlas-item-bottom"><span>${m.length} ruta${m.length!==1?'s':''} · ${sectors.length} sector${sectors.length!==1?'es':''} · ${esc(p.territorio||'Territorio por precisar')}</span><button type="button" class="card-action" data-open="${esc(p.id)}">Abrir ficha <span aria-hidden="true">↗</span></button></div></article>`;
    }).join('')||htmlEmpty('Ninguna propuesta coincide','Los filtros se cruzan solo con rutas existentes. Elige otras categorías o limpia la selección.');
    pagination($('#atlasPager'),state.atlas.page,ids.length,(p)=>{state.atlas.page=p;renderAtlas();$('#atlasResultCount').scrollIntoView({block:'nearest',behavior:'smooth'})});
  }
  ATLAS_KEYS.forEach((key,i)=>$(ATLAS_SELECT[key]).addEventListener('change',(ev)=>{
    state.atlas[key]=ev.target.value;
    for(const later of ATLAS_KEYS.slice(i+1)){state.atlas[later]='';}
    state.atlas.page=1;renderAtlas();
  }));
  $('#atlasEstado').addEventListener('change',e=>{state.atlas.estado=e.target.value;state.atlas.page=1;renderAtlas()});
  $('#atlasSearch').addEventListener('input',e=>{state.atlas.query=e.target.value;state.atlas.page=1;renderAtlas()});
  $('#atlasClear').addEventListener('click',()=>{Object.assign(state.atlas,{tema:'',subtema:'',problema:'',pregunta:'',alcance:'',sector:'',territorio:'',estado:'',query:'',page:1});$('#atlasEstado').value='';$('#atlasSearch').value='';renderAtlas()});
  bindOpen($('#atlasResults'));
  // === Memoria histórica (no investigaciones principales) ===
  function renderLegacy(){
    const query=plain(state.legacy.query);const entries=query ? D.historico.filter(x=>plain([x.folio,x.tema,x.problema,x.sector,x.titulo].join(' ')).includes(query)) : D.historico;
    $('#legacyCount').textContent=`${format(entries.length)} combinaciones históricas de ${format(D.historico.length)} · Este catálogo no es un conjunto de estudios validados.`;
    const pages=Math.max(1,Math.ceil(entries.length/PER_LEGACY));state.legacy.page=Math.min(state.legacy.page,pages);
    $('#legacyResults').innerHTML=entries.slice((state.legacy.page-1)*PER_LEGACY,state.legacy.page*PER_LEGACY).map(x=>`<tr><td class="mono">${esc(x.folio)}</td><td><strong>${esc(x.tema)}</strong><br><span class="muted">${esc(x.problema)}</span></td><td>${esc(x.sector)}</td><td>${esc(x.titulo)}</td></tr>`).join('')||'<tr><td colspan="4">No se encontraron combinaciones históricas para esta búsqueda.</td></tr>';
    pagination($('#legacyPager'),state.legacy.page,entries.length,p=>{state.legacy.page=p;renderLegacy()});
  }
  $('#legacySearch').addEventListener('input',e=>{state.legacy.query=e.target.value;state.legacy.page=1;renderLegacy()});
  // === Cobertura y evidencia ===
  const STATUS_ORDER=['directo','razonado','parcial','pendiente','fuera_del_modelo'];
  function bars(el,stats,total){el.innerHTML=STATUS_ORDER.map(s=>{
    const num=stats[s]||0,pct=100*num/total;
    return `<div class="bar-row"><div class="bar-label"><span>${esc(STATUS[s])}</span><span><strong>${num}</strong> · ${pct.toFixed(1)} %</span></div><div class="bar-track" role="img" aria-label="${esc(STATUS[s])}: ${num} de ${total}"><div class="bar-fill bar-${s}" style="width:${pct}%"></div></div></div>`
  }).join('')}
  bars($('#propStatusBars'),D.meta.clasificacion_investigaciones,249);bars($('#questionStatusBars'),D.meta.clasificacion_preguntas,365);
  function renderSources(){
    $('#sourcesGrid').innerHTML=D.fuentes.map(source=>{
      const href=safeUrl(source.url);
      return `<article class="source-item"><div class="source-top"><span class="mono">${esc(source.id)}</span><span class="source-type">${esc(source.tipo.replace(/_/g,' '))}</span></div><p>${esc(source.apa)}</p><small>${esc(source.localizador)}</small>${href?`<a href="${esc(href)}" target="_blank" rel="noopener noreferrer">Consultar fuente externa ↗</a>`:'<span class="tiny muted">Fuente interna citada, sin enlace público</span>'}</article>`
    }).join('');
  }
  renderSources();
  // === Ficha documental original y trazable ===
  function openFicha(invId){
    const p=byInv.get(invId);if(!p)return;
    const qs=questionsByProp.get(p.original)||[];const rr=routesByProp.get(p.original)||[];
    const links=coByProp.get(p.original)||[];
    const old=D.vinculos_heredados.filter(x=>x.prop===p.original);
    $('#fichaTitle').textContent=p.titulo;
    const questionBlock=qs.map(q=>{
      const qLinks=links.filter(x=>x.pregunta===q.id);
      return `<div class="ficha-question"><div class="flex"><strong class="mono">${esc(q.id)}</strong><span class="scope-pill">${q.alcance==='CAU'?'CAU · Candidata causal':'DES · Descriptiva'}</span>${badge(q.estado_co)}</div><p>${esc(q.texto)}</p><p class="tiny muted">Unidad: ${textOr(q.unidad)} · Indicadores: ${textOr(q.indicadores)}</p>${q.alcance==='CAU'?`<div class="causal-grid"><div><strong>X original</strong><span>${textOr(q.x)}</span></div><div><strong>Y original</strong><span>${textOr(q.y)}</span></div><div><strong>Confusores planteados</strong><span>${textOr(q.confusores)}</span></div><div><strong>Diseño candidato</strong><span>${textOr(q.diseno)}</span></div></div><p class="tiny caution">No hay identificación causal validada. Hipótesis documental no comprobada: ${textOr(q.hipotesis_no_verificada)}.</p>`:''}<p class="tiny muted">Relaciones CO específicas de esta pregunta: ${qLinks.length}. Estado académico: revisión del profesor pendiente.</p></div>`;
    }).join('');
    const linkRows=links.map(l=>`<article class="ficha-link"><div class="flex"><strong>${esc(byConcept.get(l.concepto_id)?.nombre||l.concepto_id)}</strong>${badge(l.grado)}</div><p class="tiny">${esc(LEVEL[l.nivel])} · ${esc(STAGE[l.etapa])} · ${esc(l.tipo==='PREGUNTA'?'Pregunta '+l.pregunta:'Propuesta '+l.prop)} · ${esc(l.id)}</p><p>${esc(l.justificacion)}</p><div class="tiny muted"><strong>Cita:</strong> ${esc(l.cita)}${l.diapositiva?' · Diapositiva '+esc(l.diapositiva):''} · ${esc(l.fuentes_ids)}</div><p class="tiny caution">${esc(linkMethod(l))} · ${esc(l.revision)} · No acredita hipótesis causal.</p></article>`).join('')||'<p class="muted">Esta investigación no tiene un vínculo nuevo V1.1 fundamentado. Su permanencia en el Atlas general no requiere clasificación CO.</p>';
    const routeRows=rr.slice(0,20).map(r=>`<tr><td class="mono">${esc(r.id)}</td><td>${esc(r.q.id)} · ${esc(r.alcance)}</td><td>${esc(r.sector)}</td><td>${esc(r.territorio)}</td></tr>`).join('');
    const historical=old.map(l=>`<li><span class="mono">${esc(l.id)}</span> → ${esc(byConcept.get(l.concepto_id)?.nombre || l.concepto_id)} · ${esc(l.grado)} · ${esc(l.cita)}. <em>Heredado, sin ratificar.</em></li>`).join('');
    $('#fichaBody').innerHTML=`<div class="ficha-main-stats"><span class="mono">${esc(p.id)} / ${esc(p.original)}</span>${badge(p.estado_co)}<span class="review-status">Estado académico: ${esc(p.estado_academico)}</span></div><section class="ficha-section"><h3>Objeto y delimitación</h3><dl class="detail-grid"><div><dt>Tema general</dt><dd>${esc(p.tema_general)}</dd></div><div><dt>Tema específico</dt><dd>${esc(p.tema_especifico)}</dd></div><div><dt>Problema de investigación</dt><dd>${esc(p.problema)}</dd></div><div><dt>Sector principal original</dt><dd>${textOr(p.sector_principal)}</dd></div><div><dt>Territorio literal</dt><dd>${textOr(p.territorio)}</dd></div><div><dt>Unidad de análisis</dt><dd>${textOr(p.unidad)}</dd></div><div><dt>Indicadores de origen</dt><dd>${textOr(p.indicadores)}</dd></div><div><dt>Método propuesto</dt><dd>${textOr(p.metodo)}</dd></div></dl><p class="ficha-callout"><strong>Estado general CO:</strong> ${esc(STATUS[p.estado_co]||p.estado_co)}. ${esc(p.justificacion||'Sin justificación')}<br><strong>Pendiente:</strong> ${textOr(p.evidencia_requerida)}</p></section><section class="ficha-section"><h3>Preguntas originales · ${qs.length}</h3>${questionBlock}</section><section class="ficha-section"><h3>Correspondencias del modelo CO · ${links.length}</h3><p class="tiny muted">Los grados siguientes son particulares de cada vínculo, no sustituyen el estado general de la propuesta.</p>${linkRows}</section>${old.length?`<section class="ficha-section"><h3>Vínculos heredados · ${old.length}</h3><ul class="small">${historical}</ul></section>`:''}<section class="ficha-section"><h3>Rutas sectoriales explícitas · ${rr.length}</h3><div class="route-table-scroll"><table class="route-table"><thead><tr><th>ID de ruta</th><th>Pregunta y alcance</th><th>Sector</th><th>Territorio</th></tr></thead><tbody>${routeRows}</tbody></table></div>${rr.length>20?`<p class="tiny muted">Vista abreviada de 20 rutas; el Excel maestro conserva las ${rr.length}.</p>`:''}</section><section class="ficha-section trace-section"><h3>Procedencia y reservas</h3><p><strong>Fuente de datos:</strong> ${esc(p.archivo_origen)} · ${esc(p.hoja_origen)}, fila ${esc(p.fila_origen)} · ID normalizado ${esc(p.id)} · versión V1.1.</p><p><strong>Hash de fila de origen:</strong> <code>${esc(p.hash_fila)}</code></p><p><strong>Fuentes y notas originales:</strong> ${textOr(p.fuentes_ids)}</p><p>Documento generado por la interfaz a partir de datos proporcionados. No equivale a evaluación académica, información de campo ni aprobación para publicación.</p></section>`;
    const bridge=$('#goCoFromFicha');
    bridge.hidden=links.length===0;
    bridge.dataset.id=p.id;
    $('#goAtlasFromFicha').dataset.id=p.id;
    const dialog=$('#fichaDialog');dialog.showModal();$('#closeFicha').focus();
  }
  const dialog=$('#fichaDialog');
  $('#closeFicha').addEventListener('click',()=>dialog.close());
  $('#closeFichaBottom').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});
  $('#printFicha').addEventListener('click',()=>window.print());
  $('#goAtlasFromFicha').addEventListener('click',()=>{
    const p=byInv.get($('#goAtlasFromFicha').dataset.id);if(!p)return;
    Object.assign(state.atlas,{tema:'',subtema:'',problema:'',pregunta:'',alcance:'',sector:'',territorio:'',estado:'',query:p.original,page:1});
    $('#atlasSearch').value=p.original;$('#atlasEstado').value='';renderAtlas();
    dialog.close();document.getElementById('atlas-general').scrollIntoView({block:'start',behavior:'smooth'});
  });
  $('#goCoFromFicha').addEventListener('click',()=>{
    const p=byInv.get($('#goCoFromFicha').dataset.id);if(!p||!(coByProp.get(p.original)||[]).length)return;
    Object.assign(state.co,{level:'',stage:'',concept:'',grade:'todos',query:p.original,scope:'',sector:'',page:1});
    $('#coSearch').value=p.original;$('#coLevel').value='';$('#coStage').value='';$('#coGrade').value='todos';$('#coAlcance').value='';$('#coSector').value='';renderCo();
    dialog.close();document.getElementById('explorador-co').scrollIntoView({block:'start',behavior:'smooth'});
  });
  // === Menú adaptable ===
  const menu=$('#menuToggle');
  menu.addEventListener('click',()=>{const opening=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(opening));$('#navigation').classList.toggle('open',opening)});
  $('#navigation').querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{menu.setAttribute('aria-expanded','false');$('#navigation').classList.remove('open')}));
  // render inicial. La carga externa no es necesaria: se usa un archivo JS local con la exportación.
  renderCo();renderAtlas();renderLegacy();
  window.__ATLAS_QA__=Object.freeze({records:{investigaciones:D.investigaciones.length,preguntas:D.preguntas.length,rutas:D.rutas.length,conceptos:D.conceptos.length,vinculos:D.vinculos_co.length,historico:D.historico.length},visibleCo:()=>coFilterLinks().length,visibleAtlas:()=>new Set(atlasMatches().map(r=>r.prop)).size,activeCo:()=>({...state.co}),activeAtlas:()=>({...state.atlas})});
})();
