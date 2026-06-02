((a,b)=>{a[b]=a[b]||{}})(self,"$__dart_deferred_initializers__")
$__dart_deferred_initializers__.current=function(a,b,c,$){var J,B,C,A={
bzv(){return new b.G.XMLHttpRequest()},
bzw(){return b.G.document.createElement("img")},
bhP(d,e,f){var x=new A.a4S(d,B.a([],y.v),B.a([],y.l),B.a([],y.u))
x.ajr(d,e,f)
return x},
AK:function AK(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
asi:function asi(d,e,f){this.a=d
this.b=e
this.c=f},
asj:function asj(d,e){this.a=d
this.b=e},
asg:function asg(d,e,f){this.a=d
this.b=e
this.c=f},
ash:function ash(d,e,f){this.a=d
this.b=e
this.c=f},
a4S:function a4S(d,e,f,g){var _=this
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
aLb:function aLb(d){this.a=d},
aLc:function aLc(d,e){this.a=d
this.b=e},
aLd:function aLd(d){this.a=d},
aLe:function aLe(d){this.a=d},
aLf:function aLf(d){this.a=d},
Cu:function Cu(d,e){this.a=d
this.b=e},
btj(d,e){return new A.AL("HTTP request failed, statusCode: "+d+", "+e.j(0))},
aBT:function aBT(d,e){this.a=d
this.b=e},
AL:function AL(d){this.b=d},
btr(d,e){var x=new A.Y1(B.a([],y.v),B.a([],y.l),B.a([],y.u))
x.ajd(d,e)
return x},
Y1:function Y1(d,e,f){var _=this
_.a=d
_.b=e
_.e=_.d=_.c=null
_.f=!1
_.r=0
_.w=!1
_.x=f},
asv:function asv(d,e){this.a=d
this.b=e},
bet(d,e,f){var x=null
return new B.qW(B.b91(x,x,new A.AK(d,1,x,D.ahG)),e,x,x,f,x)}},D
J=c[1]
B=c[0]
C=c[2]
A=a.updateHolder(c[14],A)
D=c[55]
A.AK.prototype={
Bo(d){return new B.dg(this,y.i)},
w0(d,e){return A.bhP(this.xj(d,e),d.a,null)},
w1(d,e){return A.bhP(this.xj(d,e),d.a,null)},
xj(d,e){return this.awz(d,e)},
awz(d,e){var x=0,w=B.o(y.R),v,u=2,t=[],s=this,r,q,p,o,n
var $async$xj=B.k(function(f,g){if(f===1){t.push(g)
x=u}for(;;)switch(x){case 0:p=new A.asi(s,e,d)
o=new A.asj(s,d)
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
return B.e(p.$0(),$async$xj)
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
return B.n($async$xj,w)},
yb(d){var x=0,w=B.o(y.p),v,u=this,t,s,r,q,p,o,n
var $async$yb=B.k(function(e,f){if(e===1)return B.l(f,w)
for(;;)switch(x){case 0:s=u.a
r=B.a16().U(s)
q=new B.ap($.ax,y.Z)
p=new B.b7(q,y.x)
o=A.bzv()
o.open("GET",s,!0)
o.responseType="arraybuffer"
o.addEventListener("load",B.j3(new A.asg(o,p,r)))
o.addEventListener("error",B.j3(new A.ash(p,o,r)))
o.send()
x=3
return B.e(q,$async$yb)
case 3:s=o.response
s.toString
t=B.b8F(y.a.a(s),0,null)
if(t.byteLength===0)throw B.i(A.btj(B.a5(o,"status"),r))
n=d
x=4
return B.e(B.WE(t),$async$yb)
case 4:v=n.$1(f)
x=1
break
case 1:return B.m(v,w)}})
return B.n($async$yb,w)},
k(d,e){var x=this
if(e==null)return!1
if(J.ae(e)!==B.O(x))return!1
return e instanceof A.AK&&e.a===x.a&&e.b===x.b&&e.d===x.d&&B.Ea(e.c,x.c)},
gD(d){var x=this
return B.a8(x.a,x.b,x.d,C.CK.fH(0,x.c),C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a,C.a)},
j(d){var x=this
return'NetworkImage("'+x.a+'", scale: '+C.k.S(x.b,1)+", webHtmlElementStrategy: "+x.d.b+", headers: "+B.j(x.c)+")"}}
A.a4S.prototype={
ajr(d,e,f){var x=this
x.e=e
x.y.fe(new A.aLb(x),new A.aLc(x,f),y.P)},
ga9L(d){var x=this,w=x.at
return w===$?x.at=new B.iF(new A.aLd(x),new A.aLe(x),new A.aLf(x)):w},
T4(){var x,w=this
if(w.z){x=w.Q
x===$&&B.b()
x.M(0,w.ga9L(0))}w.as=!0
w.aeP()}}
A.Cu.prototype={
QA(d){return new A.Cu(this.a,this.b)},
l(){},
gfs(d){return B.a4(B.aF("Could not create image data for this image because access to it is restricted by the Same-Origin Policy.\nSee https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy"))},
gq7(d){return 1},
gVz(){var x=this.a
return C.e.dC(4*x.naturalWidth*x.naturalHeight)},
$iiE:1,
gjO(){return this.b}}
A.aBT.prototype={
L(){return"WebHtmlElementStrategy."+this.b}}
A.AL.prototype={
j(d){return this.b},
$ic5:1}
A.Y1.prototype={
ajd(d,e){d.fe(this.gadj(),new A.asv(this,e),y.H)}}
var z=a.updateTypes([])
A.asi.prototype={
$0(){var x=0,w=B.o(y.R),v,u=this,t,s,r
var $async$$0=B.k(function(d,e){if(d===1)return B.l(e,w)
for(;;)switch(x){case 0:t=u.c
s=B
r=B
x=3
return B.e(u.a.yb(u.b),$async$$0)
case 3:v=s.XB(r.dt(e,y.p),t.a,null,t.b)
x=1
break
case 1:return B.m(v,w)}})
return B.n($async$$0,w)},
$S:274}
A.asj.prototype={
$0(){var x=0,w=B.o(y.R),v,u=this,t,s,r
var $async$$0=B.k(function(d,e){if(d===1)return B.l(e,w)
for(;;)switch(x){case 0:s=A.bzw()
r=u.b.a
s.src=r
x=3
return B.e(B.fT(s.decode(),y.X),$async$$0)
case 3:t=A.btr(B.dt(new A.Cu(s,r),y.J),null)
t.e=r
v=t
x=1
break
case 1:return B.m(v,w)}})
return B.n($async$$0,w)},
$S:274}
A.asg.prototype={
$1(d){var x=this.a,w=x.status,v=w>=200&&w<300,u=w>307&&w<400,t=v||w===0||w===304||u,s=this.b
if(t)s.dd(0,x)
else s.iz(new A.AL("HTTP request failed, statusCode: "+B.j(w)+", "+this.c.j(0)))},
$S:38}
A.ash.prototype={
$1(d){return this.a.iz(new A.AL("HTTP request failed, statusCode: "+B.j(this.b.status)+", "+this.c.j(0)))},
$S:2}
A.aLb.prototype={
$1(d){var x=this.a
x.z=!0
if(x.as){d.yN()
return}x.Q!==$&&B.bd()
x.Q=d
d.a2(0,x.ga9L(0))},
$S:729}
A.aLc.prototype={
$2(d,e){this.a.t9(B.c4("resolving an image stream completer"),d,this.b,!0,e)},
$S:30}
A.aLd.prototype={
$2(d,e){this.a.Ky(d)},
$S:226}
A.aLe.prototype={
$1(d){this.a.aPB(d)},
$S:730}
A.aLf.prototype={
$2(d,e){this.a.aPA(d,e)},
$S:116}
A.asv.prototype={
$2(d,e){this.a.t9(B.c4("resolving a single-frame image stream"),d,this.b,!0,e)},
$S:30};(function inheritance(){var x=a.inherit,w=a.inheritMany
x(A.AK,B.ho)
w(B.fZ,[A.asi,A.asj])
w(B.eK,[A.asg,A.ash,A.aLb,A.aLe])
w(B.hp,[A.a4S,A.Y1])
w(B.j9,[A.aLc,A.aLd,A.aLf,A.asv])
w(B.N,[A.Cu,A.AL])
x(A.aBT,B.kv)})()
B.fB(b.typeUniverse,JSON.parse('{"AK":{"ho":["b8H"],"ho.T":"b8H"},"a4S":{"hp":[]},"Cu":{"iE":[]},"b8H":{"ho":["b8H"]},"AL":{"c5":[]},"Y1":{"hp":[]}}'))
var y=(function rtii(){var x=B.aa
return{p:x("h_"),J:x("iE"),R:x("hp"),v:x("C<iF>"),u:x("C<~()>"),l:x("C<~(N,dv?)>"),a:x("ro"),P:x("br"),i:x("dg<AK>"),x:x("b7<af>"),Z:x("ap<af>"),X:x("N?"),H:x("~")}})();(function constants(){D.nE=new B.aX(C.z,1,C.H,-1)
D.dX=new B.i5(null,null,null,null)
D.wJ=new B.aj(61195,"MaterialIcons",null,!1)
D.eD=new B.cc(16,16,C.kF,null)
D.eG=new B.q(!0,null,null,null,null,null,null,C.aa,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)
D.ahG=new A.aBT(0,"never")})()};
(a=>{a["U7fABTWKra17b26cPyJGDVcOM9M="]=a.current})($__dart_deferred_initializers__);