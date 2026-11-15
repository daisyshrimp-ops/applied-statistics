/* Frontend runtime mounted by an anywidget: works in marimo run and HTML/WASM. */
export default { render({el}) {
  el.classList.add('report-runtime-anchor');
  const abort = new AbortController();
  const on = (target,event,fn,options={}) => target.addEventListener(event,fn,{...options,signal:abort.signal});
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const mode=()=>document.querySelector('.theme-extra-active')?'extra':document.querySelector('.theme-sprint2-active')?'sprint2':'white';
  const views={
    white:{anchor:'top',question:'Хотите попробовать наше вино?)',toast:'Упс, вы, кажется, всё забыли… Начнём с первого глотка?'},
    sprint2:{anchor:'sprint2',question:'Хотите попробовать наше вино?)',toast:'Упс, генератор приготовил новую порцию. Проверим её ещё раз?'},
    extra:{anchor:'extra',question:'Хотите взглянуть на интерфейс другими глазами?',toast:'Новый взгляд загружен. Посмотрим, где красота встречается с удобством.'}
  };
  const offer=document.createElement('section');offer.className='wine-offer';offer.dataset.runtimeVersion='reading-v4';offer.hidden=true;offer.setAttribute('role','dialog');offer.setAttribute('aria-labelledby','report-offer-question');
  offer.innerHTML='<p id="report-offer-question"></p><div class="offer-actions"><button type="button" class="wine-offer-yes">Да</button><button type="button" class="wine-offer-no">Нет</button></div>';
  const toast=document.createElement('div');toast.hidden=true;toast.className='oops-toast';toast.setAttribute('role','status');toast.setAttribute('aria-live','polite');
  document.body.append(offer,toast);
  let frame=0,current=0,target=0,lastMode='',scroller=null,busy=false,timer=0,run=0,restoreFocus=null,lastTime=0;
  const dismissed=new Set();
  function close() {
    const restore=offer.contains(document.activeElement);
    offer.classList.remove('is-open');offer.hidden=true;
    if(restore)restoreFocus?.focus({preventScroll:true});
  }
  const findScroller=anchor=>{
    for(let e=anchor.parentElement;e;e=e.parentElement)
      if(/(auto|scroll)/.test(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+1)return e;
    return document.scrollingElement;
  };
  const resize=new ResizeObserver(schedule);
  function measure() {
    const next=mode(),start=document.getElementById(views[next].anchor),indicator=document.querySelector('.read-glass');
    if(!start||!indicator||!start.getClientRects().length)return;
    const nextScroller=findScroller(start);
    if(scroller!==nextScroller){resize.disconnect();scroller=nextScroller;resize.observe(scroller);}
    const doc=scroller===document.scrollingElement,viewportTop=doc?0:scroller.getBoundingClientRect().top+scroller.clientTop;
    const height=doc?innerHeight:scroller.clientHeight,top=scroller.scrollTop;
    const begin=start.getBoundingClientRect().top-viewportTop+top;
    const footer=document.querySelector('.site-footer');
    const end=footer?footer.getBoundingClientRect().bottom-viewportTop+top:scroller.scrollHeight;
    target=end-height-begin>1?Math.min(1,Math.max(0,(top-begin)/(end-height-begin))):0;
    if(lastMode!==next){run++;busy=false;current=target;close();toast.classList.remove('is-open');toast.hidden=true;lastMode=next;}
  }
  function paint(time) {
    frame=0;measure();
    const dt=lastTime?Math.min(64,time-lastTime):16;lastTime=time;
    current=reduced.matches?target:current+(target-current)*(1-Math.exp(-dt/70));
    if(Math.abs(current-target)<.0001)current=target;
    const indicator=document.querySelector('.read-glass'),percent=Math.round(current*100);
    if(indicator){
      indicator.querySelectorAll('.read-wine').forEach(rect=>{
        const bottom=Number(rect.getAttribute('data-fill-bottom')||32);
        rect.setAttribute('y',String(bottom-28*current));rect.setAttribute('height',String(28*current));
      });
      indicator.setAttribute('aria-valuenow',String(percent));
      const caption=indicator.querySelector('.read-percent');if(caption&&caption.textContent!==percent+'%')caption.textContent=percent+'%';
    }
    if(percent<90)dismissed.delete(lastMode);
    if(target>=.999&&percent===100&&!busy&&!dismissed.has(lastMode)){
      if(!offer.classList.contains('is-open')){restoreFocus=document.activeElement;offer.querySelector('p').textContent=views[lastMode].question;offer.hidden=false;offer.classList.add('is-open');}
    }else close();
    if(current!==target)frame=requestAnimationFrame(paint);else lastTime=0;
  }
  function schedule(){if(!frame)frame=requestAnimationFrame(paint);}
  on(offer,'click',event=>{
    if(event.target.closest('.wine-offer-no')){dismissed.add(mode());close();return;}
    if(!event.target.closest('.wine-offer-yes'))return;
    const selected=mode();busy=true;dismissed.add(selected);close();const token=++run;
    document.getElementById(views[selected].anchor)?.scrollIntoView({block:'start',behavior:reduced.matches?'auto':'smooth'});
    const started=performance.now();
    function done(){
      if(token!==run)return;
      if(current<.025||performance.now()-started>2500){busy=false;toast.textContent=views[selected].toast;toast.hidden=false;toast.classList.add('is-open');clearTimeout(timer);timer=setTimeout(()=>{toast.classList.remove('is-open');toast.hidden=true;},5000);}
      else requestAnimationFrame(done);
    }requestAnimationFrame(done);
  });
  on(document,'keydown',event=>{if(event.key==='Escape'){dismissed.add(mode());close();}});
  const paneRoutes=__REPORT_ROUTES__;
  let navigationRun=0;
  function routeToPane(id){return paneRoutes[id]||null;}
  function activatePane(route){
    const root=document.getElementById(route.anchor)?.closest('.output-area');
    const widget=root?.querySelector('marimo-tabs');
    const button=Array.from(widget?.shadowRoot?.querySelectorAll('[role="tab"]')||[]).find(e=>e.textContent.trim()===route.tab);
    if(button?.getAttribute('aria-selected')!=='true'){
      if(button){button.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,composed:true,button:0}));button.click();}
      return false;
    }
    if(route.select){
      const host=Array.from(root?.querySelectorAll('marimo-dropdown')||[]).find(e=>(e.getAttribute('data-label')||'').includes('Проверка'));
      const select=host?.shadowRoot?.querySelector('select');
      const option=Array.from(select?.options||[]).find(e=>e.textContent.trim()===route.select);
      if(!select||!option)return false;
      if(select.value!==option.value){select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true,composed:true}));return false;}
    }
    return true;
  }
  on(window,'click',event=>{
    const link=event.composedPath().find(e=>e instanceof Element&&e.matches('a[href^="#"]'));
    if(!link)return;
    const id=link.getAttribute('href').slice(1), route=routeToPane(id);
    let destination=document.getElementById(id);
    if(!destination&&!route)return;
    event.preventDefault();
    if(route)event.stopPropagation();
    const toc=link.closest('#lab-toc');if(toc?.matches(':popover-open'))toc.hidePopover();
    const started=performance.now(),token=++navigationRun;
    function navigate(){
      if(token!==navigationRun)return;
      if(route&&!activatePane(route)){if(performance.now()-started<10000)requestAnimationFrame(navigate);return;}
      destination=document.getElementById(id);
      if(destination){
        for(let p=destination.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
        destination.scrollIntoView({block:'start',behavior:reduced.matches?'auto':'smooth'});
        history.replaceState(null,'',link.getAttribute('href'));schedule();
      }else if(performance.now()-started<10000)requestAnimationFrame(navigate);
    }
    navigate();
  },{capture:true});
  on(document,'scroll',schedule,{passive:true,capture:true});on(document,'toggle',schedule,{capture:true});
  on(document,'load',schedule,{capture:true});on(window,'resize',schedule,{passive:true});on(window,'hashchange',schedule);
  const observer=new MutationObserver(records=>{
    if(records.every(r=>r.target instanceof Element&&r.target.closest('.read-glass,.wine-offer,.oops-toast')))return;
    schedule();
  });observer.observe(document.body,{childList:true,subtree:true});schedule();
  return ()=>{run++;abort.abort();resize.disconnect();observer.disconnect();cancelAnimationFrame(frame);clearTimeout(timer);offer.remove();toast.remove();};
}};
