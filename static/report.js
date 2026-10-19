/* Renderizador do relatório mensal. Usado pelo app e pelo arquivo exportado (mesmo código). */
(function(){
const NS="http://www.w3.org/2000/svg";
const CSS=`
.rp{color:var(--text,#16202e);font:15px/1.5 "Segoe UI",system-ui,sans-serif}
.rp h1{margin:0;font:300 30px "Segoe UI Light","Segoe UI",sans-serif}
.rp h2{margin:26px 0 8px;font:600 13px var(--mono,Consolas,monospace);letter-spacing:.14em;text-transform:uppercase;color:var(--accent,#0b63e5)}
.rp .sub{color:var(--dim,#58687e);font-size:14px;margin:2px 0 14px}
.rp .badge{display:inline-block;border:1px solid var(--accent,#0b63e5);color:var(--accent,#0b63e5);padding:1px 10px;font-size:12px;margin-left:8px}
.rp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(170px,100%),1fr));gap:12px}
.rp-kpi,.rp-card{background:var(--panel,#fff);border:1px solid var(--line,#d3dbe8);padding:14px}
.rp-kpi span{display:block;color:var(--dim,#58687e);font-size:13px}
.rp-kpi b{display:block;font:300 32px var(--mono,Consolas,monospace);color:var(--accent,#0b63e5);line-height:1.2}
.rp-kpi small{color:var(--dim,#58687e)}
.rp-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:14px}
.rp ul{margin:6px 0 0;padding-left:20px}.rp li{margin:3px 0}
.rp table{width:100%;border-collapse:collapse;font-size:14px}
.rp th,.rp td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line,#d3dbe8)}
.rp th{color:var(--dim,#58687e);font-weight:600}
.rp-chips{display:flex;flex-wrap:wrap;gap:8px}
.rp-chips span{border:1px solid var(--line,#d3dbe8);padding:2px 10px;background:var(--panel2,#f2f5fa)}
.rp-chips em{font-style:normal;color:var(--dim,#58687e);margin-left:6px}
.rp svg{width:100%;height:auto;display:block;color:var(--dim,#58687e)}
.rp .bar{fill:var(--accent,#0b63e5)}
.rp .note{color:var(--dim,#58687e);font-size:13px;margin-top:22px}
.rp-row{display:flex;align-items:center;gap:10px;margin:4px 0;font-size:14px}
.rp-row i{display:block;height:10px;background:var(--accent,#0b63e5);min-width:2px}
.rp-ai{white-space:pre-wrap}
`;
function el(t,txt,cls){const e=document.createElement(t);if(txt!=null)e.textContent=txt;if(cls)e.className=cls;return e}
function sec(root,title){root.append(el("h2",title))}
function bars(vals,labels,every){
  const W=600,H=130,n=vals.length,max=Math.max(1,...vals),bw=W/n;
  const s=document.createElementNS(NS,"svg");s.setAttribute("viewBox",`0 0 ${W} ${H+20}`);s.setAttribute("role","img");
  vals.forEach((v,i)=>{
    const h=v/max*H,r=document.createElementNS(NS,"rect");
    r.setAttribute("class","bar");r.setAttribute("x",i*bw+1);r.setAttribute("y",H-h);r.setAttribute("width",Math.max(1,bw-2));r.setAttribute("height",h);
    const t=document.createElementNS(NS,"title");t.textContent=`${labels[i]}: ${v}`;r.append(t);s.append(r);
    if(i%every===0){const x=document.createElementNS(NS,"text");x.setAttribute("x",i*bw+bw/2);x.setAttribute("y",H+14);x.setAttribute("font-size","11");x.setAttribute("text-anchor","middle");x.setAttribute("fill","currentColor");x.textContent=labels[i];s.append(x)}
  });
  return s;
}
function hbars(box,pairs){
  const max=Math.max(1,...pairs.map(p=>p[1]));
  pairs.forEach(([k,v])=>{const r=el("div",null,"rp-row");const i=el("i");i.style.width=Math.round(v/max*220)+"px";r.append(el("span",k),i,el("span",String(v)));box.append(r)});
}
const dur=s=>s<60?`${s} s`:s<3600?`${Math.round(s/60)} min`:`${Math.floor(s/3600)} h ${Math.round(s%3600/60)} min`;
const kpi=(l,b,s)=>{const k=el("div",null,"rp-kpi");k.append(el("span",l),el("b",String(b)),el("small",s||""));return k};
function dlt(c,p,unit=""){if(!p)return "sem dados do mês anterior";const d=c-p;return `${d>=0?"▲":"▼"} ${Math.abs(d)}${unit} vs mês anterior`}
function list(items,empty){const ul=el("ul");if(!items.length)ul.append(el("li",empty));items.forEach(t=>ul.append(el("li",t)));return ul}

window.renderReport=function(box,d){
  if(!document.getElementById("rp-style")){const s=el("style",CSS);s.id="rp-style";document.head.append(s)}
  const root=el("div",null,"rp");box.append(root);
  const h=el("h1","Relatório de "+d.label);if(d.partial)h.append(el("span","mês em andamento","badge"));root.append(h);
  root.append(el("div","Gerado em "+new Date(d.generated*1000).toLocaleString("pt-BR"),"sub"));
  const S=d.summary,P=d.previous,T=d.tasks,B=d.briefings,U=d.usage;

  const g=el("div",null,"rp-grid");
  g.append(kpi("Mensagens enviadas",S.messages,dlt(S.messages,P.messages)),
           kpi("Conversas",S.conversations,`${S.bot_messages} respostas da HERO`),
           kpi("Dias ativos",`${S.active_days}/${d.days}`,dlt(S.active_days,P.active_days)),
           kpi("Briefings",S.briefings,dlt(S.briefings,P.briefings)),
           kpi("Tarefas concluídas",T.completed,T.rate==null?"nenhuma criada no mês":`${T.rate}% das criadas no mês`),
           kpi("Controle por mãos",U.hands.seconds?dur(U.hands.seconds):"—",`${U.hands.sessions} sessão(ões)`));
  root.append(g);

  sec(root,"Destaques");root.append(list(d.highlights,"Ainda não há dados suficientes neste mês."));

  sec(root,"Atividade por dia");
  const c1=el("div",null,"rp-card");c1.append(bars(d.daily,d.daily.map((_,i)=>String(i+1)),d.days>20?3:1));root.append(c1);
  const two=el("div",null,"rp-two");
  const a=el("div",null,"rp-card");a.append(el("b","Por dia da semana"),bars(d.weekday,d.weekday_names.map(x=>x.slice(0,3)),1));
  const b=el("div",null,"rp-card");b.append(el("b","Por horário"),bars(d.hours,d.hours.map((_,i)=>i+"h"),3));
  two.append(a,b);root.append(two);

  sec(root,"Conversas");
  const cv=el("div",null,"rp-card");
  cv.append(el("p",`Você enviou ${S.messages} mensagens (média de ${S.avg_words_user} palavras) e a HERO respondeu com ${S.bot_messages} (média de ${S.avg_words_bot} palavras).`));
  if(d.top_convs.length){const t=el("table"),hd=el("tr");hd.append(el("th","Conversa mais longa"),el("th","Mensagens"));t.append(hd);
    d.top_convs.forEach(c=>{const r=el("tr");r.append(el("td",c.title),el("td",String(c.count)));t.append(r)});cv.append(t)}
  root.append(cv);
  sec(root,"Assuntos mais frequentes");
  const tp=el("div",null,"rp-chips");d.topics.forEach(([w,n])=>{const s=el("span",w);s.append(el("em",String(n)));tp.append(s)});
  if(!d.topics.length)tp.append(el("span","Sem dados suficientes"));root.append(tp);

  sec(root,"Tarefas");
  const tk=el("div",null,"rp-two");
  const t1=el("div",null,"rp-card");t1.append(el("b",`Concluídas (${T.completed})`),list(T.completed_list,"Nenhuma tarefa concluída."));
  const t2=el("div",null,"rp-card");t2.append(el("b",`Pendentes no fim do período (${T.pending})`),list(T.pending_list,"Nada pendente."));
  tk.append(t1,t2);root.append(tk);
  root.append(el("p",`Criadas no mês: ${T.created}.`+(T.avg_hours!=null?` Tempo médio para concluir: ${T.avg_hours} h.`:""),"sub"));

  sec(root,"Briefings, clima e notícias");
  const bf=el("div",null,"rp-card");
  bf.append(el("p",`${B.count} briefing(s) em ${B.days} dia(s).`+(B.tmax_avg!=null?` Temperatura média: mínima ${B.tmin_avg}°C e máxima ${B.tmax_avg}°C; ${B.rainy_days} dia(s) com chuva provável (50% ou mais).`:"")));
  const em=B.emails;if(em.att+em.info+em.noise)bf.append(el("p",`E-mails vistos nos briefings: ${em.att} pediam atenção, ${em.info} informativos e ${em.noise} ruído.`));
  if(B.agenda_events)bf.append(el("p",`Compromissos de agenda incluídos nos briefings: ${B.agenda_events}.`));
  const nw=Object.entries(B.news);if(nw.length){bf.append(el("b","Manchetes recebidas por categoria"));hbars(bf,nw)}
  if(B.weather.length){const dt=el("details"),sm=el("summary","Clima dia a dia");dt.append(sm);
    const t=el("table"),hd=el("tr");["Dia","Mín.","Máx.","Chuva"].forEach(x=>hd.append(el("th",x)));t.append(hd);
    B.weather.forEach(w=>{const r=el("tr");r.append(el("td",w.day.slice(8)+"/"+w.day.slice(5,7)),el("td",w.tmin+"°"),el("td",w.tmax+"°"),el("td",w.rain+"%"));t.append(r)});dt.append(t);bf.append(dt)}
  root.append(bf);

  sec(root,"Uso de voz e gestos");
  const us=el("div",null,"rp-card"),H=U.hands;
  us.append(el("p",`Entradas por voz: ${U.voice}.`+(U.commands.length?"":" Nenhum comando de voz usado.")));
  if(U.commands.length){us.append(el("b","Comandos mais usados"));hbars(us,U.commands)}
  us.append(el("p",H.sessions?`Controle por mãos: ${H.sessions} sessão(ões), ${dur(H.seconds)} no total, ${H.clicks} cliques, ${H.swipes} trocas de página, ${H.zooms} zooms, ${H.drags} arrastes e ${H.scrolls} rolagens.`:"Controle por mãos não usado neste mês."));
  root.append(us);

  sec(root,"Análise da HERO (IA)");
  const ai=el("div",null,"rp-card");
  if(d.analysis){ai.append(el("div",d.analysis,"rp-ai"),el("p","Gerada a partir dos números deste relatório, sem o conteúdo das suas conversas.","sub"))}
  else ai.append(el("p","Ainda não gerada. Use o botão “Gerar análise com IA” na página do relatório.","sub"));
  root.append(ai);

  root.append(el("p","Observações: mensagens e conversas criadas antes da versão com data e login têm data aproximada (a da última atualização da conversa). Apagar uma conversa remove suas mensagens das contagens de meses ainda abertos; meses fechados ficam congelados na primeira geração, até você atualizar o relatório.","note"));
};
})();
