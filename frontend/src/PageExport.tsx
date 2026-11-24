import {useState} from 'react';

export default function PageExport(){
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 async function download(){
  const root=document.querySelector<HTMLElement>('.shell');
  if(!root||busy)return;
  setBusy(true);setError('');
  const previousInert=root.inert;
  const x=window.scrollX,y=window.scrollY;
  let timer:ReturnType<typeof setTimeout>|undefined;
  try{
   await document.fonts.ready;
   root.classList.add('page-export');root.inert=true;
   await new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve())));
   const width=Math.ceil(root.scrollWidth),height=Math.ceil(root.scrollHeight);
   // Keep the whole page within browser canvas limits, even with expanded guides.
   const pixelRatio=Math.min(2,Math.sqrt(24_000_000/(width*height)),16000/Math.max(width,height));
   if(pixelRatio<.25)throw new Error('Página muito extensa. Recolha alguns detalhes e tente novamente.');
   const capture=async()=>{
    const {toCanvas}=await import('html-to-image');
    const canvas=await toCanvas(root,{width,height,pixelRatio,skipAutoScale:true,
     backgroundColor:'#f4f6fa',filter:node=>!node.hasAttribute?.('data-export-ignore')});
    return new Promise<Blob>((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('Não foi possível gerar o JPG.')),'image/jpeg',.95));
   };
   const blob=await Promise.race([capture(),new Promise<never>((_,reject)=>{
    timer=setTimeout(()=>reject(new Error('A captura demorou demais. Tente recolher alguns detalhes.')),20000);
   })]);
   if(!root.isConnected)return;
   const url=URL.createObjectURL(blob);
   const link=document.createElement('a');
   const title=(document.querySelector('h1')?.textContent||'pagina').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
   link.href=url;link.download=`enterprise-ai-workbench-${title}.jpg`;
   document.body.append(link);link.click();link.remove();
   setTimeout(()=>URL.revokeObjectURL(url),60000);
  }catch(reason){setError(reason instanceof Error?reason.message:'Não foi possível gerar o JPG. Tente novamente.');}
  finally{
   clearTimeout(timer);root.classList.remove('page-export');root.inert=previousInert;
   if(root.isConnected)window.scrollTo(x,y);
   setBusy(false);
  }
 }
 return <div className="page-export-control" data-export-ignore="true"><button className="logout-button" onClick={download} disabled={busy} aria-label="Baixar página completa em JPG">{busy?'Gerando…':'↓ Baixar JPG'}</button>{error&&<span className="export-error" role="alert">{error}</span>}</div>;
}
