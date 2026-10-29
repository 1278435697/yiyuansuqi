import { spawn } from 'child_process';
import fs from 'fs';
const EDGE='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';const port=9353;
const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
const child=spawn(EDGE,['--headless=new','--disable-gpu','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox',`--remote-debugging-port=${port}`,`--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_one_${Date.now()}`,'--window-size=1440,900','about:blank'],{stdio:'ignore'});
async function target(){for(let i=0;i<60;i++){try{const l=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();const p=l.find(t=>t.type==='page');if(p)return p;}catch{}await sleep(250);}throw new Error('no target');}
function cdp(ws){let id=0;const pend=new Map();ws.addEventListener('message',(ev)=>{const m=JSON.parse(ev.data);if(m.id&&pend.has(m.id)){const p=pend.get(m.id);pend.delete(m.id);m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result);}});return (method,params={})=>new Promise((res,rej)=>{const n=++id;pend.set(n,{resolve:res,reject:rej});ws.send(JSON.stringify({id:n,method,params}));});}
const t=await target();const ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));const send=cdp(ws);
await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
const [url,scrollTo,out]=process.argv.slice(2);
await send('Page.navigate',{url});await sleep(4000);
await send('Runtime.evaluate',{expression:`window.scrollTo(0,${scrollTo})`});await sleep(1200);
const s=await send('Page.captureScreenshot',{format:'jpeg',quality:70});
fs.writeFileSync(out,Buffer.from(s.data,'base64'));console.log('saved '+out);
ws.close();child.kill();
