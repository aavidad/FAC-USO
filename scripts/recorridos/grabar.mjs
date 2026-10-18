// Grabación pública FAC-USO con Chrome del sistema y Playwright ya instalado en ETF.
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, writeFileSync, rmSync, realpathSync } from 'node:fs';
import { resolve, basename } from 'node:path';

const require = createRequire(process.env.FACUSO_PLAYWRIGHT_PACKAGE || '/home/alberto/Trabajo/ETF/web/package.json');
const { chromium } = require('playwright-core');
const ORIGEN = 'http://127.0.0.1:18086';
const SALIDA = realpathSync(resolve(process.env.FACUSO_VIDEO_OUTPUT || '/home/alberto/Vídeos/FAC-USO'));
const REPO = resolve(new URL('../..', import.meta.url).pathname);
if (SALIDA === REPO || SALIDA.startsWith(REPO+'/')) throw new Error('Salida fuera del repositorio requerida');
const carpeta = process.argv[2] && realpathSync(process.argv[2]);
if (!carpeta || !carpeta.startsWith(SALIDA+'/')) throw new Error('Carpeta de recorrido fuera de salida');
const tramos = JSON.parse(readFileSync(resolve(carpeta, 'tramos.json'), 'utf8'));
const raw = resolve(carpeta, 'raw');
mkdirSync(raw, { recursive: true });
const espera = ms => new Promise(r => setTimeout(r, ms));

async function preparar(page) {
  await page.context().route('**/*', async route => {
    const peticion = route.request();
    let u;
    try { u = new URL(peticion.url()); } catch { return route.abort(); }
    if (['data:', 'about:'].includes(u.protocol)) return route.continue();
    if (peticion.method() !== 'GET' || u.origin !== ORIGEN) return route.abort();
    try {
      const respuesta=await route.fetch({maxRedirects:0});
      if (respuesta.status()>=300 && respuesta.status()<400) return route.abort();
      return route.fulfill({response:respuesta});
    } catch { return route.abort(); }
  });
  await page.addInitScript(() => {
    document.addEventListener('DOMContentLoaded', () => {
      const cursor = document.createElement('div');
      cursor.id = 'video-cursor';
      Object.assign(cursor.style, { position: 'fixed', zIndex: 2147483647, width: '23px', height: '31px',
        left: '50%', top: '40%', pointerEvents: 'none', background: '#cf2c1b',
        clipPath: 'polygon(0 0,0 88%,29% 68%,50% 100%,67% 91%,46% 58%,88% 60%)',
        filter: 'drop-shadow(1px 1px 1px white)' });
      document.body.append(cursor);
      document.addEventListener('mousemove', e => { cursor.style.left = `${e.clientX}px`; cursor.style.top = `${e.clientY}px`; });
    }, { once: true });
  });
}

async function apuntar(page, loc) {
  await loc.scrollIntoViewIfNeeded();
  const b = await loc.boundingBox();
  if (!b) throw new Error('Control no visible: ' + page.url());
  await page.mouse.move(b.x+b.width/2, b.y+b.height/2, { steps: 12 });
  await loc.evaluate(e => { e.style.outline = '3px solid #cf2c1b'; e.style.outlineOffset = '3px'; });
  await espera(300);
}
async function pulsar(page, path, scope='main') {
  const loc = page.locator(`${scope} a[href="${ORIGEN}${path}"]`).first();
  if (await loc.count() !== 1) throw new Error(`No hay enlace ${path} en ${page.url()}`);
  await apuntar(page, loc);
  await Promise.all([page.waitForURL(u => u.pathname === path, { timeout: 12000 }), loc.click()]);
  await page.locator('h1').first().waitFor({ timeout: 12000 });
  await espera(350);
}
async function nav(page, path) { await pulsar(page, path, path === '/noticias/' ? 'footer' : 'nav[aria-label="Navegación principal"]'); }
async function scroll(page, n=600) { await page.mouse.move(1150, 600, { steps: 10 }); await page.mouse.wheel(0,n); await espera(700); }
async function subir(page) { await page.mouse.wheel(0,-1800); await espera(500); }
async function seleccionar(page, nombre, valor) {
  const loc=page.locator(`main select[name="${nombre}"]`);
  await apuntar(page,loc);
  await loc.selectOption(valor);
  await espera(500);
}
async function enviar(page) {
  const loc=page.locator('main button:has-text("Ver noticias")').first();
  await apuntar(page,loc);
  await Promise.all([page.waitForLoadState('domcontentloaded'),loc.click()]);
  await espera(500);
}
async function rotulo(page, titulo) {
  await page.evaluate(t => {
    document.querySelector('#video-rotulo')?.remove();
    const n=document.createElement('div'); n.id='video-rotulo'; n.textContent=t;
    Object.assign(n.style,{position:'fixed',left:'3%',bottom:'2%',zIndex:2147483646,padding:'10px 16px',
      color:'white',background:'#00683d',borderRadius:'6px',font:'bold 21px system-ui',pointerEvents:'none',
      boxShadow:'0 2px 10px #0005'}); document.body.append(n);
  }, titulo);
}
async function esquema(page, titulo, lineas) {
  await page.evaluate(({titulo,lineas}) => {
    document.querySelector('#video-esquema')?.remove();
    const d=document.createElement('section'); d.id='video-esquema';
    Object.assign(d.style,{position:'fixed',zIndex:2147483645,top:'11%',left:'9%',right:'9%',
      padding:'30px 38px',borderRadius:'14px',background:'#fffffffa',boxShadow:'0 8px 40px #0008',
      borderTop:'10px solid #00683d',fontFamily:'system-ui',color:'#183d2d',pointerEvents:'none'});
    const h=document.createElement('h2'); h.textContent=titulo; h.style='font-size:32px;margin:0 0 8px';
    const p=document.createElement('p'); p.textContent='Esquema explicativo · Instalación local';p.style='font-size:17px;margin:0 0 20px;color:#666';
    const row=document.createElement('div'); row.style='display:flex;gap:8px;align-items:stretch;justify-content:space-between';
    lineas.forEach((x,i)=>{const e=document.createElement('div');e.textContent=x;e.style='flex:1;padding:14px 9px;background:#e9f4ed;border:2px solid #00683d;border-radius:8px;text-align:center;font-weight:700;font-size:20px';row.append(e);if(i<lineas.length-1){const a=document.createElement('span');a.textContent='→';a.style='align-self:center;font-size:29px;color:#cf2c1b';row.append(a)}});
    d.append(h,p,row);document.body.append(d);
  },{titulo,lineas});
}

const acciones={
  '01a': async p => {await rotulo(p,'Bienvenidas y bienvenidos');await espera(2800);await nav(p,'/territorios/');await pulsar(p,'/territorios/almeria/');await scroll(p,450);await nav(p,'/noticias/');await scroll(p,500);},
  '01b': async p => {await rotulo(p,'Portada · información y empleo');await scroll(p,520);await scroll(p,650);},
  '02': async p => {await nav(p,'/conocenos/');await rotulo(p,'Conócenos y contacto');await pulsar(p,'/conocenos/que-es-la-uso-andalucia/');await scroll(p,450);await nav(p,'/conocenos/');await pulsar(p,'/conocenos/contacto/');await scroll(p,400);},
  '03': async p => {await nav(p,'/servicios-a-la-afiliacion/');await rotulo(p,'Cuatro servicios a la afiliación');await espera(1500);for(const path of ['promociones','formacion','asesoria-juridica','crs']){await pulsar(p,`/servicios-a-la-afiliacion/${path}/`);await scroll(p,320);await espera(2500);await nav(p,'/servicios-a-la-afiliacion/');}},
  '04': async p => {await nav(p,'/informacion/');await rotulo(p,'Información y empleo público');await espera(1500);for(const path of ['accion-sindical','salud-laboral','igualdad']){await pulsar(p,`/informacion/${path}/`);await scroll(p,260);await espera(2500);await nav(p,'/informacion/');}await pulsar(p,'/informacion/empleo-publico/');await scroll(p,500);await espera(2500);},
  '05': async p => {await nav(p,'/sectores/');await rotulo(p,'Cinco sectores y especialidades');await espera(1800);for(const path of ['sanidad','administracion-local','administracion-autonomica']){await pulsar(p,`/sectores/${path}/`);await scroll(p,480);await espera(5200);await nav(p,'/sectores/');}},
  '06': async p => {await nav(p,'/territorios/');await rotulo(p,'Ocho provincias y OPAEF');await espera(1400);await pulsar(p,'/territorios/granada/');await scroll(p,480);await espera(1400);await pulsar(p,'/territorios/granada/diputacion-de-granada/');await espera(1500);await nav(p,'/territorios/');await pulsar(p,'/territorios/sevilla/');await espera(1200);await pulsar(p,'/territorios/sevilla/opaef/');await espera(1800);await pulsar(p,'/territorios/sevilla/opaef/uso-opaef/');await espera(1800);await pulsar(p,'/territorios/sevilla/opaef/observatorio-igualdad-opaef/');await scroll(p,450);await espera(2800);},
  '07': async p => {await nav(p,'/territorios/');await pulsar(p,'/territorios/almeria/');await pulsar(p,'/territorios/almeria/empleo-publico-almeria/');await rotulo(p,'Almería: BOP y BOE');await scroll(p,300);await seleccionar(p,'fac_fuente','boe');await enviar(p);await scroll(p,370);},
  '08': async p => {await nav(p,'/noticias/');await seleccionar(p,'fac_materia','accion-sindical');await enviar(p);await pulsar(p,'/spj-uso-andalucia-marca-la-hoja-de-ruta-para-la-subida-retributiva-del-personal-de-justicia/');await rotulo(p,'Imagen, fecha y fuente de origen');await scroll(p,450);const mas=p.locator('main summary').filter({hasText:'Fuentes y más información'}).first();await apuntar(p,mas);await mas.click();await espera(500);const fuente=p.locator('main a[href^="https://"]').first();await apuntar(p,fuente);await espera(2400);},
  '09': async p => {await nav(p,'/noticias/');await rotulo(p,'Filtros combinados');await seleccionar(p,'fac_sector','administracion-local');await seleccionar(p,'fac_materia','empleo-publico');await seleccionar(p,'fac_territorio','almeria');await enviar(p);await scroll(p,400);},
  '10': async p => {await nav(p,'/conocenos/');await pulsar(p,'/conocenos/fotos/');await rotulo(p,'Fotos y créditos');await scroll(p,610);await scroll(p,700);await nav(p,'/enlaces/');await scroll(p,500);await p.locator('footer a[href="'+ORIGEN+'/afiliacion/"]').first().click();await scroll(p,450);},
  '11': async p => {await p.setViewportSize({width:390,height:844});await p.reload();await rotulo(p,'Navegación móvil');await apuntar(p,p.locator('.fac-menu-toggle'));await p.locator('.fac-menu-toggle').click();await espera(2200);const sub=p.getByRole('button',{name:'Abrir apartados de Conócenos'});await apuntar(p,sub);await sub.click();await espera(2200);await pulsar(p,'/conocenos/contacto/','nav[aria-label="Navegación principal"]');await scroll(p,350);},
  '12': async p => {await nav(p,'/territorios/');await pulsar(p,'/territorios/almeria/');await pulsar(p,'/territorios/almeria/empleo-publico-almeria/');await esquema(p,'Cómo se actualiza: fuentes',['BOE, siete BOP y RSS','Conector provincial','API REST','Provincia, materia, sector']);},
  '13': async p => {await nav(p,'/noticias/');await esquema(p,'Cómo se actualiza: control',['Cron horario','Lector Almería','Ocho bots','Validación y borrador']);},
  '14': async p => {await nav(p,'/territorios/');await pulsar(p,'/territorios/malaga/');await pulsar(p,'/territorios/malaga/empleo-publico-malaga/');await esquema(p,'Cómo se actualiza: alcance',['Málaga: BOE y RSS','BOP sin extractor activo','Revisión humana']);}
};

const navegador=await chromium.launch({executablePath:process.env.FACUSO_CHROME || '/usr/bin/google-chrome',headless:true,args:['--no-first-run','--disable-background-networking']});
const evidencia=[];
try { evidencia.push(...JSON.parse(readFileSync(resolve(carpeta,'escenas.json'),'utf8'))); } catch { /* primera grabación */ }
const regrabar=new Set((process.env.FACUSO_REGRABAR || '').split(',').filter(Boolean));
for (const id of regrabar) {
  if (!tramos.some(t=>t.id===id)) throw new Error(`Tramo desconocido: ${id}`);
  const n=evidencia.findIndex(e=>e.id===id);
  if (n>=0) evidencia.splice(n,1);
  for(const prefijo of ['escena-','captura-']) rmSync(resolve(carpeta,`${prefijo}${id}.${prefijo==='escena-'?'webm':'png'}`),{force:true});
}
try {
  for (const tramo of tramos) {
    const id=tramo.id;
    if (evidencia.some(e => e.id === id)) { process.stdout.write(`Escena ${id}: conservada\n`); continue; }
    const ctx=await navegador.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1,serviceWorkers:'block',
      recordVideo:{dir:raw,size:{width:1440,height:900}},acceptDownloads:false});
    if (typeof ctx.routeWebSocket === 'function') await ctx.routeWebSocket('**/*', ws => ws.close());
    const p=await ctx.newPage();
    await preparar(p);
    const inicio=performance.now();
    try {
      await p.goto(ORIGEN+'/',{waitUntil:'domcontentloaded'});
      await acciones[id](p);
      const objetivo=(tramo.duracion_s+1.8)*1000;
      await espera(Math.max(0,objetivo-(performance.now()-inicio)));
      const imagen=resolve(carpeta,`captura-${id}.png`);
      await p.screenshot({path:imagen});
      const ultimo=p.url();
      const real=(performance.now()-inicio)/1000;
      const video=p.video();
      await ctx.close();
      const webm=resolve(carpeta,`escena-${id}.webm`);
      await video.saveAs(webm);
      evidencia.push({id,titulo:tramo.titulo,url:ultimo,imagen:basename(imagen),video:basename(webm),
        voz_s:tramo.duracion_s,grabacion_s:real});
      evidencia.sort((a,b)=>tramos.findIndex(t=>t.id===a.id)-tramos.findIndex(t=>t.id===b.id));
      writeFileSync(resolve(carpeta,'escenas.json'),JSON.stringify(evidencia,null,2));
      process.stdout.write(`Escena ${id}: ${real.toFixed(1)} s · ${ultimo}\n`);
    } catch (e) {await ctx.close();throw new Error(`Escena ${id}: ${e.message}`,{cause:e});}
  }
} finally {await navegador.close();}
