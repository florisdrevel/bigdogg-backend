((a,b)=>{a[b]=a[b]||{}})(self,"$__dart_deferred_initializers__")
$__dart_deferred_initializers__.current=function(a,b,c,$){var J,B,C,A={
bzR(){return new b.G.XMLHttpRequest()},
bzS(){return b.G.document.createElement("img")},
bia(d,e,f){var x=new A.a4G(d,B.a([],y.v),B.a([],y.l),B.a([],y.u))
x.ajH(d,e,f)
return x},
AK:function AK(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
ask:function ask(d,e,f){this.a=d
this.b=e
this.c=f},
asl:function asl(d,e){this.a=d
this.b=e},
asi:function asi(d,e,f){this.a=d
this.b=e
this.c=f},
asj:function asj(d,e,f){this.a=d
this.b=e
this.c=f},
a4G:function a4G(d,e,f,g){var _=this
_.y=d
_.z=!1
_.Q=$
_.as=!1
_.at=$
_.a=e
_.b=f
_.e=_.d=_.c=null
_.f=!1
_.r=0
_.w=!1
_.x=g},
aLv:function aLv(d){this.a=d},
aLw:function aLw(d,e){this.a=d
this.b=e},
aLx:function aLx(d){this.a=d},
aLy:function aLy(d){this.a=d},
aLz:function aLz(d){this.a=d},
Cu:function Cu(d,e){this.a=d
this.b=e},
btE(d,e){return new A.AL("HTTP request failed, statusCode: "+d+", "+e.j(0))},
aCb:function aCb(d,e){this.a=d
this.b=e},
AL:function AL(d){this.b=d},
btM(d,e){var x=new A.XU(B.a([],y.v),B.a([],y.l),B.a([],y.u))
x.ajt(d,e)
return x},
XU:function XU(d,e,f){var _=this
_.a=d
_.b=e
_.e=_.d=_.c=null
_.f=!1
_.r=0
_.w=!1
_.x=f},
asG:function asG(d,e){this.a=d
this.b=e},
beP(d,e,f){var x=null
return new B.qX(B.b9l(x,x,new A.AK(d,1,x,D.ahG)),e,x,x,f,x)}},D
J=c[1]
B=c[0]
C=c[2]
A=a.updateHolder(c[14],A)
D=c[55]
A.AK.prototype={
Bt(d){return new B.dg(this,y.i)},
w4(d,e){return A.bia(this.xn(d,e),d.a,null)},
w5(d,e){return A.bia(this.xn(d,e),d.a,null)},
xn(d,e){return this.awS(d,e)},
awS(d,e){var x=0,w=B.o(y.R),v,u=2,t=[],s=this,r,q,p,o,n
var $async$xn=B.k(function(f,g){if(f===1){t.push(g)
x=u}for(;;)switch(x){case 0:p=new A.ask(s,e,d)
o=new A.asl(s,d)
case 3:switch(s.d.a){case 0:x=5
break
case 2:x=6
break
case 1:x=7
break
default:x=4
break}break
case 5:v=p.$0()
x=1
break
case 6:v=o.$0()
x=1
break
case 7:u=9
x=12
return B.e(p.$0(),$async$xn)
case 12:r=g
v=r
x=1
break
u=2
x=11
break
case 9:u=8
n=t.pop()
r=o.$0()
v=r
x=1
break
x=11
break
case 8:x=2
break
case 11:x=4
break
case 4:case 1:return B.m(v,w)
case 2:return B.l(t.at(-1),w)}})
return B.n($async$xn,w)},
ye(d){var x=0,w=B.o(y.p),v,u=this,t,s,r,q,p,o,n
var $async$ye=B.k(function(e,f){if(e===1)return B.l(f,w)
for(;;)switch(x){case 0:s=u.a
r=B.a0V().U(s)
q=new B.ap($.ax,y.Z)
p=new B.b7(q,y.x)
o=A.bzR()
o.open("GET",s,!0)
o.responseType="arraybuffer"
o.addEventListener("load",B.j5(new A.asi(o,p,r)))
o.addEventListener("error",B.j5(new A.asj(p,o,r)))
o.send()
x=3
return B.e(q,$async$ye)
case 3:s=o.response
s.toString
t=B.b8Z(y.a.a(s),0,null)
if(t.byteLength===0)throw B.i(A.btE(B.a5(o,"status"),r))
n=d
x=4
return B.e(B.Wz(t),$async$ye)
case 4:v=n.$1(f)
x=1
break
case 1:return B.m(v,w)}})
return B.n($async$ye,w)},
k(d,e){var x=this
if(e==null)return!1
if(J.ae(e)!==B.O(x))return!1
return e instanceof A.AK&&e.a===x.a&&e.b===x.b&&e.d===x.d&&B.Ea(e.c,x.c)},
gD(d){var x=this
return B.a8(x.a,x.b,x.d,C.CK.fG(0,x.c),C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a)},
j(d){var x=this
return'NetworkImage("'+x.a+'", scale: '+C.k.S(x.b,1)+", webHtmlElementStrategy: "+x.d.b+", headers: "+B.j(x.c)+")"}}
A.a4G.prototype={
ajH(d,e,f){var x=this
x.e=e
x.y.fd(new A.aLv(x),new A.aLw(x,f),y.P)},
gaa0(d){var x=this,w=x.at
return w===$?x.at=new B.iH(new A.aLx(x),new A.aLy(x),new A.aLz(x)):w},
Tf(){var x,w=this
if(w.z){x=w.Q
x===$&&B.b()
x.M(0,w.gaa0(0))}w.as=!0
w.af4()}}
A.Cu.prototype={
QL(d){return new A.Cu(this.a,this.b)},
l(){},
gfp(d){return B.a4(B.aF("Could not create image data for this image because access to it is restricted by the Same-Origin Policy.\nSee https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy"))},
gq8(d){return 1},
gVK(){var x=this.a
return C.e.dB(4*x.naturalWidth*x.naturalHeight)},
$iiG:1,
gjL(){return this.b}}
A.aCb.prototype={
L(){return"WebHtmlElementStrategy."+this.b}}
A.AL.prototype={
j(d){return this.b},
$ic5:1}
A.XU.prototype={
ajt(d,e){d.fd(this.gadz(),new A.asG(this,e),y.H)}}
var z=a.updateTypes([])
A.ask.prototype={
$0(){var x=0,w=B.o(y.R),v,u=this,t,s,r
var $async$$0=B.k(function(d,e){if(d===1)return B.l(e,w)
for(;;)switch(x){case 0:t=u.c
s=B
r=B
x=3
return B.e(u.a.ye(u.b),$async$$0)
case 3:v=s.Xw(r.dt(e,y.p),t.a,null,t.b)
x=1
break
case 1:return B.m(v,w)}})
return B.n($async$$0,w)},
$S:275}
A.asl.prototype={
$0(){var x=0,w=B.o(y.R),v,u=this,t,s,r
var $async$$0=B.k(function(d,e){if(d===1)return B.l(e,w)
for(;;)switch(x){case 0:s=A.bzS()
r=u.b.a
s.src=r
x=3
return B.e(B.fU(s.decode(),y.X),$async$$0)
case 3:t=A.btM(B.dt(new A.Cu(s,r),y.J),null)
t.e=r
v=t
x=1
break
case 1:return B.m(v,w)}})
return B.n($async$$0,w)},
$S:275}
A.asi.prototype={
$1(d){var x=this.a,w=x.status,v=w>=200&&w<300,u=w>307&&w<400,t=v||w===0||w===304||u,s=this.b
if(t)s.dc(0,x)
else s.iy(new A.AL("HTTP request failed, statusCode: "+B.j(w)+", "+this.c.j(0)))},
$S:43}
A.asj.prototype={
$1(d){return this.a.iy(new A.AL("HTTP request failed, statusCode: "+B.j(this.b.status)+", "+this.c.j(0)))},
$S:2}
A.aLv.prototype={
$1(d){var x=this.a
x.z=!0
if(x.as){d.yP()
return}x.Q!==$&&B.bd()
x.Q=d
d.a2(0,x.gaa0(0))},
$S:731}
A.aLw.prototype={
$2(d,e){this.a.t9(B.c4("resolving an image stream completer"),d,this.b,!0,e)},
$S:32}
A.aLx.prototype={
$2(d,e){this.a.KK(d)},
$S:227}
A.aLy.prototype={
$1(d){this.a.aPS(d)},
$S:732}
A.aLz.prototype={
$2(d,e){this.a.aPR(d,e)},
$S:128}
A.asG.prototype={
$2(d,e){this.a.t9(B.c4("resolving a single-frame image stream"),d,this.b,!0,e)},
$S:32};(function inheritance(){var x=a.inherit,w=a.inheritMany
x(A.AK,B.hq)
w(B.h_,[A.ask,A.asl])
w(B.eK,[A.asi,A.asj,A.aLv,A.aLy])
w(B.hr,[A.a4G,A.XU])
w(B.jb,[A.aLw,A.aLx,A.aLz,A.asG])
w(B.N,[A.Cu,A.AL])
x(A.aCb,B.kx)})()
B.fB(b.typeUniverse,JSON.parse('{"AK":{"hq":["b90"],"hq.T":"b90"},"a4G":{"hr":[]},"Cu":{"iG":[]},"b90":{"hq":["b90"]},"AL":{"c5":[]},"XU":{"hr":[]}}'))
var y=(function rtii(){var x=B.ab
return{p:x("h0"),J:x("iG"),R:x("hr"),v:x("C<iH>"),u:x("C<~()>"),l:x("C<~(N,dv?)>"),a:x("rp"),P:x("br"),i:x("dg<AK>"),x:x("b7<ag>"),Z:x("ap<ag>"),X:x("N?"),H:x("~")}})();(function constants(){D.nE=new B.aX(C.z,1,C.H,-1)
D.dX=new B.i6(null,null,null,null)
D.wJ=new B.aj(61195,"MaterialIcons",null,!1)
D.eC=new B.cd(16,16,C.kF,null)
D.eF=new B.q(!0,null,null,null,null,null,null,C.aa,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)
D.ahG=new A.aCb(0,"never")})()};
(a=>{a["C8QVdHhkzYW24J/Vx+2ewaVVs3s="]=a.current})($__dart_deferred_initializers__);