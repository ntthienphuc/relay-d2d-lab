export async function api(path,data){
  const r=await fetch('/api/'+path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const value=await r.json();if(!r.ok)throw new Error(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail));return value;
}
export function toast(message,error=false){const n=document.getElementById('toast');n.textContent=message;n.className=error?'visible error':'visible';n.style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>n.style.display='none',6000);}
