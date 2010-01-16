/*
	Copyright (c) 2004-2006, The Dojo Foundation
	All Rights Reserved.

	Licensed under the Academic Free License version 2.1 or above OR the
	modified BSD license. For more information on Dojo licensing, see:

		http://dojotoolkit.org/community/licensing.shtml
*/

/*
	This is a compiled version of Dojo, built for deployment and not for
	development. To get an editable version, please visit:

		http://dojotoolkit.org

	for documentation and information on getting the source.
*/

if(typeof dojo=="undefined"){
var dj_global=this;
var dj_currentContext=this;
function dj_undef(_1,_2){
return (typeof (_2||dj_currentContext)[_1]=="undefined");
}
if(dj_undef("djConfig",this)){
var djConfig={};
}
if(dj_undef("dojo",this)){
var dojo={};
}
dojo.global=function(){
return dj_currentContext;
};
dojo.locale=djConfig.locale;
dojo.version={major:0,minor:0,patch:0,flag:"dev",revision:Number("$Rev: 5779 $".match(/[0-9]+/)[0]),toString:function(){
with(dojo.version){
return major+"."+minor+"."+patch+flag+" ("+revision+")";
}
}};
dojo.evalProp=function(_3,_4,_5){
if((!_4)||(!_3)){
return undefined;
}
if(!dj_undef(_3,_4)){
return _4[_3];
}
return (_5?(_4[_3]={}):undefined);
};
dojo.parseObjPath=function(_6,_7,_8){
var _9=(_7||dojo.global());
var _a=_6.split(".");
var _b=_a.pop();
for(var i=0,l=_a.length;i<l&&_9;i++){
_9=dojo.evalProp(_a[i],_9,_8);
}
return {obj:_9,prop:_b};
};
dojo.evalObjPath=function(_e,_f){
if(typeof _e!="string"){
return dojo.global();
}
if(_e.indexOf(".")==-1){
return dojo.evalProp(_e,dojo.global(),_f);
}
var ref=dojo.parseObjPath(_e,dojo.global(),_f);
if(ref){
return dojo.evalProp(ref.prop,ref.obj,_f);
}
return null;
};
dojo.errorToString=function(_11){
if(!dj_undef("message",_11)){
return _11.message;
}else{
if(!dj_undef("description",_11)){
return _11.description;
}else{
return _11;
}
}
};
dojo.raise=function(_12,_13){
if(_13){
_12=_12+": "+dojo.errorToString(_13);
}
try{
if(djConfig.isDebug){
dojo.hostenv.println("FATAL exception raised: "+_12);
}
}
catch(e){
}
throw _13||Error(_12);
};
dojo.debug=function(){
};
dojo.debugShallow=function(obj){
};
dojo.profile={start:function(){
},end:function(){
},stop:function(){
},dump:function(){
}};
function dj_eval(_15){
return dj_global.eval?dj_global.eval(_15):eval(_15);
}
dojo.unimplemented=function(_16,_17){
var _18="'"+_16+"' not implemented";
if(_17!=null){
_18+=" "+_17;
}
dojo.raise(_18);
};
dojo.deprecated=function(_19,_1a,_1b){
var _1c="DEPRECATED: "+_19;
if(_1a){
_1c+=" "+_1a;
}
if(_1b){
_1c+=" -- will be removed in version: "+_1b;
}
dojo.debug(_1c);
};
dojo.render=(function(){
function vscaffold(_1d,_1e){
var tmp={capable:false,support:{builtin:false,plugin:false},prefixes:_1d};
for(var i=0;i<_1e.length;i++){
tmp[_1e[i]]=false;
}
return tmp;
}
return {name:"",ver:dojo.version,os:{win:false,linux:false,osx:false},html:vscaffold(["html"],["ie","opera","khtml","safari","moz"]),svg:vscaffold(["svg"],["corel","adobe","batik"]),vml:vscaffold(["vml"],["ie"]),swf:vscaffold(["Swf","Flash","Mm"],["mm"]),swt:vscaffold(["Swt"],["ibm"])};
})();
dojo.hostenv=(function(){
var _21={isDebug:false,allowQueryConfig:false,baseScriptUri:"",baseRelativePath:"",libraryScriptUri:"",iePreventClobber:false,ieClobberMinimal:true,preventBackButtonFix:true,searchIds:[],parseWidgets:true};
if(typeof djConfig=="undefined"){
djConfig=_21;
}else{
for(var _22 in _21){
if(typeof djConfig[_22]=="undefined"){
djConfig[_22]=_21[_22];
}
}
}
return {name_:"(unset)",version_:"(unset)",getName:function(){
return this.name_;
},getVersion:function(){
return this.version_;
},getText:function(uri){
dojo.unimplemented("getText","uri="+uri);
}};
})();
dojo.hostenv.getBaseScriptUri=function(){
if(djConfig.baseScriptUri.length){
return djConfig.baseScriptUri;
}
var uri=new String(djConfig.libraryScriptUri||djConfig.baseRelativePath);
if(!uri){
dojo.raise("Nothing returned by getLibraryScriptUri(): "+uri);
}
var _25=uri.lastIndexOf("/");
djConfig.baseScriptUri=djConfig.baseRelativePath;
return djConfig.baseScriptUri;
};
(function(){
var _26={pkgFileName:"__package__",loading_modules_:{},loaded_modules_:{},addedToLoadingCount:[],removedFromLoadingCount:[],inFlightCount:0,modulePrefixes_:{dojo:{name:"dojo",value:"src"}},setModulePrefix:function(_27,_28){
this.modulePrefixes_[_27]={name:_27,value:_28};
},moduleHasPrefix:function(_29){
var mp=this.modulePrefixes_;
return Boolean(mp[_29]&&mp[_29].value);
},getModulePrefix:function(_2b){
if(this.moduleHasPrefix(_2b)){
return this.modulePrefixes_[_2b].value;
}
return _2b;
},getTextStack:[],loadUriStack:[],loadedUris:[],post_load_:false,modulesLoadedListeners:[],unloadListeners:[],loadNotifying:false};
for(var _2c in _26){
dojo.hostenv[_2c]=_26[_2c];
}
})();
dojo.hostenv.loadPath=function(_2d,_2e,cb){
var uri;
if(_2d.charAt(0)=="/"||_2d.match(/^\w+:/)){
uri=_2d;
}else{
uri=this.getBaseScriptUri()+_2d;
}
if(djConfig.cacheBust&&dojo.render.html.capable){
uri+="?"+String(djConfig.cacheBust).replace(/\W+/g,"");
}
try{
return !_2e?this.loadUri(uri,cb):this.loadUriAndCheck(uri,_2e,cb);
}
catch(e){
dojo.debug(e);
return false;
}
};
dojo.hostenv.loadUri=function(uri,cb){
if(this.loadedUris[uri]){
return true;
}
var _33=this.getText(uri,null,true);
if(!_33){
return false;
}
this.loadedUris[uri]=true;
if(cb){
_33="("+_33+")";
}
var _34=dj_eval(_33);
if(cb){
cb(_34);
}
return true;
};
dojo.hostenv.loadUriAndCheck=function(uri,_36,cb){
var ok=true;
try{
ok=this.loadUri(uri,cb);
}
catch(e){
dojo.debug("failed loading ",uri," with error: ",e);
}
return Boolean(ok&&this.findModule(_36,false));
};
dojo.loaded=function(){
};
dojo.unloaded=function(){
};
dojo.hostenv.loaded=function(){
this.loadNotifying=true;
this.post_load_=true;
var mll=this.modulesLoadedListeners;
for(var x=0;x<mll.length;x++){
mll[x]();
}
this.modulesLoadedListeners=[];
this.loadNotifying=false;
dojo.loaded();
};
dojo.hostenv.unloaded=function(){
var mll=this.unloadListeners;
while(mll.length){
(mll.pop())();
}
dojo.unloaded();
};
dojo.addOnLoad=function(obj,_3d){
var dh=dojo.hostenv;
if(arguments.length==1){
dh.modulesLoadedListeners.push(obj);
}else{
if(arguments.length>1){
dh.modulesLoadedListeners.push(function(){
obj[_3d]();
});
}
}
if(dh.post_load_&&dh.inFlightCount==0&&!dh.loadNotifying){
dh.callLoaded();
}
};
dojo.addOnUnload=function(obj,_40){
var dh=dojo.hostenv;
if(arguments.length==1){
dh.unloadListeners.push(obj);
}else{
if(arguments.length>1){
dh.unloadListeners.push(function(){
obj[_40]();
});
}
}
};
dojo.hostenv.modulesLoaded=function(){
if(this.post_load_){
return;
}
if(this.loadUriStack.length==0&&this.getTextStack.length==0){
if(this.inFlightCount>0){
dojo.debug("files still in flight!");
return;
}
dojo.hostenv.callLoaded();
}
};
dojo.hostenv.callLoaded=function(){
if(typeof setTimeout=="object"){
setTimeout("dojo.hostenv.loaded();",0);
}else{
dojo.hostenv.loaded();
}
};
dojo.hostenv.getModuleSymbols=function(_42){
var _43=_42.split(".");
for(var i=_43.length;i>0;i--){
var _45=_43.slice(0,i).join(".");
if((i==1)&&!this.moduleHasPrefix(_45)){
_43[0]="../"+_43[0];
}else{
var _46=this.getModulePrefix(_45);
if(_46!=_45){
_43.splice(0,i,_46);
break;
}
}
}
return _43;
};
dojo.hostenv._global_omit_module_check=false;
dojo.hostenv.loadModule=function(_47,_48,_49){
if(!_47){
return;
}
_49=this._global_omit_module_check||_49;
var _4a=this.findModule(_47,false);
if(_4a){
return _4a;
}
if(dj_undef(_47,this.loading_modules_)){
this.addedToLoadingCount.push(_47);
}
this.loading_modules_[_47]=1;
var _4b=_47.replace(/\./g,"/")+".js";
var _4c=_47.split(".");
var _4d=this.getModuleSymbols(_47);
var _4e=((_4d[0].charAt(0)!="/")&&!_4d[0].match(/^\w+:/));
var _4f=_4d[_4d.length-1];
var ok;
if(_4f=="*"){
_47=_4c.slice(0,-1).join(".");
while(_4d.length){
_4d.pop();
_4d.push(this.pkgFileName);
_4b=_4d.join("/")+".js";
if(_4e&&_4b.charAt(0)=="/"){
_4b=_4b.slice(1);
}
ok=this.loadPath(_4b,!_49?_47:null);
if(ok){
break;
}
_4d.pop();
}
}else{
_4b=_4d.join("/")+".js";
_47=_4c.join(".");
var _51=!_49?_47:null;
ok=this.loadPath(_4b,_51);
if(!ok&&!_48){
_4d.pop();
while(_4d.length){
_4b=_4d.join("/")+".js";
ok=this.loadPath(_4b,_51);
if(ok){
break;
}
_4d.pop();
_4b=_4d.join("/")+"/"+this.pkgFileName+".js";
if(_4e&&_4b.charAt(0)=="/"){
_4b=_4b.slice(1);
}
ok=this.loadPath(_4b,_51);
if(ok){
break;
}
}
}
if(!ok&&!_49){
dojo.raise("Could not load '"+_47+"'; last tried '"+_4b+"'");
}
}
if(!_49&&!this["isXDomain"]){
_4a=this.findModule(_47,false);
if(!_4a){
dojo.raise("symbol '"+_47+"' is not defined after loading '"+_4b+"'");
}
}
return _4a;
};
dojo.hostenv.startPackage=function(_52){
var _53=String(_52);
var _54=_53;
var _55=_52.split(/\./);
if(_55[_55.length-1]=="*"){
_55.pop();
_54=_55.join(".");
}
var _56=dojo.evalObjPath(_54,true);
this.loaded_modules_[_53]=_56;
this.loaded_modules_[_54]=_56;
return _56;
};
dojo.hostenv.findModule=function(_57,_58){
var lmn=String(_57);
if(this.loaded_modules_[lmn]){
return this.loaded_modules_[lmn];
}
if(_58){
dojo.raise("no loaded module named '"+_57+"'");
}
return null;
};
dojo.kwCompoundRequire=function(_5a){
var _5b=_5a["common"]||[];
var _5c=_5a[dojo.hostenv.name_]?_5b.concat(_5a[dojo.hostenv.name_]||[]):_5b.concat(_5a["default"]||[]);
for(var x=0;x<_5c.length;x++){
var _5e=_5c[x];
if(_5e.constructor==Array){
dojo.hostenv.loadModule.apply(dojo.hostenv,_5e);
}else{
dojo.hostenv.loadModule(_5e);
}
}
};
dojo.require=function(){
dojo.hostenv.loadModule.apply(dojo.hostenv,arguments);
};
dojo.requireIf=function(){
var _5f=arguments[0];
if((_5f===true)||(_5f=="common")||(_5f&&dojo.render[_5f].capable)){
var _60=[];
for(var i=1;i<arguments.length;i++){
_60.push(arguments[i]);
}
dojo.require.apply(dojo,_60);
}
};
dojo.requireAfterIf=dojo.requireIf;
dojo.provide=function(){
return dojo.hostenv.startPackage.apply(dojo.hostenv,arguments);
};
dojo.registerModulePath=function(_62,_63){
return dojo.hostenv.setModulePrefix(_62,_63);
};
dojo.setModulePrefix=function(_64,_65){
dojo.deprecated("dojo.setModulePrefix(\""+_64+"\", \""+_65+"\")","replaced by dojo.registerModulePath","0.5");
return dojo.registerModulePath(_64,_65);
};
dojo.exists=function(obj,_67){
var p=_67.split(".");
for(var i=0;i<p.length;i++){
if(!obj[p[i]]){
return false;
}
obj=obj[p[i]];
}
return true;
};
dojo.hostenv.normalizeLocale=function(_6a){
return _6a?_6a.toLowerCase():dojo.locale;
};
dojo.hostenv.searchLocalePath=function(_6b,_6c,_6d){
_6b=dojo.hostenv.normalizeLocale(_6b);
var _6e=_6b.split("-");
var _6f=[];
for(var i=_6e.length;i>0;i--){
_6f.push(_6e.slice(0,i).join("-"));
}
_6f.push(false);
if(_6c){
_6f.reverse();
}
for(var j=_6f.length-1;j>=0;j--){
var loc=_6f[j]||"ROOT";
var _73=_6d(loc);
if(_73){
break;
}
}
};
dojo.hostenv.preloadLocalizations=function(){
var _74;
if(_74){
dojo.registerModulePath("nls","nls");
function preload(_75){
_75=dojo.hostenv.normalizeLocale(_75);
dojo.hostenv.searchLocalePath(_75,true,function(loc){
for(var i=0;i<_74.length;i++){
if(_74[i]==loc){
dojo["require"]("nls.dojo_"+loc);
return true;
}
}
return false;
});
}
preload();
var _78=djConfig.extraLocale||[];
for(var i=0;i<_78.length;i++){
preload(_78[i]);
}
}
dojo.hostenv.preloadLocalizations=function(){
};
};
dojo.requireLocalization=function(_7a,_7b,_7c){
dojo.hostenv.preloadLocalizations();
var _7d=[_7a,"nls",_7b].join(".");
var _7e=dojo.hostenv.findModule(_7d);
if(_7e){
if(djConfig.localizationComplete&&_7e._built){
return;
}
var _7f=dojo.hostenv.normalizeLocale(_7c).replace("-","_");
var _80=_7d+"."+_7f;
if(dojo.hostenv.findModule(_80)){
return;
}
}
_7e=dojo.hostenv.startPackage(_7d);
var _81=dojo.hostenv.getModuleSymbols(_7a);
var _82=_81.concat("nls").join("/");
var _83;
dojo.hostenv.searchLocalePath(_7c,false,function(loc){
var _85=loc.replace("-","_");
var _86=_7d+"."+_85;
var _87=false;
if(!dojo.hostenv.findModule(_86)){
dojo.hostenv.startPackage(_86);
var _88=[_82];
if(loc!="ROOT"){
_88.push(loc);
}
_88.push(_7b);
var _89=_88.join("/")+".js";
_87=dojo.hostenv.loadPath(_89,null,function(_8a){
var _8b=function(){
};
_8b.prototype=_83;
_7e[_85]=new _8b();
for(var j in _8a){
_7e[_85][j]=_8a[j];
}
});
}else{
_87=true;
}
if(_87&&_7e[_85]){
_83=_7e[_85];
}else{
_7e[_85]=_83;
}
});
};
(function(){
var _8d=djConfig.extraLocale;
if(_8d){
if(!_8d instanceof Array){
_8d=[_8d];
}
var req=dojo.requireLocalization;
dojo.requireLocalization=function(m,b,_91){
req(m,b,_91);
if(_91){
return;
}
for(var i=0;i<_8d.length;i++){
req(m,b,_8d[i]);
}
};
}
})();
}
if(typeof window!="undefined"){
(function(){
if(djConfig.allowQueryConfig){
var _93=document.location.toString();
var _94=_93.split("?",2);
if(_94.length>1){
var _95=_94[1];
var _96=_95.split("&");
for(var x in _96){
var sp=_96[x].split("=");
if((sp[0].length>9)&&(sp[0].substr(0,9)=="djConfig.")){
var opt=sp[0].substr(9);
try{
djConfig[opt]=eval(sp[1]);
}
catch(e){
djConfig[opt]=sp[1];
}
}
}
}
}
if(((djConfig["baseScriptUri"]=="")||(djConfig["baseRelativePath"]==""))&&(document&&document.getElementsByTagName)){
var _9a=document.getElementsByTagName("script");
var _9b=/(__package__|dojo|bootstrap1)\.js([\?\.]|$)/i;
for(var i=0;i<_9a.length;i++){
var src=_9a[i].getAttribute("src");
if(!src){
continue;
}
var m=src.match(_9b);
if(m){
var _9f=src.substring(0,m.index);
if(src.indexOf("bootstrap1")>-1){
_9f+="../";
}
if(!this["djConfig"]){
djConfig={};
}
if(djConfig["baseScriptUri"]==""){
djConfig["baseScriptUri"]=_9f;
}
if(djConfig["baseRelativePath"]==""){
djConfig["baseRelativePath"]=_9f;
}
break;
}
}
}
var dr=dojo.render;
var drh=dojo.render.html;
var drs=dojo.render.svg;
var dua=(drh.UA=navigator.userAgent);
var dav=(drh.AV=navigator.appVersion);
var t=true;
var f=false;
drh.capable=t;
drh.support.builtin=t;
dr.ver=parseFloat(drh.AV);
dr.os.mac=dav.indexOf("Macintosh")>=0;
dr.os.win=dav.indexOf("Windows")>=0;
dr.os.linux=dav.indexOf("X11")>=0;
drh.opera=dua.indexOf("Opera")>=0;
drh.khtml=(dav.indexOf("Konqueror")>=0)||(dav.indexOf("Safari")>=0);
drh.safari=dav.indexOf("Safari")>=0;
var _a7=dua.indexOf("Gecko");
drh.mozilla=drh.moz=(_a7>=0)&&(!drh.khtml);
if(drh.mozilla){
drh.geckoVersion=dua.substring(_a7+6,_a7+14);
}
drh.ie=(document.all)&&(!drh.opera);
drh.ie50=drh.ie&&dav.indexOf("MSIE 5.0")>=0;
drh.ie55=drh.ie&&dav.indexOf("MSIE 5.5")>=0;
drh.ie60=drh.ie&&dav.indexOf("MSIE 6.0")>=0;
drh.ie70=drh.ie&&dav.indexOf("MSIE 7.0")>=0;
var cm=document["compatMode"];
drh.quirks=(cm=="BackCompat")||(cm=="QuirksMode")||drh.ie55||drh.ie50;
dojo.locale=dojo.locale||(drh.ie?navigator.userLanguage:navigator.language).toLowerCase();
dr.vml.capable=drh.ie;
drs.capable=f;
drs.support.plugin=f;
drs.support.builtin=f;
var _a9=window["document"];
var tdi=_a9["implementation"];
if((tdi)&&(tdi["hasFeature"])&&(tdi.hasFeature("org.w3c.dom.svg","1.0"))){
drs.capable=t;
drs.support.builtin=t;
drs.support.plugin=f;
}
if(drh.safari){
var tmp=dua.split("AppleWebKit/")[1];
var ver=parseFloat(tmp.split(" ")[0]);
if(ver>=420){
drs.capable=t;
drs.support.builtin=t;
drs.support.plugin=f;
}
}
})();
dojo.hostenv.startPackage("dojo.hostenv");
dojo.render.name=dojo.hostenv.name_="browser";
dojo.hostenv.searchIds=[];
dojo.hostenv._XMLHTTP_PROGIDS=["Msxml2.XMLHTTP","Microsoft.XMLHTTP","Msxml2.XMLHTTP.4.0"];
dojo.hostenv.getXmlhttpObject=function(){
var _ad=null;
var _ae=null;
try{
_ad=new XMLHttpRequest();
}
catch(e){
}
if(!_ad){
for(var i=0;i<3;++i){
var _b0=dojo.hostenv._XMLHTTP_PROGIDS[i];
try{
_ad=new ActiveXObject(_b0);
}
catch(e){
_ae=e;
}
if(_ad){
dojo.hostenv._XMLHTTP_PROGIDS=[_b0];
break;
}
}
}
if(!_ad){
return dojo.raise("XMLHTTP not available",_ae);
}
return _ad;
};
dojo.hostenv._blockAsync=false;
dojo.hostenv.getText=function(uri,_b2,_b3){
if(!_b2){
this._blockAsync=true;
}
var _b4=this.getXmlhttpObject();
function isDocumentOk(_b5){
var _b6=_b5["status"];
return Boolean((!_b6)||((200<=_b6)&&(300>_b6))||(_b6==304));
}
if(_b2){
var _b7=this,_b8=null,gbl=dojo.global();
var xhr=dojo.evalObjPath("dojo.io.XMLHTTPTransport");
_b4.onreadystatechange=function(){
if(_b8){
gbl.clearTimeout(_b8);
_b8=null;
}
if(_b7._blockAsync||(xhr&&xhr._blockAsync)){
_b8=gbl.setTimeout(function(){
_b4.onreadystatechange.apply(this);
},10);
}else{
if(4==_b4.readyState){
if(isDocumentOk(_b4)){
_b2(_b4.responseText);
}
}
}
};
}
_b4.open("GET",uri,_b2?true:false);
try{
_b4.send(null);
if(_b2){
return null;
}
if(!isDocumentOk(_b4)){
var err=Error("Unable to load "+uri+" status:"+_b4.status);
err.status=_b4.status;
err.responseText=_b4.responseText;
throw err;
}
}
catch(e){
this._blockAsync=false;
if((_b3)&&(!_b2)){
return null;
}else{
throw e;
}
}
this._blockAsync=false;
return _b4.responseText;
};
dojo.hostenv.defaultDebugContainerId="dojoDebug";
dojo.hostenv._println_buffer=[];
dojo.hostenv._println_safe=false;
dojo.hostenv.println=function(_bc){
if(!dojo.hostenv._println_safe){
dojo.hostenv._println_buffer.push(_bc);
}else{
try{
var _bd=document.getElementById(djConfig.debugContainerId?djConfig.debugContainerId:dojo.hostenv.defaultDebugContainerId);
if(!_bd){
_bd=dojo.body();
}
var div=document.createElement("div");
div.appendChild(document.createTextNode(_bc));
_bd.appendChild(div);
}
catch(e){
try{
document.write("<div>"+_bc+"</div>");
}
catch(e2){
window.status=_bc;
}
}
}
};
dojo.addOnLoad(function(){
dojo.hostenv._println_safe=true;
while(dojo.hostenv._println_buffer.length>0){
dojo.hostenv.println(dojo.hostenv._println_buffer.shift());
}
});
function dj_addNodeEvtHdlr(_bf,_c0,fp,_c2){
var _c3=_bf["on"+_c0]||function(){
};
_bf["on"+_c0]=function(){
fp.apply(_bf,arguments);
_c3.apply(_bf,arguments);
};
return true;
}
function dj_load_init(e){
var _c5=(e&&e.type)?e.type.toLowerCase():"load";
if(arguments.callee.initialized||(_c5!="domcontentloaded"&&_c5!="load")){
return;
}
arguments.callee.initialized=true;
if(typeof (_timer)!="undefined"){
clearInterval(_timer);
delete _timer;
}
var _c6=function(){
if(dojo.render.html.ie){
dojo.hostenv.makeWidgets();
}
};
if(dojo.hostenv.inFlightCount==0){
_c6();
dojo.hostenv.modulesLoaded();
}else{
dojo.addOnLoad(_c6);
}
}
if(document.addEventListener){
document.addEventListener("DOMContentLoaded",dj_load_init,null);
document.addEventListener("load",dj_load_init,null);
}
if(dojo.render.html.ie&&dojo.render.os.win){
document.attachEvent("onreadystatechange",function(e){
if(document.readyState=="complete"){
dj_load_init();
}
});
}
if(/(WebKit|khtml)/i.test(navigator.userAgent)){
var _timer=setInterval(function(){
if(/loaded|complete/.test(document.readyState)){
dj_load_init();
}
},10);
}
dj_addNodeEvtHdlr(window,"unload",function(){
dojo.hostenv.unloaded();
});
dojo.hostenv.makeWidgets=function(){
var _c8=[];
if(djConfig.searchIds&&djConfig.searchIds.length>0){
_c8=_c8.concat(djConfig.searchIds);
}
if(dojo.hostenv.searchIds&&dojo.hostenv.searchIds.length>0){
_c8=_c8.concat(dojo.hostenv.searchIds);
}
if((djConfig.parseWidgets)||(_c8.length>0)){
if(dojo.evalObjPath("dojo.widget.Parse")){
var _c9=new dojo.xml.Parse();
if(_c8.length>0){
for(var x=0;x<_c8.length;x++){
var _cb=document.getElementById(_c8[x]);
if(!_cb){
continue;
}
var _cc=_c9.parseElement(_cb,null,true);
dojo.widget.getParser().createComponents(_cc);
}
}else{
if(djConfig.parseWidgets){
var _cc=_c9.parseElement(dojo.body(),null,true);
dojo.widget.getParser().createComponents(_cc);
}
}
}
}
};
dojo.addOnLoad(function(){
if(!dojo.render.html.ie){
dojo.hostenv.makeWidgets();
}
});
try{
if(dojo.render.html.ie){
document.namespaces.add("v","urn:schemas-microsoft-com:vml");
document.createStyleSheet().addRule("v\\:*","behavior:url(#default#VML)");
}
}
catch(e){
}
dojo.hostenv.writeIncludes=function(){
};
if(!dj_undef("document",this)){
dj_currentDocument=this.document;
}
dojo.doc=function(){
return dj_currentDocument;
};
dojo.body=function(){
return dojo.doc().body||dojo.doc().getElementsByTagName("body")[0];
};
dojo.byId=function(id,doc){
if((id)&&((typeof id=="string")||(id instanceof String))){
if(!doc){
doc=dj_currentDocument;
}
var ele=doc.getElementById(id);
if(ele&&(ele.id!=id)&&doc.all){
ele=null;
eles=doc.all[id];
if(eles){
if(eles.length){
for(var i=0;i<eles.length;i++){
if(eles[i].id==id){
ele=eles[i];
break;
}
}
}else{
ele=eles;
}
}
}
return ele;
}
return id;
};
dojo.setContext=function(_d1,_d2){
dj_currentContext=_d1;
dj_currentDocument=_d2;
};
dojo._fireCallback=function(_d3,_d4,_d5){
if((_d4)&&((typeof _d3=="string")||(_d3 instanceof String))){
_d3=_d4[_d3];
}
return (_d4?_d3.apply(_d4,_d5||[]):_d3());
};
dojo.withGlobal=function(_d6,_d7,_d8,_d9){
var _da;
var _db=dj_currentContext;
var _dc=dj_currentDocument;
try{
dojo.setContext(_d6,_d6.document);
_da=dojo._fireCallback(_d7,_d8,_d9);
}
finally{
dojo.setContext(_db,_dc);
}
return _da;
};
dojo.withDoc=function(_dd,_de,_df,_e0){
var _e1;
var _e2=dj_currentDocument;
try{
dj_currentDocument=_dd;
_e1=dojo._fireCallback(_de,_df,_e0);
}
finally{
dj_currentDocument=_e2;
}
return _e1;
};
}
(function(){
if(typeof dj_usingBootstrap!="undefined"){
return;
}
var _e3=false;
var _e4=false;
var _e5=false;
if((typeof this["load"]=="function")&&((typeof this["Packages"]=="function")||(typeof this["Packages"]=="object"))){
_e3=true;
}else{
if(typeof this["load"]=="function"){
_e4=true;
}else{
if(window.widget){
_e5=true;
}
}
}
var _e6=[];
if((this["djConfig"])&&((djConfig["isDebug"])||(djConfig["debugAtAllCosts"]))){
_e6.push("debug.js");
}
if((this["djConfig"])&&(djConfig["debugAtAllCosts"])&&(!_e3)&&(!_e5)){
_e6.push("browser_debug.js");
}
var _e7=djConfig["baseScriptUri"];
if((this["djConfig"])&&(djConfig["baseLoaderUri"])){
_e7=djConfig["baseLoaderUri"];
}
for(var x=0;x<_e6.length;x++){
var _e9=_e7+"src/"+_e6[x];
if(_e3||_e4){
load(_e9);
}else{
try{
document.write("<scr"+"ipt type='text/javascript' src='"+_e9+"'></scr"+"ipt>");
}
catch(e){
var _ea=document.createElement("script");
_ea.src=_e9;
document.getElementsByTagName("head")[0].appendChild(_ea);
}
}
}
})();
dojo.provide("dojo.string.common");
dojo.string.trim=function(str,wh){
if(!str.replace){
return str;
}
if(!str.length){
return str;
}
var re=(wh>0)?(/^\s+/):(wh<0)?(/\s+$/):(/^\s+|\s+$/g);
return str.replace(re,"");
};
dojo.string.trimStart=function(str){
return dojo.string.trim(str,1);
};
dojo.string.trimEnd=function(str){
return dojo.string.trim(str,-1);
};
dojo.string.repeat=function(str,_f1,_f2){
var out="";
for(var i=0;i<_f1;i++){
out+=str;
if(_f2&&i<_f1-1){
out+=_f2;
}
}
return out;
};
dojo.string.pad=function(str,len,c,dir){
var out=String(str);
if(!c){
c="0";
}
if(!dir){
dir=1;
}
while(out.length<len){
if(dir>0){
out=c+out;
}else{
out+=c;
}
}
return out;
};
dojo.string.padLeft=function(str,len,c){
return dojo.string.pad(str,len,c,1);
};
dojo.string.padRight=function(str,len,c){
return dojo.string.pad(str,len,c,-1);
};
dojo.provide("dojo.string");
dojo.provide("dojo.lang.common");
dojo.lang.inherits=function(_100,_101){
if(typeof _101!="function"){
dojo.raise("dojo.inherits: superclass argument ["+_101+"] must be a function (subclass: ["+_100+"']");
}
_100.prototype=new _101();
_100.prototype.constructor=_100;
_100.superclass=_101.prototype;
_100["super"]=_101.prototype;
};
dojo.lang._mixin=function(obj,_103){
var tobj={};
for(var x in _103){
if((typeof tobj[x]=="undefined")||(tobj[x]!=_103[x])){
obj[x]=_103[x];
}
}
if(dojo.render.html.ie&&(typeof (_103["toString"])=="function")&&(_103["toString"]!=obj["toString"])&&(_103["toString"]!=tobj["toString"])){
obj.toString=_103.toString;
}
return obj;
};
dojo.lang.mixin=function(obj,_107){
for(var i=1,l=arguments.length;i<l;i++){
dojo.lang._mixin(obj,arguments[i]);
}
return obj;
};
dojo.lang.extend=function(_10a,_10b){
for(var i=1,l=arguments.length;i<l;i++){
dojo.lang._mixin(_10a.prototype,arguments[i]);
}
return _10a;
};
dojo.inherits=dojo.lang.inherits;
dojo.mixin=dojo.lang.mixin;
dojo.extend=dojo.lang.extend;
dojo.lang.find=function(_10e,_10f,_110,_111){
if(!dojo.lang.isArrayLike(_10e)&&dojo.lang.isArrayLike(_10f)){
dojo.deprecated("dojo.lang.find(value, array)","use dojo.lang.find(array, value) instead","0.5");
var temp=_10e;
_10e=_10f;
_10f=temp;
}
var _113=dojo.lang.isString(_10e);
if(_113){
_10e=_10e.split("");
}
if(_111){
var step=-1;
var i=_10e.length-1;
var end=-1;
}else{
var step=1;
var i=0;
var end=_10e.length;
}
if(_110){
while(i!=end){
if(_10e[i]===_10f){
return i;
}
i+=step;
}
}else{
while(i!=end){
if(_10e[i]==_10f){
return i;
}
i+=step;
}
}
return -1;
};
dojo.lang.indexOf=dojo.lang.find;
dojo.lang.findLast=function(_117,_118,_119){
return dojo.lang.find(_117,_118,_119,true);
};
dojo.lang.lastIndexOf=dojo.lang.findLast;
dojo.lang.inArray=function(_11a,_11b){
return dojo.lang.find(_11a,_11b)>-1;
};
dojo.lang.isObject=function(it){
if(typeof it=="undefined"){
return false;
}
return (typeof it=="object"||it===null||dojo.lang.isArray(it)||dojo.lang.isFunction(it));
};
dojo.lang.isArray=function(it){
return (it&&it instanceof Array||typeof it=="array");
};
dojo.lang.isArrayLike=function(it){
if((!it)||(dojo.lang.isUndefined(it))){
return false;
}
if(dojo.lang.isString(it)){
return false;
}
if(dojo.lang.isFunction(it)){
return false;
}
if(dojo.lang.isArray(it)){
return true;
}
if((it.tagName)&&(it.tagName.toLowerCase()=="form")){
return false;
}
if(dojo.lang.isNumber(it.length)&&isFinite(it.length)){
return true;
}
return false;
};
dojo.lang.isFunction=function(it){
if(!it){
return false;
}
if((typeof (it)=="function")&&(it=="[object NodeList]")){
return false;
}
return (it instanceof Function||typeof it=="function");
};
dojo.lang.isString=function(it){
return (typeof it=="string"||it instanceof String);
};
dojo.lang.isAlien=function(it){
if(!it){
return false;
}
return !dojo.lang.isFunction()&&/\{\s*\[native code\]\s*\}/.test(String(it));
};
dojo.lang.isBoolean=function(it){
return (it instanceof Boolean||typeof it=="boolean");
};
dojo.lang.isNumber=function(it){
return (it instanceof Number||typeof it=="number");
};
dojo.lang.isUndefined=function(it){
return ((typeof (it)=="undefined")&&(it==undefined));
};
dojo.provide("dojo.lang.extras");
dojo.lang.setTimeout=function(func,_126){
var _127=window,_128=2;
if(!dojo.lang.isFunction(func)){
_127=func;
func=_126;
_126=arguments[2];
_128++;
}
if(dojo.lang.isString(func)){
func=_127[func];
}
var args=[];
for(var i=_128;i<arguments.length;i++){
args.push(arguments[i]);
}
return dojo.global().setTimeout(function(){
func.apply(_127,args);
},_126);
};
dojo.lang.clearTimeout=function(_12b){
dojo.global().clearTimeout(_12b);
};
dojo.lang.getNameInObj=function(ns,item){
if(!ns){
ns=dj_global;
}
for(var x in ns){
if(ns[x]===item){
return new String(x);
}
}
return null;
};
dojo.lang.shallowCopy=function(obj,deep){
var i,ret;
if(obj===null){
return null;
}
if(dojo.lang.isObject(obj)){
ret=new obj.constructor();
for(i in obj){
if(dojo.lang.isUndefined(ret[i])){
ret[i]=deep?dojo.lang.shallowCopy(obj[i],deep):obj[i];
}
}
}else{
if(dojo.lang.isArray(obj)){
ret=[];
for(i=0;i<obj.length;i++){
ret[i]=deep?dojo.lang.shallowCopy(obj[i],deep):obj[i];
}
}else{
ret=obj;
}
}
return ret;
};
dojo.lang.firstValued=function(){
for(var i=0;i<arguments.length;i++){
if(typeof arguments[i]!="undefined"){
return arguments[i];
}
}
return undefined;
};
dojo.lang.getObjPathValue=function(_134,_135,_136){
with(dojo.parseObjPath(_134,_135,_136)){
return dojo.evalProp(prop,obj,_136);
}
};
dojo.lang.setObjPathValue=function(_137,_138,_139,_13a){
if(arguments.length<4){
_13a=true;
}
with(dojo.parseObjPath(_137,_139,_13a)){
if(obj&&(_13a||(prop in obj))){
obj[prop]=_138;
}
}
};
dojo.provide("dojo.io.common");
dojo.io.transports=[];
dojo.io.hdlrFuncNames=["load","error","timeout"];
dojo.io.Request=function(url,_13c,_13d,_13e){
if((arguments.length==1)&&(arguments[0].constructor==Object)){
this.fromKwArgs(arguments[0]);
}else{
this.url=url;
if(_13c){
this.mimetype=_13c;
}
if(_13d){
this.transport=_13d;
}
if(arguments.length>=4){
this.changeUrl=_13e;
}
}
};
dojo.lang.extend(dojo.io.Request,{url:"",mimetype:"text/plain",method:"GET",content:undefined,transport:undefined,changeUrl:undefined,formNode:undefined,sync:false,bindSuccess:false,useCache:false,preventCache:false,load:function(type,data,evt){
},error:function(type,_143){
},timeout:function(type){
},handle:function(){
},timeoutSeconds:0,abort:function(){
},fromKwArgs:function(_145){
if(_145["url"]){
_145.url=_145.url.toString();
}
if(_145["formNode"]){
_145.formNode=dojo.byId(_145.formNode);
}
if(!_145["method"]&&_145["formNode"]&&_145["formNode"].method){
_145.method=_145["formNode"].method;
}
if(!_145["handle"]&&_145["handler"]){
_145.handle=_145.handler;
}
if(!_145["load"]&&_145["loaded"]){
_145.load=_145.loaded;
}
if(!_145["changeUrl"]&&_145["changeURL"]){
_145.changeUrl=_145.changeURL;
}
_145.encoding=dojo.lang.firstValued(_145["encoding"],djConfig["bindEncoding"],"");
_145.sendTransport=dojo.lang.firstValued(_145["sendTransport"],djConfig["ioSendTransport"],false);
var _146=dojo.lang.isFunction;
for(var x=0;x<dojo.io.hdlrFuncNames.length;x++){
var fn=dojo.io.hdlrFuncNames[x];
if(_145[fn]&&_146(_145[fn])){
continue;
}
if(_145["handle"]&&_146(_145["handle"])){
_145[fn]=_145.handle;
}
}
dojo.lang.mixin(this,_145);
}});
dojo.io.Error=function(msg,type,num){
this.message=msg;
this.type=type||"unknown";
this.number=num||0;
};
dojo.io.transports.addTransport=function(name){
this.push(name);
this[name]=dojo.io[name];
};
dojo.io.bind=function(_14d){
if(!(_14d instanceof dojo.io.Request)){
try{
_14d=new dojo.io.Request(_14d);
}
catch(e){
dojo.debug(e);
}
}
var _14e="";
if(_14d["transport"]){
_14e=_14d["transport"];
if(!this[_14e]){
dojo.io.sendBindError(_14d,"No dojo.io.bind() transport with name '"+_14d["transport"]+"'.");
return _14d;
}
if(!this[_14e].canHandle(_14d)){
dojo.io.sendBindError(_14d,"dojo.io.bind() transport with name '"+_14d["transport"]+"' cannot handle this type of request.");
return _14d;
}
}else{
for(var x=0;x<dojo.io.transports.length;x++){
var tmp=dojo.io.transports[x];
if((this[tmp])&&(this[tmp].canHandle(_14d))){
_14e=tmp;
}
}
if(_14e==""){
dojo.io.sendBindError(_14d,"None of the loaded transports for dojo.io.bind()"+" can handle the request.");
return _14d;
}
}
this[_14e].bind(_14d);
_14d.bindSuccess=true;
return _14d;
};
dojo.io.sendBindError=function(_151,_152){
if((typeof _151.error=="function"||typeof _151.handle=="function")&&(typeof setTimeout=="function"||typeof setTimeout=="object")){
var _153=new dojo.io.Error(_152);
setTimeout(function(){
_151[(typeof _151.error=="function")?"error":"handle"]("error",_153,null,_151);
},50);
}else{
dojo.raise(_152);
}
};
dojo.io.queueBind=function(_154){
if(!(_154 instanceof dojo.io.Request)){
try{
_154=new dojo.io.Request(_154);
}
catch(e){
dojo.debug(e);
}
}
var _155=_154.load;
_154.load=function(){
dojo.io._queueBindInFlight=false;
var ret=_155.apply(this,arguments);
dojo.io._dispatchNextQueueBind();
return ret;
};
var _157=_154.error;
_154.error=function(){
dojo.io._queueBindInFlight=false;
var ret=_157.apply(this,arguments);
dojo.io._dispatchNextQueueBind();
return ret;
};
dojo.io._bindQueue.push(_154);
dojo.io._dispatchNextQueueBind();
return _154;
};
dojo.io._dispatchNextQueueBind=function(){
if(!dojo.io._queueBindInFlight){
dojo.io._queueBindInFlight=true;
if(dojo.io._bindQueue.length>0){
dojo.io.bind(dojo.io._bindQueue.shift());
}else{
dojo.io._queueBindInFlight=false;
}
}
};
dojo.io._bindQueue=[];
dojo.io._queueBindInFlight=false;
dojo.io.argsFromMap=function(map,_15a,last){
var enc=/utf/i.test(_15a||"")?encodeURIComponent:dojo.string.encodeAscii;
var _15d=[];
var _15e=new Object();
for(var name in map){
var _160=function(elt){
var val=enc(name)+"="+enc(elt);
_15d[(last==name)?"push":"unshift"](val);
};
if(!_15e[name]){
var _163=map[name];
if(dojo.lang.isArray(_163)){
dojo.lang.forEach(_163,_160);
}else{
_160(_163);
}
}
}
return _15d.join("&");
};
dojo.io.setIFrameSrc=function(_164,src,_166){
try{
var r=dojo.render.html;
if(!_166){
if(r.safari){
_164.location=src;
}else{
frames[_164.name].location=src;
}
}else{
var idoc;
if(r.ie){
idoc=_164.contentWindow.document;
}else{
if(r.safari){
idoc=_164.document;
}else{
idoc=_164.contentWindow;
}
}
if(!idoc){
_164.location=src;
return;
}else{
idoc.location.replace(src);
}
}
}
catch(e){
dojo.debug(e);
dojo.debug("setIFrameSrc: "+e);
}
};
dojo.provide("dojo.lang.array");
dojo.lang.has=function(obj,name){
try{
return (typeof obj[name]!="undefined");
}
catch(e){
return false;
}
};
dojo.lang.isEmpty=function(obj){
if(dojo.lang.isObject(obj)){
var tmp={};
var _16d=0;
for(var x in obj){
if(obj[x]&&(!tmp[x])){
_16d++;
break;
}
}
return (_16d==0);
}else{
if(dojo.lang.isArrayLike(obj)||dojo.lang.isString(obj)){
return obj.length==0;
}
}
};
dojo.lang.map=function(arr,obj,_171){
var _172=dojo.lang.isString(arr);
if(_172){
arr=arr.split("");
}
if(dojo.lang.isFunction(obj)&&(!_171)){
_171=obj;
obj=dj_global;
}else{
if(dojo.lang.isFunction(obj)&&_171){
var _173=obj;
obj=_171;
_171=_173;
}
}
if(Array.map){
var _174=Array.map(arr,_171,obj);
}else{
var _174=[];
for(var i=0;i<arr.length;++i){
_174.push(_171.call(obj,arr[i]));
}
}
if(_172){
return _174.join("");
}else{
return _174;
}
};
dojo.lang.reduce=function(arr,_177,obj,_179){
var _17a=_177;
var ob=obj?obj:dj_global;
dojo.lang.map(arr,function(val){
_17a=_179.call(ob,_17a,val);
});
return _17a;
};
dojo.lang.forEach=function(_17d,_17e,_17f){
if(dojo.lang.isString(_17d)){
_17d=_17d.split("");
}
if(Array.forEach){
Array.forEach(_17d,_17e,_17f);
}else{
if(!_17f){
_17f=dj_global;
}
for(var i=0,l=_17d.length;i<l;i++){
_17e.call(_17f,_17d[i],i,_17d);
}
}
};
dojo.lang._everyOrSome=function(_182,arr,_184,_185){
if(dojo.lang.isString(arr)){
arr=arr.split("");
}
if(Array.every){
return Array[(_182)?"every":"some"](arr,_184,_185);
}else{
if(!_185){
_185=dj_global;
}
for(var i=0,l=arr.length;i<l;i++){
var _188=_184.call(_185,arr[i],i,arr);
if((_182)&&(!_188)){
return false;
}else{
if((!_182)&&(_188)){
return true;
}
}
}
return (_182)?true:false;
}
};
dojo.lang.every=function(arr,_18a,_18b){
return this._everyOrSome(true,arr,_18a,_18b);
};
dojo.lang.some=function(arr,_18d,_18e){
return this._everyOrSome(false,arr,_18d,_18e);
};
dojo.lang.filter=function(arr,_190,_191){
var _192=dojo.lang.isString(arr);
if(_192){
arr=arr.split("");
}
if(Array.filter){
var _193=Array.filter(arr,_190,_191);
}else{
if(!_191){
if(arguments.length>=3){
dojo.raise("thisObject doesn't exist!");
}
_191=dj_global;
}
var _193=[];
for(var i=0;i<arr.length;i++){
if(_190.call(_191,arr[i],i,arr)){
_193.push(arr[i]);
}
}
}
if(_192){
return _193.join("");
}else{
return _193;
}
};
dojo.lang.unnest=function(){
var out=[];
for(var i=0;i<arguments.length;i++){
if(dojo.lang.isArrayLike(arguments[i])){
var add=dojo.lang.unnest.apply(this,arguments[i]);
out=out.concat(add);
}else{
out.push(arguments[i]);
}
}
return out;
};
dojo.lang.toArray=function(_198,_199){
var _19a=[];
for(var i=_199||0;i<_198.length;i++){
_19a.push(_198[i]);
}
return _19a;
};
dojo.provide("dojo.lang.func");
dojo.lang.hitch=function(_19c,_19d){
var fcn=(dojo.lang.isString(_19d)?_19c[_19d]:_19d)||function(){
};
return function(){
return fcn.apply(_19c,arguments);
};
};
dojo.lang.anonCtr=0;
dojo.lang.anon={};
dojo.lang.nameAnonFunc=function(_19f,_1a0,_1a1){
var nso=(_1a0||dojo.lang.anon);
if((_1a1)||((dj_global["djConfig"])&&(djConfig["slowAnonFuncLookups"]==true))){
for(var x in nso){
try{
if(nso[x]===_19f){
return x;
}
}
catch(e){
}
}
}
var ret="__"+dojo.lang.anonCtr++;
while(typeof nso[ret]!="undefined"){
ret="__"+dojo.lang.anonCtr++;
}
nso[ret]=_19f;
return ret;
};
dojo.lang.forward=function(_1a5){
return function(){
return this[_1a5].apply(this,arguments);
};
};
dojo.lang.curry=function(ns,func){
var _1a8=[];
ns=ns||dj_global;
if(dojo.lang.isString(func)){
func=ns[func];
}
for(var x=2;x<arguments.length;x++){
_1a8.push(arguments[x]);
}
var _1aa=(func["__preJoinArity"]||func.length)-_1a8.length;
function gather(_1ab,_1ac,_1ad){
var _1ae=_1ad;
var _1af=_1ac.slice(0);
for(var x=0;x<_1ab.length;x++){
_1af.push(_1ab[x]);
}
_1ad=_1ad-_1ab.length;
if(_1ad<=0){
var res=func.apply(ns,_1af);
_1ad=_1ae;
return res;
}else{
return function(){
return gather(arguments,_1af,_1ad);
};
}
}
return gather([],_1a8,_1aa);
};
dojo.lang.curryArguments=function(ns,func,args,_1b5){
var _1b6=[];
var x=_1b5||0;
for(x=_1b5;x<args.length;x++){
_1b6.push(args[x]);
}
return dojo.lang.curry.apply(dojo.lang,[ns,func].concat(_1b6));
};
dojo.lang.tryThese=function(){
for(var x=0;x<arguments.length;x++){
try{
if(typeof arguments[x]=="function"){
var ret=(arguments[x]());
if(ret){
return ret;
}
}
}
catch(e){
dojo.debug(e);
}
}
};
dojo.lang.delayThese=function(farr,cb,_1bc,_1bd){
if(!farr.length){
if(typeof _1bd=="function"){
_1bd();
}
return;
}
if((typeof _1bc=="undefined")&&(typeof cb=="number")){
_1bc=cb;
cb=function(){
};
}else{
if(!cb){
cb=function(){
};
if(!_1bc){
_1bc=0;
}
}
}
setTimeout(function(){
(farr.shift())();
cb();
dojo.lang.delayThese(farr,cb,_1bc,_1bd);
},_1bc);
};
dojo.provide("dojo.string.extras");
dojo.string.substituteParams=function(_1be,hash){
var map=(typeof hash=="object")?hash:dojo.lang.toArray(arguments,1);
return _1be.replace(/\%\{(\w+)\}/g,function(_1c1,key){
if(typeof (map[key])!="undefined"&&map[key]!=null){
return map[key];
}
dojo.raise("Substitution not found: "+key);
});
};
dojo.string.capitalize=function(str){
if(!dojo.lang.isString(str)){
return "";
}
if(arguments.length==0){
str=this;
}
var _1c4=str.split(" ");
for(var i=0;i<_1c4.length;i++){
_1c4[i]=_1c4[i].charAt(0).toUpperCase()+_1c4[i].substring(1);
}
return _1c4.join(" ");
};
dojo.string.isBlank=function(str){
if(!dojo.lang.isString(str)){
return true;
}
return (dojo.string.trim(str).length==0);
};
dojo.string.encodeAscii=function(str){
if(!dojo.lang.isString(str)){
return str;
}
var ret="";
var _1c9=escape(str);
var _1ca,re=/%u([0-9A-F]{4})/i;
while((_1ca=_1c9.match(re))){
var num=Number("0x"+_1ca[1]);
var _1cd=escape("&#"+num+";");
ret+=_1c9.substring(0,_1ca.index)+_1cd;
_1c9=_1c9.substring(_1ca.index+_1ca[0].length);
}
ret+=_1c9.replace(/\+/g,"%2B");
return ret;
};
dojo.string.escape=function(type,str){
var args=dojo.lang.toArray(arguments,1);
switch(type.toLowerCase()){
case "xml":
case "html":
case "xhtml":
return dojo.string.escapeXml.apply(this,args);
case "sql":
return dojo.string.escapeSql.apply(this,args);
case "regexp":
case "regex":
return dojo.string.escapeRegExp.apply(this,args);
case "javascript":
case "jscript":
case "js":
return dojo.string.escapeJavaScript.apply(this,args);
case "ascii":
return dojo.string.encodeAscii.apply(this,args);
default:
return str;
}
};
dojo.string.escapeXml=function(str,_1d2){
str=str.replace(/&/gm,"&amp;").replace(/</gm,"&lt;").replace(/>/gm,"&gt;").replace(/"/gm,"&quot;");
if(!_1d2){
str=str.replace(/'/gm,"&#39;");
}
return str;
};
dojo.string.escapeSql=function(str){
return str.replace(/'/gm,"''");
};
dojo.string.escapeRegExp=function(str){
return str.replace(/\\/gm,"\\\\").replace(/([\f\b\n\t\r[\^$|?*+(){}])/gm,"\\$1");
};
dojo.string.escapeJavaScript=function(str){
return str.replace(/(["'\f\b\n\t\r])/gm,"\\$1");
};
dojo.string.escapeString=function(str){
return ("\""+str.replace(/(["\\])/g,"\\$1")+"\"").replace(/[\f]/g,"\\f").replace(/[\b]/g,"\\b").replace(/[\n]/g,"\\n").replace(/[\t]/g,"\\t").replace(/[\r]/g,"\\r");
};
dojo.string.summary=function(str,len){
if(!len||str.length<=len){
return str;
}
return str.substring(0,len).replace(/\.+$/,"")+"...";
};
dojo.string.endsWith=function(str,end,_1db){
if(_1db){
str=str.toLowerCase();
end=end.toLowerCase();
}
if((str.length-end.length)<0){
return false;
}
return str.lastIndexOf(end)==str.length-end.length;
};
dojo.string.endsWithAny=function(str){
for(var i=1;i<arguments.length;i++){
if(dojo.string.endsWith(str,arguments[i])){
return true;
}
}
return false;
};
dojo.string.startsWith=function(str,_1df,_1e0){
if(_1e0){
str=str.toLowerCase();
_1df=_1df.toLowerCase();
}
return str.indexOf(_1df)==0;
};
dojo.string.startsWithAny=function(str){
for(var i=1;i<arguments.length;i++){
if(dojo.string.startsWith(str,arguments[i])){
return true;
}
}
return false;
};
dojo.string.has=function(str){
for(var i=1;i<arguments.length;i++){
if(str.indexOf(arguments[i])>-1){
return true;
}
}
return false;
};
dojo.string.normalizeNewlines=function(text,_1e6){
if(_1e6=="\n"){
text=text.replace(/\r\n/g,"\n");
text=text.replace(/\r/g,"\n");
}else{
if(_1e6=="\r"){
text=text.replace(/\r\n/g,"\r");
text=text.replace(/\n/g,"\r");
}else{
text=text.replace(/([^\r])\n/g,"$1\r\n").replace(/\r([^\n])/g,"\r\n$1");
}
}
return text;
};
dojo.string.splitEscaped=function(str,_1e8){
var _1e9=[];
for(var i=0,_1eb=0;i<str.length;i++){
if(str.charAt(i)=="\\"){
i++;
continue;
}
if(str.charAt(i)==_1e8){
_1e9.push(str.substring(_1eb,i));
_1eb=i+1;
}
}
_1e9.push(str.substr(_1eb));
return _1e9;
};
dojo.provide("dojo.dom");
dojo.dom.ELEMENT_NODE=1;
dojo.dom.ATTRIBUTE_NODE=2;
dojo.dom.TEXT_NODE=3;
dojo.dom.CDATA_SECTION_NODE=4;
dojo.dom.ENTITY_REFERENCE_NODE=5;
dojo.dom.ENTITY_NODE=6;
dojo.dom.PROCESSING_INSTRUCTION_NODE=7;
dojo.dom.COMMENT_NODE=8;
dojo.dom.DOCUMENT_NODE=9;
dojo.dom.DOCUMENT_TYPE_NODE=10;
dojo.dom.DOCUMENT_FRAGMENT_NODE=11;
dojo.dom.NOTATION_NODE=12;
dojo.dom.dojoml="http://www.dojotoolkit.org/2004/dojoml";
dojo.dom.xmlns={svg:"http://www.w3.org/2000/svg",smil:"http://www.w3.org/2001/SMIL20/",mml:"http://www.w3.org/1998/Math/MathML",cml:"http://www.xml-cml.org",xlink:"http://www.w3.org/1999/xlink",xhtml:"http://www.w3.org/1999/xhtml",xul:"http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul",xbl:"http://www.mozilla.org/xbl",fo:"http://www.w3.org/1999/XSL/Format",xsl:"http://www.w3.org/1999/XSL/Transform",xslt:"http://www.w3.org/1999/XSL/Transform",xi:"http://www.w3.org/2001/XInclude",xforms:"http://www.w3.org/2002/01/xforms",saxon:"http://icl.com/saxon",xalan:"http://xml.apache.org/xslt",xsd:"http://www.w3.org/2001/XMLSchema",dt:"http://www.w3.org/2001/XMLSchema-datatypes",xsi:"http://www.w3.org/2001/XMLSchema-instance",rdf:"http://www.w3.org/1999/02/22-rdf-syntax-ns#",rdfs:"http://www.w3.org/2000/01/rdf-schema#",dc:"http://purl.org/dc/elements/1.1/",dcq:"http://purl.org/dc/qualifiers/1.0","soap-env":"http://schemas.xmlsoap.org/soap/envelope/",wsdl:"http://schemas.xmlsoap.org/wsdl/",AdobeExtensions:"http://ns.adobe.com/AdobeSVGViewerExtensions/3.0/"};
dojo.dom.isNode=function(wh){
if(typeof Element=="function"){
try{
return wh instanceof Element;
}
catch(E){
}
}else{
return wh&&!isNaN(wh.nodeType);
}
};
dojo.dom.getUniqueId=function(){
var _1ed=dojo.doc();
do{
var id="dj_unique_"+(++arguments.callee._idIncrement);
}while(_1ed.getElementById(id));
return id;
};
dojo.dom.getUniqueId._idIncrement=0;
dojo.dom.firstElement=dojo.dom.getFirstChildElement=function(_1ef,_1f0){
var node=_1ef.firstChild;
while(node&&node.nodeType!=dojo.dom.ELEMENT_NODE){
node=node.nextSibling;
}
if(_1f0&&node&&node.tagName&&node.tagName.toLowerCase()!=_1f0.toLowerCase()){
node=dojo.dom.nextElement(node,_1f0);
}
return node;
};
dojo.dom.lastElement=dojo.dom.getLastChildElement=function(_1f2,_1f3){
var node=_1f2.lastChild;
while(node&&node.nodeType!=dojo.dom.ELEMENT_NODE){
node=node.previousSibling;
}
if(_1f3&&node&&node.tagName&&node.tagName.toLowerCase()!=_1f3.toLowerCase()){
node=dojo.dom.prevElement(node,_1f3);
}
return node;
};
dojo.dom.nextElement=dojo.dom.getNextSiblingElement=function(node,_1f6){
if(!node){
return null;
}
do{
node=node.nextSibling;
}while(node&&node.nodeType!=dojo.dom.ELEMENT_NODE);
if(node&&_1f6&&_1f6.toLowerCase()!=node.tagName.toLowerCase()){
return dojo.dom.nextElement(node,_1f6);
}
return node;
};
dojo.dom.prevElement=dojo.dom.getPreviousSiblingElement=function(node,_1f8){
if(!node){
return null;
}
if(_1f8){
_1f8=_1f8.toLowerCase();
}
do{
node=node.previousSibling;
}while(node&&node.nodeType!=dojo.dom.ELEMENT_NODE);
if(node&&_1f8&&_1f8.toLowerCase()!=node.tagName.toLowerCase()){
return dojo.dom.prevElement(node,_1f8);
}
return node;
};
dojo.dom.moveChildren=function(_1f9,_1fa,trim){
var _1fc=0;
if(trim){
while(_1f9.hasChildNodes()&&_1f9.firstChild.nodeType==dojo.dom.TEXT_NODE){
_1f9.removeChild(_1f9.firstChild);
}
while(_1f9.hasChildNodes()&&_1f9.lastChild.nodeType==dojo.dom.TEXT_NODE){
_1f9.removeChild(_1f9.lastChild);
}
}
while(_1f9.hasChildNodes()){
_1fa.appendChild(_1f9.firstChild);
_1fc++;
}
return _1fc;
};
dojo.dom.copyChildren=function(_1fd,_1fe,trim){
var _200=_1fd.cloneNode(true);
return this.moveChildren(_200,_1fe,trim);
};
dojo.dom.removeChildren=function(node){
var _202=node.childNodes.length;
while(node.hasChildNodes()){
node.removeChild(node.firstChild);
}
return _202;
};
dojo.dom.replaceChildren=function(node,_204){
dojo.dom.removeChildren(node);
node.appendChild(_204);
};
dojo.dom.removeNode=function(node){
if(node&&node.parentNode){
return node.parentNode.removeChild(node);
}
};
dojo.dom.getAncestors=function(node,_207,_208){
var _209=[];
var _20a=(_207&&(_207 instanceof Function||typeof _207=="function"));
while(node){
if(!_20a||_207(node)){
_209.push(node);
}
if(_208&&_209.length>0){
return _209[0];
}
node=node.parentNode;
}
if(_208){
return null;
}
return _209;
};
dojo.dom.getAncestorsByTag=function(node,tag,_20d){
tag=tag.toLowerCase();
return dojo.dom.getAncestors(node,function(el){
return ((el.tagName)&&(el.tagName.toLowerCase()==tag));
},_20d);
};
dojo.dom.getFirstAncestorByTag=function(node,tag){
return dojo.dom.getAncestorsByTag(node,tag,true);
};
dojo.dom.isDescendantOf=function(node,_212,_213){
if(_213&&node){
node=node.parentNode;
}
while(node){
if(node==_212){
return true;
}
node=node.parentNode;
}
return false;
};
dojo.dom.innerXML=function(node){
if(node.innerXML){
return node.innerXML;
}else{
if(node.xml){
return node.xml;
}else{
if(typeof XMLSerializer!="undefined"){
return (new XMLSerializer()).serializeToString(node);
}
}
}
};
dojo.dom.createDocument=function(){
var doc=null;
var _216=dojo.doc();
if(!dj_undef("ActiveXObject")){
var _217=["MSXML2","Microsoft","MSXML","MSXML3"];
for(var i=0;i<_217.length;i++){
try{
doc=new ActiveXObject(_217[i]+".XMLDOM");
}
catch(e){
}
if(doc){
break;
}
}
}else{
if((_216.implementation)&&(_216.implementation.createDocument)){
doc=_216.implementation.createDocument("","",null);
}
}
return doc;
};
dojo.dom.createDocumentFromText=function(str,_21a){
if(!_21a){
_21a="text/xml";
}
if(!dj_undef("DOMParser")){
var _21b=new DOMParser();
return _21b.parseFromString(str,_21a);
}else{
if(!dj_undef("ActiveXObject")){
var _21c=dojo.dom.createDocument();
if(_21c){
_21c.async=false;
_21c.loadXML(str);
return _21c;
}else{
dojo.debug("toXml didn't work?");
}
}else{
var _21d=dojo.doc();
if(_21d.createElement){
var tmp=_21d.createElement("xml");
tmp.innerHTML=str;
if(_21d.implementation&&_21d.implementation.createDocument){
var _21f=_21d.implementation.createDocument("foo","",null);
for(var i=0;i<tmp.childNodes.length;i++){
_21f.importNode(tmp.childNodes.item(i),true);
}
return _21f;
}
return ((tmp.document)&&(tmp.document.firstChild?tmp.document.firstChild:tmp));
}
}
}
return null;
};
dojo.dom.prependChild=function(node,_222){
if(_222.firstChild){
_222.insertBefore(node,_222.firstChild);
}else{
_222.appendChild(node);
}
return true;
};
dojo.dom.insertBefore=function(node,ref,_225){
if(_225!=true&&(node===ref||node.nextSibling===ref)){
return false;
}
var _226=ref.parentNode;
_226.insertBefore(node,ref);
return true;
};
dojo.dom.insertAfter=function(node,ref,_229){
var pn=ref.parentNode;
if(ref==pn.lastChild){
if((_229!=true)&&(node===ref)){
return false;
}
pn.appendChild(node);
}else{
return this.insertBefore(node,ref.nextSibling,_229);
}
return true;
};
dojo.dom.insertAtPosition=function(node,ref,_22d){
if((!node)||(!ref)||(!_22d)){
return false;
}
switch(_22d.toLowerCase()){
case "before":
return dojo.dom.insertBefore(node,ref);
case "after":
return dojo.dom.insertAfter(node,ref);
case "first":
if(ref.firstChild){
return dojo.dom.insertBefore(node,ref.firstChild);
}else{
ref.appendChild(node);
return true;
}
break;
default:
ref.appendChild(node);
return true;
}
};
dojo.dom.insertAtIndex=function(node,_22f,_230){
var _231=_22f.childNodes;
if(!_231.length){
_22f.appendChild(node);
return true;
}
var _232=null;
for(var i=0;i<_231.length;i++){
var _234=_231.item(i)["getAttribute"]?parseInt(_231.item(i).getAttribute("dojoinsertionindex")):-1;
if(_234<_230){
_232=_231.item(i);
}
}
if(_232){
return dojo.dom.insertAfter(node,_232);
}else{
return dojo.dom.insertBefore(node,_231.item(0));
}
};
dojo.dom.textContent=function(node,text){
if(arguments.length>1){
var _237=dojo.doc();
dojo.dom.replaceChildren(node,_237.createTextNode(text));
return text;
}else{
if(node.textContent!=undefined){
return node.textContent;
}
var _238="";
if(node==null){
return _238;
}
for(var i=0;i<node.childNodes.length;i++){
switch(node.childNodes[i].nodeType){
case 1:
case 5:
_238+=dojo.dom.textContent(node.childNodes[i]);
break;
case 3:
case 2:
case 4:
_238+=node.childNodes[i].nodeValue;
break;
default:
break;
}
}
return _238;
}
};
dojo.dom.hasParent=function(node){
return node&&node.parentNode&&dojo.dom.isNode(node.parentNode);
};
dojo.dom.isTag=function(node){
if(node&&node.tagName){
for(var i=1;i<arguments.length;i++){
if(node.tagName==String(arguments[i])){
return String(arguments[i]);
}
}
}
return "";
};
dojo.dom.setAttributeNS=function(elem,_23e,_23f,_240){
if(elem==null||((elem==undefined)&&(typeof elem=="undefined"))){
dojo.raise("No element given to dojo.dom.setAttributeNS");
}
if(!((elem.setAttributeNS==undefined)&&(typeof elem.setAttributeNS=="undefined"))){
elem.setAttributeNS(_23e,_23f,_240);
}else{
var _241=elem.ownerDocument;
var _242=_241.createNode(2,_23f,_23e);
_242.nodeValue=_240;
elem.setAttributeNode(_242);
}
};
dojo.provide("dojo.undo.browser");
try{
if((!djConfig["preventBackButtonFix"])&&(!dojo.hostenv.post_load_)){
document.write("<iframe style='border: 0px; width: 1px; height: 1px; position: absolute; bottom: 0px; right: 0px; visibility: visible;' name='djhistory' id='djhistory' src='"+(dojo.hostenv.getBaseScriptUri()+"iframe_history.html")+"'></iframe>");
}
}
catch(e){
}
if(dojo.render.html.opera){
dojo.debug("Opera is not supported with dojo.undo.browser, so back/forward detection will not work.");
}
dojo.undo.browser={initialHref:window.location.href,initialHash:window.location.hash,moveForward:false,historyStack:[],forwardStack:[],historyIframe:null,bookmarkAnchor:null,locationTimer:null,setInitialState:function(args){
this.initialState=this._createState(this.initialHref,args,this.initialHash);
},addToHistory:function(args){
this.forwardStack=[];
var hash=null;
var url=null;
if(!this.historyIframe){
this.historyIframe=window.frames["djhistory"];
}
if(!this.bookmarkAnchor){
this.bookmarkAnchor=document.createElement("a");
dojo.body().appendChild(this.bookmarkAnchor);
this.bookmarkAnchor.style.display="none";
}
if(args["changeUrl"]){
hash="#"+((args["changeUrl"]!==true)?args["changeUrl"]:(new Date()).getTime());
if(this.historyStack.length==0&&this.initialState.urlHash==hash){
this.initialState=this._createState(url,args,hash);
return;
}else{
if(this.historyStack.length>0&&this.historyStack[this.historyStack.length-1].urlHash==hash){
this.historyStack[this.historyStack.length-1]=this._createState(url,args,hash);
return;
}
}
this.changingUrl=true;
setTimeout("window.location.href = '"+hash+"'; dojo.undo.browser.changingUrl = false;",1);
this.bookmarkAnchor.href=hash;
if(dojo.render.html.ie){
url=this._loadIframeHistory();
var _247=args["back"]||args["backButton"]||args["handle"];
var tcb=function(_249){
if(window.location.hash!=""){
setTimeout("window.location.href = '"+hash+"';",1);
}
_247.apply(this,[_249]);
};
if(args["back"]){
args.back=tcb;
}else{
if(args["backButton"]){
args.backButton=tcb;
}else{
if(args["handle"]){
args.handle=tcb;
}
}
}
var _24a=args["forward"]||args["forwardButton"]||args["handle"];
var tfw=function(_24c){
if(window.location.hash!=""){
window.location.href=hash;
}
if(_24a){
_24a.apply(this,[_24c]);
}
};
if(args["forward"]){
args.forward=tfw;
}else{
if(args["forwardButton"]){
args.forwardButton=tfw;
}else{
if(args["handle"]){
args.handle=tfw;
}
}
}
}else{
if(dojo.render.html.moz){
if(!this.locationTimer){
this.locationTimer=setInterval("dojo.undo.browser.checkLocation();",200);
}
}
}
}else{
url=this._loadIframeHistory();
}
this.historyStack.push(this._createState(url,args,hash));
},checkLocation:function(){
if(!this.changingUrl){
var hsl=this.historyStack.length;
if((window.location.hash==this.initialHash||window.location.href==this.initialHref)&&(hsl==1)){
this.handleBackButton();
return;
}
if(this.forwardStack.length>0){
if(this.forwardStack[this.forwardStack.length-1].urlHash==window.location.hash){
this.handleForwardButton();
return;
}
}
if((hsl>=2)&&(this.historyStack[hsl-2])){
if(this.historyStack[hsl-2].urlHash==window.location.hash){
this.handleBackButton();
return;
}
}
}
},iframeLoaded:function(evt,_24f){
if(!dojo.render.html.opera){
var _250=this._getUrlQuery(_24f.href);
if(_250==null){
if(this.historyStack.length==1){
this.handleBackButton();
}
return;
}
if(this.moveForward){
this.moveForward=false;
return;
}
if(this.historyStack.length>=2&&_250==this._getUrlQuery(this.historyStack[this.historyStack.length-2].url)){
this.handleBackButton();
}else{
if(this.forwardStack.length>0&&_250==this._getUrlQuery(this.forwardStack[this.forwardStack.length-1].url)){
this.handleForwardButton();
}
}
}
},handleBackButton:function(){
var _251=this.historyStack.pop();
if(!_251){
return;
}
var last=this.historyStack[this.historyStack.length-1];
if(!last&&this.historyStack.length==0){
last=this.initialState;
}
if(last){
if(last.kwArgs["back"]){
last.kwArgs["back"]();
}else{
if(last.kwArgs["backButton"]){
last.kwArgs["backButton"]();
}else{
if(last.kwArgs["handle"]){
last.kwArgs.handle("back");
}
}
}
}
this.forwardStack.push(_251);
},handleForwardButton:function(){
var last=this.forwardStack.pop();
if(!last){
return;
}
if(last.kwArgs["forward"]){
last.kwArgs.forward();
}else{
if(last.kwArgs["forwardButton"]){
last.kwArgs.forwardButton();
}else{
if(last.kwArgs["handle"]){
last.kwArgs.handle("forward");
}
}
}
this.historyStack.push(last);
},_createState:function(url,args,hash){
return {"url":url,"kwArgs":args,"urlHash":hash};
},_getUrlQuery:function(url){
var _258=url.split("?");
if(_258.length<2){
return null;
}else{
return _258[1];
}
},_loadIframeHistory:function(){
var url=dojo.hostenv.getBaseScriptUri()+"iframe_history.html?"+(new Date()).getTime();
this.moveForward=true;
dojo.io.setIFrameSrc(this.historyIframe,url,false);
return url;
}};
dojo.provide("dojo.io.BrowserIO");
dojo.io.checkChildrenForFile=function(node){
var _25b=false;
var _25c=node.getElementsByTagName("input");
dojo.lang.forEach(_25c,function(_25d){
if(_25b){
return;
}
if(_25d.getAttribute("type")=="file"){
_25b=true;
}
});
return _25b;
};
dojo.io.formHasFile=function(_25e){
return dojo.io.checkChildrenForFile(_25e);
};
dojo.io.updateNode=function(node,_260){
node=dojo.byId(node);
var args=_260;
if(dojo.lang.isString(_260)){
args={url:_260};
}
args.mimetype="text/html";
args.load=function(t,d,e){
while(node.firstChild){
if(dojo["event"]){
try{
dojo.event.browser.clean(node.firstChild);
}
catch(e){
}
}
node.removeChild(node.firstChild);
}
node.innerHTML=d;
};
dojo.io.bind(args);
};
dojo.io.formFilter=function(node){
var type=(node.type||"").toLowerCase();
return !node.disabled&&node.name&&!dojo.lang.inArray(["file","submit","image","reset","button"],type);
};
dojo.io.encodeForm=function(_267,_268,_269){
if((!_267)||(!_267.tagName)||(!_267.tagName.toLowerCase()=="form")){
dojo.raise("Attempted to encode a non-form element.");
}
if(!_269){
_269=dojo.io.formFilter;
}
var enc=/utf/i.test(_268||"")?encodeURIComponent:dojo.string.encodeAscii;
var _26b=[];
for(var i=0;i<_267.elements.length;i++){
var elm=_267.elements[i];
if(!elm||elm.tagName.toLowerCase()=="fieldset"||!_269(elm)){
continue;
}
var name=enc(elm.name);
var type=elm.type.toLowerCase();
if(type=="select-multiple"){
for(var j=0;j<elm.options.length;j++){
if(elm.options[j].selected){
_26b.push(name+"="+enc(elm.options[j].value));
}
}
}else{
if(dojo.lang.inArray(["radio","checkbox"],type)){
if(elm.checked){
_26b.push(name+"="+enc(elm.value));
}
}else{
_26b.push(name+"="+enc(elm.value));
}
}
}
var _271=_267.getElementsByTagName("input");
for(var i=0;i<_271.length;i++){
var _272=_271[i];
if(_272.type.toLowerCase()=="image"&&_272.form==_267&&_269(_272)){
var name=enc(_272.name);
_26b.push(name+"="+enc(_272.value));
_26b.push(name+".x=0");
_26b.push(name+".y=0");
}
}
return _26b.join("&")+"&";
};
dojo.io.FormBind=function(args){
this.bindArgs={};
if(args&&args.formNode){
this.init(args);
}else{
if(args){
this.init({formNode:args});
}
}
};
dojo.lang.extend(dojo.io.FormBind,{form:null,bindArgs:null,clickedButton:null,init:function(args){
var form=dojo.byId(args.formNode);
if(!form||!form.tagName||form.tagName.toLowerCase()!="form"){
throw new Error("FormBind: Couldn't apply, invalid form");
}else{
if(this.form==form){
return;
}else{
if(this.form){
throw new Error("FormBind: Already applied to a form");
}
}
}
dojo.lang.mixin(this.bindArgs,args);
this.form=form;
this.connect(form,"onsubmit","submit");
for(var i=0;i<form.elements.length;i++){
var node=form.elements[i];
if(node&&node.type&&dojo.lang.inArray(["submit","button"],node.type.toLowerCase())){
this.connect(node,"onclick","click");
}
}
var _278=form.getElementsByTagName("input");
for(var i=0;i<_278.length;i++){
var _279=_278[i];
if(_279.type.toLowerCase()=="image"&&_279.form==form){
this.connect(_279,"onclick","click");
}
}
},onSubmit:function(form){
return true;
},submit:function(e){
e.preventDefault();
if(this.onSubmit(this.form)){
dojo.io.bind(dojo.lang.mixin(this.bindArgs,{formFilter:dojo.lang.hitch(this,"formFilter")}));
}
},click:function(e){
var node=e.currentTarget;
if(node.disabled){
return;
}
this.clickedButton=node;
},formFilter:function(node){
var type=(node.type||"").toLowerCase();
var _280=false;
if(node.disabled||!node.name){
_280=false;
}else{
if(dojo.lang.inArray(["submit","button","image"],type)){
if(!this.clickedButton){
this.clickedButton=node;
}
_280=node==this.clickedButton;
}else{
_280=!dojo.lang.inArray(["file","submit","reset","button"],type);
}
}
return _280;
},connect:function(_281,_282,_283){
if(dojo.evalObjPath("dojo.event.connect")){
dojo.event.connect(_281,_282,this,_283);
}else{
var fcn=dojo.lang.hitch(this,_283);
_281[_282]=function(e){
if(!e){
e=window.event;
}
if(!e.currentTarget){
e.currentTarget=e.srcElement;
}
if(!e.preventDefault){
e.preventDefault=function(){
window.event.returnValue=false;
};
}
fcn(e);
};
}
}});
dojo.io.XMLHTTPTransport=new function(){
var _286=this;
var _287={};
this.useCache=false;
this.preventCache=false;
function getCacheKey(url,_289,_28a){
return url+"|"+_289+"|"+_28a.toLowerCase();
}
function addToCache(url,_28c,_28d,http){
_287[getCacheKey(url,_28c,_28d)]=http;
}
function getFromCache(url,_290,_291){
return _287[getCacheKey(url,_290,_291)];
}
this.clearCache=function(){
_287={};
};
function doLoad(_292,http,url,_295,_296){
if(((http.status>=200)&&(http.status<300))||(http.status==304)||(location.protocol=="file:"&&(http.status==0||http.status==undefined))||(location.protocol=="chrome:"&&(http.status==0||http.status==undefined))){
var ret;
if(_292.method.toLowerCase()=="head"){
var _298=http.getAllResponseHeaders();
ret={};
ret.toString=function(){
return _298;
};
var _299=_298.split(/[\r\n]+/g);
for(var i=0;i<_299.length;i++){
var pair=_299[i].match(/^([^:]+)\s*:\s*(.+)$/i);
if(pair){
ret[pair[1]]=pair[2];
}
}
}else{
if(_292.mimetype=="text/javascript"){
try{
ret=dj_eval(http.responseText);
}
catch(e){
dojo.debug(e);
dojo.debug(http.responseText);
ret=null;
}
}else{
if(_292.mimetype=="text/json"){
try{
ret=dj_eval("("+http.responseText+")");
}
catch(e){
dojo.debug(e);
dojo.debug(http.responseText);
ret=false;
}
}else{
if((_292.mimetype=="application/xml")||(_292.mimetype=="text/xml")){
ret=http.responseXML;
if(!ret||typeof ret=="string"||!http.getResponseHeader("Content-Type")){
ret=dojo.dom.createDocumentFromText(http.responseText);
}
}else{
ret=http.responseText;
}
}
}
}
if(_296){
addToCache(url,_295,_292.method,http);
}
_292[(typeof _292.load=="function")?"load":"handle"]("load",ret,http,_292);
}else{
var _29c=new dojo.io.Error("XMLHttpTransport Error: "+http.status+" "+http.statusText);
_292[(typeof _292.error=="function")?"error":"handle"]("error",_29c,http,_292);
}
}
function setHeaders(http,_29e){
if(_29e["headers"]){
for(var _29f in _29e["headers"]){
if(_29f.toLowerCase()=="content-type"&&!_29e["contentType"]){
_29e["contentType"]=_29e["headers"][_29f];
}else{
http.setRequestHeader(_29f,_29e["headers"][_29f]);
}
}
}
}
this.inFlight=[];
this.inFlightTimer=null;
this.startWatchingInFlight=function(){
if(!this.inFlightTimer){
this.inFlightTimer=setTimeout("dojo.io.XMLHTTPTransport.watchInFlight();",10);
}
};
this.watchInFlight=function(){
var now=null;
if(!dojo.hostenv._blockAsync&&!_286._blockAsync){
for(var x=this.inFlight.length-1;x>=0;x--){
try{
var tif=this.inFlight[x];
if(!tif||tif.http._aborted||!tif.http.readyState){
this.inFlight.splice(x,1);
continue;
}
if(4==tif.http.readyState){
this.inFlight.splice(x,1);
doLoad(tif.req,tif.http,tif.url,tif.query,tif.useCache);
}else{
if(tif.startTime){
if(!now){
now=(new Date()).getTime();
}
if(tif.startTime+(tif.req.timeoutSeconds*1000)<now){
if(typeof tif.http.abort=="function"){
tif.http.abort();
}
this.inFlight.splice(x,1);
tif.req[(typeof tif.req.timeout=="function")?"timeout":"handle"]("timeout",null,tif.http,tif.req);
}
}
}
}
catch(e){
try{
var _2a3=new dojo.io.Error("XMLHttpTransport.watchInFlight Error: "+e);
tif.req[(typeof tif.req.error=="function")?"error":"handle"]("error",_2a3,tif.http,tif.req);
}
catch(e2){
dojo.debug("XMLHttpTransport error callback failed: "+e2);
}
}
}
}
clearTimeout(this.inFlightTimer);
if(this.inFlight.length==0){
this.inFlightTimer=null;
return;
}
this.inFlightTimer=setTimeout("dojo.io.XMLHTTPTransport.watchInFlight();",10);
};
var _2a4=dojo.hostenv.getXmlhttpObject()?true:false;
this.canHandle=function(_2a5){
return _2a4&&dojo.lang.inArray(["text/plain","text/html","application/xml","text/xml","text/javascript","text/json"],(_2a5["mimetype"].toLowerCase()||""))&&!(_2a5["formNode"]&&dojo.io.formHasFile(_2a5["formNode"]));
};
this.multipartBoundary="45309FFF-BD65-4d50-99C9-36986896A96F";
this.bind=function(_2a6){
if(!_2a6["url"]){
if(!_2a6["formNode"]&&(_2a6["backButton"]||_2a6["back"]||_2a6["changeUrl"]||_2a6["watchForURL"])&&(!djConfig.preventBackButtonFix)){
dojo.deprecated("Using dojo.io.XMLHTTPTransport.bind() to add to browser history without doing an IO request","Use dojo.undo.browser.addToHistory() instead.","0.4");
dojo.undo.browser.addToHistory(_2a6);
return true;
}
}
var url=_2a6.url;
var _2a8="";
if(_2a6["formNode"]){
var ta=_2a6.formNode.getAttribute("action");
if((ta)&&(!_2a6["url"])){
url=ta;
}
var tp=_2a6.formNode.getAttribute("method");
if((tp)&&(!_2a6["method"])){
_2a6.method=tp;
}
_2a8+=dojo.io.encodeForm(_2a6.formNode,_2a6.encoding,_2a6["formFilter"]);
}
if(url.indexOf("#")>-1){
dojo.debug("Warning: dojo.io.bind: stripping hash values from url:",url);
url=url.split("#")[0];
}
if(_2a6["file"]){
_2a6.method="post";
}
if(!_2a6["method"]){
_2a6.method="get";
}
if(_2a6.method.toLowerCase()=="get"){
_2a6.multipart=false;
}else{
if(_2a6["file"]){
_2a6.multipart=true;
}else{
if(!_2a6["multipart"]){
_2a6.multipart=false;
}
}
}
if(_2a6["backButton"]||_2a6["back"]||_2a6["changeUrl"]){
dojo.undo.browser.addToHistory(_2a6);
}
var _2ab=_2a6["content"]||{};
if(_2a6.sendTransport){
_2ab["dojo.transport"]="xmlhttp";
}
do{
if(_2a6.postContent){
_2a8=_2a6.postContent;
break;
}
if(_2ab){
_2a8+=dojo.io.argsFromMap(_2ab,_2a6.encoding);
}
if(_2a6.method.toLowerCase()=="get"||!_2a6.multipart){
break;
}
var t=[];
if(_2a8.length){
var q=_2a8.split("&");
for(var i=0;i<q.length;++i){
if(q[i].length){
var p=q[i].split("=");
t.push("--"+this.multipartBoundary,"Content-Disposition: form-data; name=\""+p[0]+"\"","",p[1]);
}
}
}
if(_2a6.file){
if(dojo.lang.isArray(_2a6.file)){
for(var i=0;i<_2a6.file.length;++i){
var o=_2a6.file[i];
t.push("--"+this.multipartBoundary,"Content-Disposition: form-data; name=\""+o.name+"\"; filename=\""+("fileName" in o?o.fileName:o.name)+"\"","Content-Type: "+("contentType" in o?o.contentType:"application/octet-stream"),"",o.content);
}
}else{
var o=_2a6.file;
t.push("--"+this.multipartBoundary,"Content-Disposition: form-data; name=\""+o.name+"\"; filename=\""+("fileName" in o?o.fileName:o.name)+"\"","Content-Type: "+("contentType" in o?o.contentType:"application/octet-stream"),"",o.content);
}
}
if(t.length){
t.push("--"+this.multipartBoundary+"--","");
_2a8=t.join("\r\n");
}
}while(false);
var _2b1=_2a6["sync"]?false:true;
var _2b2=_2a6["preventCache"]||(this.preventCache==true&&_2a6["preventCache"]!=false);
var _2b3=_2a6["useCache"]==true||(this.useCache==true&&_2a6["useCache"]!=false);
if(!_2b2&&_2b3){
var _2b4=getFromCache(url,_2a8,_2a6.method);
if(_2b4){
doLoad(_2a6,_2b4,url,_2a8,false);
return;
}
}
var http=dojo.hostenv.getXmlhttpObject(_2a6);
var _2b6=false;
if(_2b1){
var _2b7=this.inFlight.push({"req":_2a6,"http":http,"url":url,"query":_2a8,"useCache":_2b3,"startTime":_2a6.timeoutSeconds?(new Date()).getTime():0});
this.startWatchingInFlight();
}else{
_286._blockAsync=true;
}
if(_2a6.method.toLowerCase()=="post"){
if(!_2a6.user){
http.open("POST",url,_2b1);
}else{
http.open("POST",url,_2b1,_2a6.user,_2a6.password);
}
setHeaders(http,_2a6);
http.setRequestHeader("Content-Type",_2a6.multipart?("multipart/form-data; boundary="+this.multipartBoundary):(_2a6.contentType||"application/x-www-form-urlencoded"));
try{
http.send(_2a8);
}
catch(e){
if(typeof http.abort=="function"){
http.abort();
}
doLoad(_2a6,{status:404},url,_2a8,_2b3);
}
}else{
var _2b8=url;
if(_2a8!=""){
_2b8+=(_2b8.indexOf("?")>-1?"&":"?")+_2a8;
}
if(_2b2){
_2b8+=(dojo.string.endsWithAny(_2b8,"?","&")?"":(_2b8.indexOf("?")>-1?"&":"?"))+"dojo.preventCache="+new Date().valueOf();
}
http.open(_2a6.method.toUpperCase(),_2b8,_2b1);
setHeaders(http,_2a6);
try{
http.send(null);
}
catch(e){
if(typeof http.abort=="function"){
http.abort();
}
doLoad(_2a6,{status:404},url,_2a8,_2b3);
}
}
if(!_2b1){
doLoad(_2a6,http,url,_2a8,_2b3);
_286._blockAsync=false;
}
_2a6.abort=function(){
try{
http._aborted=true;
}
catch(e){
}
return http.abort();
};
return;
};
dojo.io.transports.addTransport("XMLHTTPTransport");
};
dojo.provide("dojo.io.cookie");
dojo.io.cookie.setCookie=function(name,_2ba,days,path,_2bd,_2be){
var _2bf=-1;
if(typeof days=="number"&&days>=0){
var d=new Date();
d.setTime(d.getTime()+(days*24*60*60*1000));
_2bf=d.toGMTString();
}
_2ba=escape(_2ba);
document.cookie=name+"="+_2ba+";"+(_2bf!=-1?" expires="+_2bf+";":"")+(path?"path="+path:"")+(_2bd?"; domain="+_2bd:"")+(_2be?"; secure":"");
};
dojo.io.cookie.set=dojo.io.cookie.setCookie;
dojo.io.cookie.getCookie=function(name){
var idx=document.cookie.lastIndexOf(name+"=");
if(idx==-1){
return null;
}
var _2c3=document.cookie.substring(idx+name.length+1);
var end=_2c3.indexOf(";");
if(end==-1){
end=_2c3.length;
}
_2c3=_2c3.substring(0,end);
_2c3=unescape(_2c3);
return _2c3;
};
dojo.io.cookie.get=dojo.io.cookie.getCookie;
dojo.io.cookie.deleteCookie=function(name){
dojo.io.cookie.setCookie(name,"-",0);
};
dojo.io.cookie.setObjectCookie=function(name,obj,days,path,_2ca,_2cb,_2cc){
if(arguments.length==5){
_2cc=_2ca;
_2ca=null;
_2cb=null;
}
var _2cd=[],_2ce,_2cf="";
if(!_2cc){
_2ce=dojo.io.cookie.getObjectCookie(name);
}
if(days>=0){
if(!_2ce){
_2ce={};
}
for(var prop in obj){
if(prop==null){
delete _2ce[prop];
}else{
if(typeof obj[prop]=="string"||typeof obj[prop]=="number"){
_2ce[prop]=obj[prop];
}
}
}
prop=null;
for(var prop in _2ce){
_2cd.push(escape(prop)+"="+escape(_2ce[prop]));
}
_2cf=_2cd.join("&");
}
dojo.io.cookie.setCookie(name,_2cf,days,path,_2ca,_2cb);
};
dojo.io.cookie.getObjectCookie=function(name){
var _2d2=null,_2d3=dojo.io.cookie.getCookie(name);
if(_2d3){
_2d2={};
var _2d4=_2d3.split("&");
for(var i=0;i<_2d4.length;i++){
var pair=_2d4[i].split("=");
var _2d7=pair[1];
if(isNaN(_2d7)){
_2d7=unescape(pair[1]);
}
_2d2[unescape(pair[0])]=_2d7;
}
}
return _2d2;
};
dojo.io.cookie.isSupported=function(){
if(typeof navigator.cookieEnabled!="boolean"){
dojo.io.cookie.setCookie("__TestingYourBrowserForCookieSupport__","CookiesAllowed",90,null);
var _2d8=dojo.io.cookie.getCookie("__TestingYourBrowserForCookieSupport__");
navigator.cookieEnabled=(_2d8=="CookiesAllowed");
if(navigator.cookieEnabled){
this.deleteCookie("__TestingYourBrowserForCookieSupport__");
}
}
return navigator.cookieEnabled;
};
if(!dojo.io.cookies){
dojo.io.cookies=dojo.io.cookie;
}
dojo.provide("dojo.io.*");
dojo.provide("dojo.AdapterRegistry");
dojo.AdapterRegistry=function(_2d9){
this.pairs=[];
this.returnWrappers=_2d9||false;
};
dojo.lang.extend(dojo.AdapterRegistry,{register:function(name,_2db,wrap,_2dd,_2de){
var type=(_2de)?"unshift":"push";
this.pairs[type]([name,_2db,wrap,_2dd]);
},match:function(){
for(var i=0;i<this.pairs.length;i++){
var pair=this.pairs[i];
if(pair[1].apply(this,arguments)){
if((pair[3])||(this.returnWrappers)){
return pair[2];
}else{
return pair[2].apply(this,arguments);
}
}
}
throw new Error("No match found");
},unregister:function(name){
for(var i=0;i<this.pairs.length;i++){
var pair=this.pairs[i];
if(pair[0]==name){
this.pairs.splice(i,1);
return true;
}
}
return false;
}});
dojo.provide("dojo.json");
dojo.json={jsonRegistry:new dojo.AdapterRegistry(),register:function(name,_2e6,wrap,_2e8){
dojo.json.jsonRegistry.register(name,_2e6,wrap,_2e8);
},evalJson:function(json){
try{
return eval("("+json+")");
}
catch(e){
dojo.debug(e);
return json;
}
},serialize:function(o){
var _2eb=typeof (o);
if(_2eb=="undefined"){
return "undefined";
}else{
if((_2eb=="number")||(_2eb=="boolean")){
return o+"";
}else{
if(o===null){
return "null";
}
}
}
if(_2eb=="string"){
return dojo.string.escapeString(o);
}
var me=arguments.callee;
var _2ed;
if(typeof (o.__json__)=="function"){
_2ed=o.__json__();
if(o!==_2ed){
return me(_2ed);
}
}
if(typeof (o.json)=="function"){
_2ed=o.json();
if(o!==_2ed){
return me(_2ed);
}
}
if(_2eb!="function"&&typeof (o.length)=="number"){
var res=[];
for(var i=0;i<o.length;i++){
var val=me(o[i]);
if(typeof (val)!="string"){
val="undefined";
}
res.push(val);
}
return "["+res.join(",")+"]";
}
try{
window.o=o;
_2ed=dojo.json.jsonRegistry.match(o);
return me(_2ed);
}
catch(e){
}
if(_2eb=="function"){
return null;
}
res=[];
for(var k in o){
var _2f2;
if(typeof (k)=="number"){
_2f2="\""+k+"\"";
}else{
if(typeof (k)=="string"){
_2f2=dojo.string.escapeString(k);
}else{
continue;
}
}
val=me(o[k]);
if(typeof (val)!="string"){
continue;
}
res.push(_2f2+":"+val);
}
return "{"+res.join(",")+"}";
}};
dojo.provide("dojo.Deferred");
dojo.Deferred=function(_2f3){
this.chain=[];
this.id=this._nextId();
this.fired=-1;
this.paused=0;
this.results=[null,null];
this.canceller=_2f3;
this.silentlyCancelled=false;
};
dojo.lang.extend(dojo.Deferred,{getFunctionFromArgs:function(){
var a=arguments;
if((a[0])&&(!a[1])){
if(dojo.lang.isFunction(a[0])){
return a[0];
}else{
if(dojo.lang.isString(a[0])){
return dj_global[a[0]];
}
}
}else{
if((a[0])&&(a[1])){
return dojo.lang.hitch(a[0],a[1]);
}
}
return null;
},makeCalled:function(){
var _2f5=new dojo.Deferred();
_2f5.callback();
return _2f5;
},repr:function(){
var _2f6;
if(this.fired==-1){
_2f6="unfired";
}else{
if(this.fired==0){
_2f6="success";
}else{
_2f6="error";
}
}
return "Deferred("+this.id+", "+_2f6+")";
},toString:dojo.lang.forward("repr"),_nextId:(function(){
var n=1;
return function(){
return n++;
};
})(),cancel:function(){
if(this.fired==-1){
if(this.canceller){
this.canceller(this);
}else{
this.silentlyCancelled=true;
}
if(this.fired==-1){
this.errback(new Error(this.repr()));
}
}else{
if((this.fired==0)&&(this.results[0] instanceof dojo.Deferred)){
this.results[0].cancel();
}
}
},_pause:function(){
this.paused++;
},_unpause:function(){
this.paused--;
if((this.paused==0)&&(this.fired>=0)){
this._fire();
}
},_continue:function(res){
this._resback(res);
this._unpause();
},_resback:function(res){
this.fired=((res instanceof Error)?1:0);
this.results[this.fired]=res;
this._fire();
},_check:function(){
if(this.fired!=-1){
if(!this.silentlyCancelled){
dojo.raise("already called!");
}
this.silentlyCancelled=false;
return;
}
},callback:function(res){
this._check();
this._resback(res);
},errback:function(res){
this._check();
if(!(res instanceof Error)){
res=new Error(res);
}
this._resback(res);
},addBoth:function(cb,cbfn){
var _2fe=this.getFunctionFromArgs(cb,cbfn);
if(arguments.length>2){
_2fe=dojo.lang.curryArguments(null,_2fe,arguments,2);
}
return this.addCallbacks(_2fe,_2fe);
},addCallback:function(cb,cbfn){
var _301=this.getFunctionFromArgs(cb,cbfn);
if(arguments.length>2){
_301=dojo.lang.curryArguments(null,_301,arguments,2);
}
return this.addCallbacks(_301,null);
},addErrback:function(cb,cbfn){
var _304=this.getFunctionFromArgs(cb,cbfn);
if(arguments.length>2){
_304=dojo.lang.curryArguments(null,_304,arguments,2);
}
return this.addCallbacks(null,_304);
return this.addCallbacks(null,cbfn);
},addCallbacks:function(cb,eb){
this.chain.push([cb,eb]);
if(this.fired>=0){
this._fire();
}
return this;
},_fire:function(){
var _307=this.chain;
var _308=this.fired;
var res=this.results[_308];
var self=this;
var cb=null;
while(_307.length>0&&this.paused==0){
var pair=_307.shift();
var f=pair[_308];
if(f==null){
continue;
}
try{
res=f(res);
_308=((res instanceof Error)?1:0);
if(res instanceof dojo.Deferred){
cb=function(res){
self._continue(res);
};
this._pause();
}
}
catch(err){
_308=1;
res=err;
}
}
this.fired=_308;
this.results[_308]=res;
if((cb)&&(this.paused)){
res.addBoth(cb);
}
}});
dojo.provide("dojo.rpc.RpcService");
dojo.rpc.RpcService=function(url){
if(url){
this.connect(url);
}
};
dojo.lang.extend(dojo.rpc.RpcService,{strictArgChecks:true,serviceUrl:"",parseResults:function(obj){
return obj;
},errorCallback:function(_311){
return function(type,e){
_311.errback(new Error(e.message));
};
},resultCallback:function(_314){
var tf=dojo.lang.hitch(this,function(type,obj,e){
if(obj["error"]!=null){
var err=new Error(obj.error);
err.id=obj.id;
_314.errback(err);
}else{
var _31a=this.parseResults(obj);
_314.callback(_31a);
}
});
return tf;
},generateMethod:function(_31b,_31c,url){
return dojo.lang.hitch(this,function(){
var _31e=new dojo.Deferred();
if((this.strictArgChecks)&&(_31c!=null)&&(arguments.length!=_31c.length)){
dojo.raise("Invalid number of parameters for remote method.");
}else{
this.bind(_31b,arguments,_31e,url);
}
return _31e;
});
},processSmd:function(_31f){
dojo.debug("RpcService: Processing returned SMD.");
if(_31f.methods){
dojo.lang.forEach(_31f.methods,function(m){
if(m&&m["name"]){
dojo.debug("RpcService: Creating Method: this.",m.name,"()");
this[m.name]=this.generateMethod(m.name,m.parameters,m["url"]||m["serviceUrl"]||m["serviceURL"]);
if(dojo.lang.isFunction(this[m.name])){
dojo.debug("RpcService: Successfully created",m.name,"()");
}else{
dojo.debug("RpcService: Failed to create",m.name,"()");
}
}
},this);
}
this.serviceUrl=_31f.serviceUrl||_31f.serviceURL;
dojo.debug("RpcService: Dojo RpcService is ready for use.");
},connect:function(_321){
dojo.debug("RpcService: Attempting to load SMD document from:",_321);
dojo.io.bind({url:_321,mimetype:"text/json",load:dojo.lang.hitch(this,function(type,_323,e){
return this.processSmd(_323);
}),sync:true});
}});
dojo.provide("dojo.rpc.JsonService");
dojo.rpc.JsonService=function(args){
if(args){
if(dojo.lang.isString(args)){
this.connect(args);
}else{
if(args["smdUrl"]){
this.connect(args.smdUrl);
}
if(args["smdStr"]){
this.processSmd(dj_eval("("+args.smdStr+")"));
}
if(args["smdObj"]){
this.processSmd(args.smdObj);
}
if(args["serviceUrl"]){
this.serviceUrl=args.serviceUrl;
}
if(typeof args["strictArgChecks"]!="undefined"){
this.strictArgChecks=args.strictArgChecks;
}
}
}
};
dojo.inherits(dojo.rpc.JsonService,dojo.rpc.RpcService);
dojo.extend(dojo.rpc.JsonService,{bustCache:false,contentType:"application/json-rpc",lastSubmissionId:0,callRemote:function(_326,_327){
var _328=new dojo.Deferred();
this.bind(_326,_327,_328);
return _328;
},bind:function(_329,_32a,_32b,url){
dojo.io.bind({url:url||this.serviceUrl,postContent:this.createRequest(_329,_32a),method:"POST",contentType:this.contentType,mimetype:"text/json",load:this.resultCallback(_32b),error:this.errorCallback(_32b),preventCache:this.bustCache});
},createRequest:function(_32d,_32e){
var req={"params":_32e,"method":_32d,"id":++this.lastSubmissionId};
var data=dojo.json.serialize(req);
dojo.debug("JsonService: JSON-RPC Request: "+data);
return data;
},parseResults:function(obj){
if(!obj){
return;
}
if(obj["Result"]!=null){
return obj["Result"];
}else{
if(obj["result"]!=null){
return obj["result"];
}else{
if(obj["ResultSet"]){
return obj["ResultSet"];
}else{
return obj;
}
}
}
}});
dojo.provide("dojo.rpc.*");

