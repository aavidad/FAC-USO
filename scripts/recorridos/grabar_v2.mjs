// Captura real por frase. El montaje conserva las transiciones y prolonga la lectura.
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync,existsSync,realpathSync} from 'node:fs';
import {resolve} from 'node:path';
const require=createRequire(process.env.FACUSO_PLAYWRIGHT_PACKAGE || '/home/alberto/Trabajo/ETF/web/package.json');
const {chromium}=require('playwright-core');
const folder=realpathSync(process.argv[2]);
const allowed=realpathSync(process.env.FACUSO_VIDEO_OUTPUT || '/home/alberto/Vídeos/FAC-USO');
if(!folder.startsWith(allowed+'/'))throw Error('Salida fuera de la carpeta de vídeos');
const plan=JSON.parse(readFileSync(resolve(folder,'plan.json'),'utf8'));
const origin=new URL(plan.origin).origin;
if(origin!=='https://facuso.cidonia.cloud')throw Error('Origen de revisión no autorizado');
const preflight=process.argv.includes('--preflight');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const browser=await chromium.launch({executablePath:process.env.FACUSO_CHROME || '/usr/bin/google-chrome',headless:true,args:['--disable-background-networking']});
mkdirSync(resolve(folder,'raw'),{recursive:true});
let mobile=false;
async function move(page,loc){
 await loc.waitFor({state:'visible'});await loc.scrollIntoViewIfNeeded();
 const b=await loc.boundingBox();if(!b)throw Error('Elemento fuera de pantalla');
 await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:14});await wait(preflight?30:180);
}
async function top(page){await page.evaluate(()=>scrollTo({top:0,behavior:'smooth'}));await wait(preflight?120:650);}
async function center(page,loc){
 await loc.waitFor({state:'visible'});
 await loc.evaluate(el=>el.scrollIntoView({block:'center',behavior:'smooth'}));await wait(preflight?180:750);
}
async function click(page,loc){
 await move(page,loc);
 await Promise.all([page.waitForNavigation({waitUntil:'load',timeout:20000}),loc.click()]);
 await wait(preflight?20:200);
}
async function navigate(page,path){
 const url=origin+path;
 if(new URL(page.url()).pathname===path&&!new URL(page.url()).search){await top(page);return;}
 const nav=page.locator('.fac-navigation');
 const target=nav.locator(`a[href="${url}"]`).first();
 if(await target.count()){
  await top(page);
  if(mobile){const menu=page.locator('.fac-menu-toggle');if(await menu.getAttribute('aria-expanded')!=='true')await menu.click();}
  if(!await target.isVisible()){
   const rootHref=await target.evaluate(el=>{let li=el.closest('li');while(li.parentElement.closest('li'))li=li.parentElement.closest('li');return li.querySelector(':scope > a').href;});
   if(mobile){const root=nav.locator(`a[href="${rootHref}"]`).first().locator('xpath=..');const toggle=root.locator(':scope > button');if(await toggle.getAttribute('aria-expanded')!=='true')await toggle.click();}
   else await nav.locator(`:scope > ul > li > a[href="${rootHref}"]`).hover();
  }
  await click(page,target);
 }else{
  const body=page.locator(`main a[href="${url}"]`).first();
  const footer=page.locator(`footer a[href="${url}"]`).first();
  if(await body.count())await click(page,body);else if(await footer.count())await click(page,footer);else throw Error(`No hay enlace real a ${path} desde ${page.url()}`);
 }
 if(new URL(page.url()).pathname!==path)throw Error('Navegación no confirmada: '+path);
 await top(page);
}
async function diagram(page,op){
 await top(page);
 await page.evaluate(({title,boxes})=>{
  document.querySelector('#v2-diagram')?.remove();
  const div=document.createElement('section');div.id='v2-diagram';
  Object.assign(div.style,{position:'fixed',left:'7%',right:'7%',top:'36%',zIndex:'10000',background:'#fff',border:'2px solid #00683d',borderTop:'9px solid #00683d',borderRadius:'12px',padding:'32px',boxShadow:'0 10px 40px #0004',pointerEvents:'none',fontFamily:'system-ui'});
  const label=document.createElement('p');label.textContent='EXPLICACIÓN DEL FUNCIONAMIENTO · FAC-USO ANDALUCÍA';label.style='font-size:14px;color:#00683d;font-weight:700;letter-spacing:1px';
  const h=document.createElement('h2');h.textContent=title;h.style='font-size:30px;line-height:1.25;margin:12px 0 25px';
  const row=document.createElement('div');row.style='display:flex;gap:12px';
  for(const [i,text] of boxes.entries()){
   if(i){const arrow=document.createElement('span');arrow.textContent='→';arrow.style='align-self:center;font-size:25px;color:#cf2c1b';row.append(arrow);}
   const box=document.createElement('div');box.textContent=text;box.style='flex:1;background:#edf5ef;border:1px solid #00683d;border-radius:8px;padding:22px 12px;text-align:center;font-size:21px;font-weight:650;line-height:1.45';row.append(box);
  }
  div.append(label,h,row);document.body.append(div);
 },op);
}
async function action(page,op){
 switch(op.type){
 case 'home':if(new URL(page.url()).pathname!=='/'||new URL(page.url()).search)await click(page,page.locator('.fac-brand'));await top(page);break;
 case 'navigate':await navigate(page,op.path);break;
 case 'menu':await top(page);await page.locator(`.fac-navigation > ul > li > a[href="${origin+op.path}"]`).hover();await wait(150);break;
 case 'close_menu':await page.mouse.move(1380,360,{steps:15});await wait(100);break;
 case 'heading':await center(page,page.locator('main h2, main h3').filter({hasText:op.text}).first());break;
 case 'sections':await center(page,page.locator('main .fac-sections').first());break;
 case 'content':await center(page,page.locator('main .fac-content > p').first());break;
 case 'point':await center(page,page.locator(op.selector));await move(page,page.locator(op.selector));break;
 case 'select':{const loc=page.locator(`main select[name="${op.name}"]`);await center(page,loc);await move(page,loc);await loc.selectOption(op.value);break;}
 case 'submit':await click(page,page.getByRole('button',{name:'Ver noticias',exact:true}));await center(page,page.locator('main .fac-filters').first());break;
 case 'cards':await center(page,page.locator('main .fac-card').first());break;
 case 'article_image':await center(page,page.locator('.fac-article-photo'));break;
 case 'sources':{const details=page.locator('main .fac-sources');await center(page,details);const sum=details.locator('summary');if(!await details.getAttribute('open'))await sum.click();await center(page,details);break;}
 case 'reset':await click(page,page.getByRole('link',{name:'Restablecer',exact:true}).first());await center(page,page.locator('main .fac-filters').first());break;
 case 'mobile':mobile=true;await page.setViewportSize({width:390,height:844});break;
 case 'desktop':mobile=false;await page.setViewportSize(plan.viewport);break;
 case 'mobile_menu':await move(page,page.locator('.fac-menu-toggle'));await page.locator('.fac-menu-toggle').click();break;
 case 'mobile_submenu':{const loc=page.getByRole('button',{name:'Abrir apartados de Conócenos'});await move(page,loc);await loc.click();break;}
 case 'diagram':await diagram(page,op);break;
 case 'clear_diagram':await page.evaluate(()=>document.querySelector('#v2-diagram')?.remove());break;
 default:throw Error('Acción desconocida '+op.type);
 }
}
try{
 for(const [index,chapter] of plan.chapters.entries()){
  const id=String(index+1).padStart(2,'0');const meta=resolve(folder,`chapter-${id}.json`);
  if(!preflight&&existsSync(meta)){console.log('Conservado capítulo '+id);continue;}
  mobile=false;
  const ctx=await browser.newContext({viewport:plan.viewport,deviceScaleFactor:1,serviceWorkers:'block',acceptDownloads:false,
   ...(!preflight?{recordVideo:{dir:resolve(folder,'raw'),size:plan.viewport}}:{})});
  await ctx.route('**/*',async route=>{const req=route.request();const u=new URL(req.url());if(['data:','about:'].includes(u.protocol))return route.continue();if(req.method()!=='GET'||u.origin!==origin)return route.abort();try{const r=await route.fetch({maxRedirects:0});if(r.status()>=300&&r.status()<400)return route.abort();return route.fulfill({response:r});}catch{return route.abort();}});
  if(typeof ctx.routeWebSocket==='function')await ctx.routeWebSocket('**/*',ws=>ws.close());
  await ctx.addInitScript(()=>document.addEventListener('DOMContentLoaded',()=>{
   const cursor=document.createElement('div');cursor.id='v2-cursor';cursor.style='position:fixed;left:80%;top:30%;width:22px;height:30px;background:#cf2c1b;clip-path:polygon(0 0,0 90%,28% 68%,48% 100%,65% 91%,44% 60%,85% 60%);pointer-events:none;z-index:2147483647;filter:drop-shadow(0 0 2px white)';document.body.append(cursor);document.addEventListener('mousemove',e=>{cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px';});
  }));
  const zero=performance.now();const clock=()=> (performance.now()-zero)/1000;const page=await ctx.newPage();
  try{
   await page.goto(origin+'/',{waitUntil:'load'});
   // Los enlaces de preparación no se incluyen en el montaje. Así ninguna
   // frase empieza con una ráfaga de páginas que todavía no se está explicando.
   const prepared = new Map();
   if(id==='07') { await navigate(page,'/territorios/sevilla/');prepared.set(chapter.phases[0].id,1); }
   if(id==='08') { await navigate(page,'/territorios/almeria/');prepared.set(chapter.phases[0].id,1); }
   if(id==='09') { for(const op of chapter.phases[0].actions.slice(0,-1))await action(page,op);prepared.set(chapter.phases[0].id,chapter.phases[0].actions.length-1); }
   if(id==='12') { await action(page,{type:'mobile'});await action(page,{type:'home'});prepared.set(chapter.phases[0].id,2); }
   let anchorClock=0;
   if(!preflight){await page.evaluate(()=>{const d=document.createElement('div');d.id='v2-anchor';d.style='position:fixed;left:0;right:0;top:0;height:80px;background:#ff00ff;z-index:2147483647';document.body.append(d);});anchorClock=clock();await page.screenshot({path:resolve(folder,`anchor-${id}.png`)});await wait(700);await page.evaluate(()=>document.querySelector('#v2-anchor').remove());await wait(100);}
   const phases=[];
   for(const phase of chapter.phases){
    const effectiveActions=phase.actions.slice(prepared.get(phase.id)||0);
    const start=clock();for(const op of effectiveActions)await action(page,op);const actionEnd=clock();
    await wait(preflight?80:1000);
    const end=clock();
    if(!preflight)await page.screenshot({path:resolve(folder,`phase-${phase.id}.png`)});
    phases.push({...phase,effective_actions:effectiveActions,start,end,action_end:actionEnd,mobile,url:page.url(),viewport:page.viewportSize()});
    console.log(`${preflight?'PREVIO':'GRABADO'} ${phase.id} · ${chapter.title} · ${(end-start).toFixed(2)}s`);
   }
   const video=page.video();await ctx.close();
   if(!preflight){await video.saveAs(resolve(folder,`chapter-${id}.webm`));writeFileSync(meta,JSON.stringify({id,title:chapter.title,anchor_clock:anchorClock,phases},null,2));}
  }catch(error){await ctx.close();throw new Error(`Capítulo ${id}: ${error.message}`,{cause:error});}
 }
}finally{await browser.close();}
