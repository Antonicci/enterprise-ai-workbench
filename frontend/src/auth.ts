import { InMemoryWebStorage, UserManager, WebStorageStateStore } from 'oidc-client-ts';
export type AuthSettings = {mode:'demo'|'oidc';authority:string|null;client_id:string;scope:string};
export class SessionExpiredError extends Error {}
const expiryListeners=new Set<()=>void>();
export function onSessionExpired(listener:()=>void){expiryListeners.add(listener);return()=>{expiryListeners.delete(listener);};}
function notifyExpiry(){for(const listener of expiryListeners)listener();}
let manager:UserManager|null=null;
let initialization:Promise<{settings:AuthSettings;authenticated:boolean}>|null=null;
export function initializeAuth(){
 if(!initialization) initialization=(async()=>{
  const response=await fetch('/api/auth/config');
  if(!response.ok) throw new Error('Não foi possível carregar a configuração de identidade.');
  const settings:AuthSettings=await response.json();
  if(settings.mode==='oidc'){
   manager=new UserManager({authority:settings.authority!,client_id:settings.client_id,response_type:'code',
    redirect_uri:location.origin+'/auth/callback',post_logout_redirect_uri:location.origin+'/',scope:settings.scope,
    automaticSilentRenew:false,monitorSession:false,loadUserInfo:false,
    userStore:new WebStorageStateStore({store:new InMemoryWebStorage()}),
    stateStore:new WebStorageStateStore({store:sessionStorage})});
   manager.events.addAccessTokenExpired(notifyExpiry);
   if(location.pathname==='/auth/callback'){
    try{await manager.signinRedirectCallback();}finally{history.replaceState({},'', '/');}
   }
   const user=await manager.getUser();
   return {settings,authenticated:!!user&&!user.expired};
  }
  return {settings,authenticated:false};
 })();
 return initialization;
}
export async function accessToken(demoToken:string){
 if(!manager) return demoToken;
 const user=await manager.getUser();
 if(!user||user.expired){notifyExpiry();throw new SessionExpiredError('Sua sessão expirou. Entre novamente.');}
 return user.access_token;
}
export async function login(){await manager?.signinRedirect();}
export async function logout(){await manager?.signoutRedirect();}
