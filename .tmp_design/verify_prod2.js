import { spawn } from 'child_process';
import fs from 'fs';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = 9348;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new','--disable-gpu','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox',`--remote-debugging-port=${port}`,`--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_prod2_${Date.now()}`,'--window-size=1440,1000','about:blank'], { stdio: 'ignore' });
async function target(){for(let i=0;i<60;i++){try{const l=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();const p=l.find(t=>t.type==='page');if(p)return p;}catch{}await sleep(250);}throw new Error('no target');}
function cdp(ws){let id=0;const pend=new Map();const events=[];ws.addEventListener('message',(ev)=>{const m=JSON.parse(ev.data);if(m.id&&pend.has(m.id)){const p=pend.get(m.id);pend.delete(m.id);m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')events.push(m.params.exceptionDetails?.exception?.description||m.params.exceptionDetails?.text);});return Object.assign((method,params={})=>new Promise((res,rej)=>{const n=++id;pend.set(n,{resolve:res,reject:rej});ws.send(JSON.stringify({id:n,method,params}));}),{events});}
const t=await target();const ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));const send=cdp(ws);
await send('Runtime.enable');await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
await send('Page.navigate',{url:'http://47.93.14.11/'});await sleep(2000);
for(let i=0;i<30;i++){if(!(await send('Runtime.evaluate',{expression:`!!document.querySelector('#yisu-preloader, .preloader, [class*=preload]')`,returnByValue:true})).result.value)break;await sleep(700);}
await sleep(1200);
const L=JSON.parse((await send('Runtime.evaluate',{expression:`JSON.stringify({w:document.documentElement.clientWidth,h:document.documentElement.clientHeight})`,returnByValue:true})).result.value);
console.log('视口',JSON.stringify(L));
const rect=async(sel)=>JSON.parse((await send('Runtime.evaluate',{expression:`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return JSON.stringify(null);const b=e.getBoundingClientRect();return JSON.stringify({x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)})})()`,returnByValue:true})).result.value);
const mouse=async(type,x,y,button='none',clickCount=0)=>send('Input.dispatchMouseEvent',{type,x,y,button,clickCount});
// 球默认在右下角，直接点开
const b=await rect('.ai-float');console.log('球',JSON.stringify(b));
await mouse('mousePressed',b.x+29,b.y+29,'left',1);await mouse('mouseReleased',b.x+29,b.y+29,'left',1);await sleep(600);
const p=await rect('.af-panel');const g=JSON.parse((await send('Runtime.evaluate',{expression:`(()=>{const e=document.querySelector('.af-panel');const cs=getComputedStyle(e);return JSON.stringify({h:Math.round(e.getBoundingClientRect().height),overflow:cs.overflow,msgs:Math.round(document.querySelector('.af-msgs').getBoundingClientRect().height),head:Math.round(document.querySelector('.af-head').getBoundingClientRect().height),input:Math.round(document.querySelector('.af-input').getBoundingClientRect().height),dia:cs.getPropertyValue('overflow')})})()`,returnByValue:true})).result.value);
console.log('面板',JSON.stringify(p),'度量',JSON.stringify(g));
console.log((g.h===520?'PASS':'FAIL')+' 右下角打开面板高度 520  h='+g.h);
console.log((Math.abs(g.msgs+g.head+g.input+2-g.h)<2?'PASS':'FAIL')+' 头部+聊天区+输入行正好铺满面板');
console.log((p&&p.y>=0&&p.x>=0&&p.x+p.w<=L.w+1?'PASS':'FAIL')+' 面板不出视口 '+JSON.stringify(p));
await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await sleep(400);
// 拖到最顶部再打开：高度应按剩余空间收缩，且不能出屏
const b2=await rect('.ai-float');
await mouse('mousePressed',b2.x+29,b2.y+29,'left',1);
for(let i=1;i<=12;i++){await mouse('mouseMoved',Math.round(b2.x+29+(L.w*0.5)),Math.round(b2.y+29-(b2.y-20)*i/12),'left');await sleep(25);}
await mouse('mouseReleased',Math.round(b2.x+29+L.w*0.5),20,'left',1);await sleep(400);
const b3=await rect('.ai-float');console.log('拖到顶部后球',JSON.stringify(b3));
await mouse('mousePressed',b3.x+29,b3.y+29,'left',1);await mouse('mouseReleased',b3.x+29,b3.y+29,'left',1);await sleep(600);
const p2=await rect('.af-panel');
console.log((p2&&p2.y>=b3.y+58&&p2.y+p2.h<=L.h+1?'PASS':'FAIL')+' 顶部球：面板朝下开且不出屏 '+JSON.stringify(p2));
const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/audit/prod-top.png',Buffer.from(shot.data,'base64'));
const errs=send.events.filter(e=>!/Network Error|ERR_FAILED|AxiosError/i.test(e));
console.log((errs.length===0?'PASS':'FAIL')+' 无运行异常 '+errs.slice(0,2).join('|').slice(0,200));
ws.close();child.kill();
