(function(){
    var fi=document.querySelector('input[type=file]');
    var out=[];
    if(!fi){out.push('页面上没有 input[type=file]');}
    else{var cs=getComputedStyle(fi);
      out.push('input[type=file] display='+cs.display+' vis='+cs.visibility+' op='+cs.opacity+' pos='+cs.position+' w='+Math.round(fi.getBoundingClientRect().width)+' tabindex='+fi.getAttribute('tabindex'));
      out.push('  可聚焦? '+(!!(fi.offsetWidth||fi.offsetHeight||fi.getClientRects().length)));
    }
    var dz=document.querySelector('.upload-zone,.drop-zone,[class*=upload]');
    if(dz){out.push('dropzone: '+dz.tagName+'.'+dz.className.toString().slice(0,40)+' tabindex='+dz.getAttribute('tabindex')+' role='+dz.getAttribute('role')+' aria-label='+dz.getAttribute('aria-label'));
      out.push('  键盘事件: onclick='+(!!dz.onclick)+' onkeydown='+(!!dz.onkeydown));}
    return out.join('\n');})()