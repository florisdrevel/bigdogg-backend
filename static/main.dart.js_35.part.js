((a,b)=>{a[b]=a[b]||{}})(self,"$__dart_deferred_initializers__")
$__dart_deferred_initializers__.current=function(a,b,c,$){var J,A,B,C={
buK(){return new C.rN(null)},
rN:function rN(d){this.a=d},
Pd:function Pd(d,e,f,g,h,i,j,k){var _=this
_.d=d
_.e=e
_.f=f
_.r=g
_.w=h
_.x=i
_.y=j
_.z=k
_.Q=!1
_.ax=_.at=_.as=!0
_.c=_.a=_.ay=null},
aWI:function aWI(d){this.a=d},
aWH:function aWH(){},
aWn:function aWn(d,e){this.a=d
this.b=e},
aWp:function aWp(d){this.a=d},
aWq:function aWq(d){this.a=d},
aWr:function aWr(d){this.a=d},
aWs:function aWs(d){this.a=d},
aWt:function aWt(d){this.a=d},
aWu:function aWu(d){this.a=d},
aWo:function aWo(d){this.a=d},
aWv:function aWv(d,e){this.a=d
this.b=e},
aWz:function aWz(d){this.a=d},
aWy:function aWy(d){this.a=d},
aWA:function aWA(d,e){this.a=d
this.b=e},
aWB:function aWB(d,e){this.a=d
this.b=e},
aWC:function aWC(d){this.a=d},
aWx:function aWx(d){this.a=d},
aWD:function aWD(d,e){this.a=d
this.b=e},
aWE:function aWE(d){this.a=d},
aWw:function aWw(d){this.a=d},
aWF:function aWF(d){this.a=d},
aWG:function aWG(d){this.a=d},
ER(d,e,f){return C.bpk(d,e,f)},
bpk(d,e,f){var x=0,w=A.o(y.y),v,u=2,t=[],s,r,q,p,o,n,m,l,k,j,i
var $async$ER=A.k(function(g,h){if(g===1){t.push(h)
x=u}for(;;)switch(x){case 0:u=4
x=7
return A.e(A.cu(),$async$ER)
case 7:s=h
r=A.b5(J.t(s.a,"pending_referral_code"))
n=y.w
m=y.b
q=A.w(["email",d,"password",e,"full_name",f],n,m)
if(r!=null&&B.c.aK(r).length!==0)J.cl(q,"ref",B.c.aK(r))
l=A.aG("https://bigdogg-production.up.railway.app/api/v1/auth/register",0,null)
k=A.w(["Content-Type","application/json"],n,n)
x=8
return A.e(A.di(l,B.x.dJ(q,null),null,k),$async$ER)
case 8:p=h
k=p
o=B.x.aW(0,A.bu(A.bt(k.e)).aE(0,k.w),null)
x=p.b===200?9:10
break
case 9:x=11
return A.e(J.mL(s,"pending_referral_code"),$async$ER)
case 11:n=A.w(["success",!0,"data",o],n,m)
v=n
x=1
break
case 10:l=J.t(o,"detail")
n=A.w(["success",!1,"message",l==null?"Registration failed":l],n,m)
v=n
x=1
break
u=2
x=6
break
case 4:u=3
i=t.pop()
n=A.w(["success",!1,"message","Connection error. Please try again."],y.w,y.b)
v=n
x=1
break
x=6
break
case 3:x=2
break
case 6:case 1:return A.m(v,w)
case 2:return A.l(t.at(-1),w)}})
return A.n($async$ER,w)}},D,E,F,G,H
J=c[1]
A=c[0]
B=c[2]
C=a.updateHolder(c[7],C)
D=c[65]
E=c[57]
F=c[19]
G=c[50]
H=c[58]
C.rN.prototype={
V(){var x=null,w=$.an()
return new C.Pd(new A.bE(B.ab,w),new A.bE(B.ab,w),new A.bE(B.ab,w),new A.bE(B.ab,w),A.hn(!0,x,!0,!0,x,x,!1),A.hn(!0,x,!0,!0,x,x,!1),A.hn(!0,x,!0,!0,x,x,!1),A.hn(!0,x,!0,!0,x,x,!1))}}
C.Pd.prototype={
gPe(){var x=this.f,w=x.a.a,v=w.length>=8?1:0
if(B.c.p(w,A.cr("[A-Z]",!0,!1)))++v
if(B.c.p(x.a.a,A.cr("[0-9]",!0,!1)))++v
return B.c.p(x.a.a,A.cr('[!@#\\$%^&*(),.?":{}|<>]',!0,!1))?v+1:v},
ga3M(){switch(this.gPe()){case 1:return B.z
case 2:return G.ak
case 3:return D.a2I
case 4:return B.C
default:return B.w}},
gaDn(){var x=this
switch(x.gPe()){case 1:return x.ax?"Zwak":"Weak"
case 2:return x.ax?"Matig":"Fair"
case 3:return x.ax?"Goed":"Good"
case 4:return x.ax?"Sterk":"Strong"
default:return""}},
ae(){var x=this
x.ap()
x.f.a2(0,new C.aWI(x))
x.xK()},
xK(){var x=0,w=A.o(y.v),v,u=this,t,s,r
var $async$xK=A.k(function(d,e){if(d===1)return A.l(e,w)
for(;;)switch(x){case 0:x=3
return A.e(A.cu(),$async$xK)
case 3:t=e
s=A.b5(J.t(t.a,"pending_signup_email"))
r=B.c.aK(s==null?"":s)
if(r.length===0){x=1
break}x=4
return A.e(t.H(0,"pending_signup_email"),$async$xK)
case 4:if(u.c==null){x=1
break}u.t(new C.aWn(u,r))
case 1:return A.m(v,w)}})
return A.n($async$xK,w)},
l(){var x=this,w=x.d,v=w.N$=$.an()
w.J$=0
w=x.e
w.N$=v
w.J$=0
w=x.f
w.N$=v
w.J$=0
w=x.r
w.N$=v
w.J$=0
x.w.l()
x.x.l()
x.y.l()
x.z.l()
x.an()},
zg(){var x=0,w=A.o(y.v),v,u=this,t,s,r,q
var $async$zg=A.k(function(d,e){if(d===1)return A.l(e,w)
for(;;)switch(x){case 0:q=u.d
if(B.c.aK(q.a.a).length===0){u.t(new C.aWp(u))
x=1
break}t=u.f
s=t.a.a
if(!(s.length>=8&&B.c.p(s,A.cr("[A-Z]",!0,!1))&&B.c.p(t.a.a,A.cr("[0-9]",!0,!1)))){u.t(new C.aWq(u))
x=1
break}if(t.a.a!==u.r.a.a){u.t(new C.aWr(u))
x=1
break}u.t(new C.aWs(u))
x=3
return A.e(C.ER(B.c.aK(u.e.a.a),B.c.aK(t.a.a),B.c.aK(q.a.a)),$async$zg)
case 3:r=e
u.t(new C.aWt(u))
if(J.t(r,"success")){q=u.c
if(q!=null)A.dr(null,null,!1,null,new C.aWu(u),q,null,!0,!0,y.b)}else u.t(new C.aWv(u,r))
case 1:return A.m(v,w)}})
return A.n($async$zg,w)},
G(a1){var x,w,v,u,t,s,r,q,p,o,n,m,l,k,j,i=this,h=null,g="Account aanmaken",f=A.Y(a1).ax.a===B.b_,e=y.x,d=A.bB(a1,h,e).w.f.d,a0=A.fK(0,A.B(h,h,B.h,B.p,h,h,h,h,h,h,h,h,h,h),h,h,0,h,0,5)
e=A.bB(a1,h,e).w
x=A.a0(31,B.p.m()>>>16&255,B.p.m()>>>8&255,B.p.m()&255)
w=A.D(6)
v=A.aw(A.a0(102,B.p.m()>>>16&255,B.p.m()>>>8&255,B.p.m()&255),1)
u=y.u
w=A.Z(A.a([A.cY(h,A.B(h,A.c(i.ax?"EN":"NL",h,h,h,h,B.h9,h,h,h),B.h,h,h,new A.L(x,h,v,w,h,h,B.m),h,h,h,h,B.et,h,h,h),B.r,!1,h,h,h,h,h,h,h,h,h,h,h,h,h,h,new C.aWz(i),h,h,h,h,h,h)],u),B.j,B.eW,B.f,0)
v=A.k7("assets/images/logo.png",h,160,160)
x=f?B.kT:B.i
t=A.D(16)
s=A.aw(f?B.nY:B.w,1)
r=A.a([new A.bG(0,B.af,A.a0(B.e.am(255*(f?0.3:0.08)),B.B.m()>>>16&255,B.B.m()>>>8&255,B.B.m()&255),B.i1,32)],y.c)
q=i.ax?g:"Create your account"
q=A.c(q,h,h,h,h,A.aH(h,h,f?B.a1:B.l,h,h,h,h,h,h,h,h,24,h,h,B.E,h,h,!0,h,-0.5,h,h,h,h,h,h),h,h,h)
p=i.ax?"30 dagen gratis proberen":"Start your 30-day free trial"
q=A.a([q,B.av,A.c(p,h,h,h,h,A.aH(h,h,f?B.o8:B.G,h,h,h,h,h,h,h,h,14,h,h,h,h,h,!0,h,h,h,h,h,h,h,h),h,h,h),B.aR],u)
p=i.ay
if(p!=null){o=A.D(8)
q.push(A.B(h,A.c(p,h,h,h,h,B.mM,h,h,h),B.h,h,h,new A.L(B.cP,h,h,o,h,h,B.m),h,h,h,B.er,B.aQ,h,h,h))}q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),i.d,h,h,h,h,h,2,A.by(h,h,h,h,h,h,h,h,!0,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,i.ax?"Volledige naam":"Full name",!0,!0,!1,h,h,h,h,h,h,h,h,h,h,h,h,h,h),B.r,!0,h,!0,h,!1,i.w,B.R,h,h,h,h,h,h,h,h,1,h,h,!1,"\u2022",h,h,h,new C.aWA(i,a1),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.cK,h,h))
q.push(B.bB)
q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),i.e,h,h,h,h,h,2,D.Va,B.r,!0,h,!0,h,!1,i.x,B.R,h,h,h,h,B.f2,h,h,h,1,h,h,!1,"\u2022",h,h,h,new C.aWB(i,a1),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.cK,h,h))
q.push(B.bB)
p=i.f
o=i.ax?"Wachtwoord":"Password"
n=i.as
q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),p,h,h,h,h,h,2,A.by(h,h,h,h,h,h,h,h,!0,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,o,!0,!0,!1,h,h,h,h,h,h,h,h,new A.lW(!0,A.cw(h,h,A.bN(n?B.e3:B.e2,B.G,h,h),h,h,new C.aWC(i),h,h,h,h),h),h,h,h,h,h),B.r,!0,h,!0,h,!1,i.y,B.R,h,h,h,h,h,h,h,h,1,h,h,n,"\u2022",h,h,h,new C.aWD(i,a1),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.cK,h,h))
if(p.a.a.length!==0){o=y.l
m=J.jk(4,o)
for(l=0;l<4;++l){n=l<3?4:0
k=l<i.gPe()?i.ga3M():B.w
j=new A.b2(2,2)
m[l]=new A.h3(1,B.fC,A.B(h,h,B.h,h,h,new A.L(k,h,h,new A.cW(j,j,j,j),h,h,B.m),h,4,h,new A.a6(0,0,n,0),h,h,h,h),h)}o=A.aa(m,o)
o.push(B.a0)
o.push(A.c(i.gaDn(),h,h,h,h,A.aH(h,h,i.ga3M(),h,h,h,h,h,h,h,h,11,h,h,B.Q,h,h,!0,h,h,h,h,h,h,h,h),h,h,h))
o=A.Z(o,B.j,B.d,B.f,0)
n=p.a.a
k=i.ax?"Minimaal 8 tekens":"At least 8 characters"
k=i.Fy(n.length>=8,k)
n=B.c.p(p.a.a,A.cr("[A-Z]",!0,!1))
n=i.Fy(n,i.ax?"Een hoofdletter":"One uppercase letter")
j=B.c.p(p.a.a,A.cr("[0-9]",!0,!1))
j=i.Fy(j,i.ax?"Een cijfer":"One number")
p=B.c.p(p.a.a,A.cr('[!@#\\$%^&*(),.?":{}|<>]',!0,!1))
B.b.I(q,A.a([B.F,o,B.F,k,n,j,i.Fy(p,i.ax?"Speciaal teken (optioneel)":"Special character (optional)")],u))}q.push(B.bB)
p=i.ax?"Wachtwoord bevestigen":"Confirm password"
o=i.at
q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),i.r,h,h,h,h,h,2,A.by(h,h,h,h,h,h,h,h,!0,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,p,!0,!0,!1,h,h,h,h,h,h,h,h,new A.lW(!0,A.cw(h,h,A.bN(o?B.e3:B.e2,B.G,h,h),h,h,new C.aWE(i),h,h,h,h),h),h,h,h,h,h),B.r,!0,h,!0,h,!1,i.z,B.R,h,h,h,h,h,h,h,h,1,h,h,o,"\u2022",h,h,h,new C.aWF(i),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.h5,h,h))
q.push(B.aR)
p=i.Q
o=p?h:i.gaAM()
if(p)p=B.h2
else p=A.c(i.ax?g:"Create account",h,h,h,h,h,h,h,h)
q.push(A.b0(A.bZ(p,o,h),h,1/0))
q.push(B.y)
q.push(A.bH(A.ca(A.c(i.ax?"Al een account? Inloggen":"Already have an account? Sign in",h,h,h,h,h,h,h,h),new C.aWG(a1),h),h,h))
return A.fu(h,h,A.f2(B.bu,A.a([a0,A.b0(A.dm(new A.cH(new A.ao(0,1/0,e.a.b-d,1/0),new A.A6(A.G(A.a([B.cr,new A.a9(B.j8,w,h),B.F,v,B.y,A.B(h,new A.a9(B.ev,A.G(q,B.q,B.d,B.I),h),B.h,h,B.iE,new A.L(x,h,s,t,r,h,B.m),h,h,h,B.j8,h,h,h,420),B.cr],u),B.j,B.b4,B.f),h),h),h,B.r,new A.a6(0,0,0,d),h,B.a8),1/0,1/0)],u),B.n,B.b7,h),h,!0)},
Fy(d,e){var x=null,w=d?B.c4:E.wD
w=A.bN(w,d?B.C:B.aq,x,14)
return new A.a9(H.vr,A.Z(A.a([w,B.aX,A.c(e,x,x,x,x,A.aH(x,x,d?B.C:B.aq,x,x,x,x,x,x,x,x,11,x,x,x,x,x,!0,x,x,x,x,x,x,x,x),x,x,x)],y.u),B.j,B.d,B.f,0),x)}}
var z=a.updateTypes(["al<~>()","kF(S)"])
C.aWI.prototype={
$0(){return this.a.t(new C.aWH())},
$S:0}
C.aWH.prototype={
$0(){},
$S:0}
C.aWn.prototype={
$0(){this.a.e.scl(0,this.b)},
$S:0}
C.aWp.prototype={
$0(){var x=this.a
return x.ay=x.ax?"Vul je naam in":"Please enter your name"},
$S:0}
C.aWq.prototype={
$0(){var x=this.a
return x.ay=x.ax?"Wachtwoord moet minimaal 8 tekens, een hoofdletter en een cijfer bevatten":"Password must be at least 8 characters with one uppercase letter and one number"},
$S:0}
C.aWr.prototype={
$0(){var x=this.a
return x.ay=x.ax?"Wachtwoorden komen niet overeen":"Passwords do not match"},
$S:0}
C.aWs.prototype={
$0(){var x=this.a
x.Q=!0
x.ay=null},
$S:0}
C.aWt.prototype={
$0(){return this.a.Q=!1},
$S:0}
C.aWu.prototype={
$1(d){var x,w=null,v=this.a,u=v.ax,t=A.c(u?"Bevestig je e-mail":"Confirm your email",w,w,w,w,w,w,w,w)
v=B.c.aK(v.e.a.a)
x="We hebben een bevestigingsmail gestuurd naar "+v+". Klik op de link om je account te activeren."
v="We sent a confirmation email to "+v+". Click the link to activate your account."
v=A.c(u?x:v,w,w,w,w,w,w,w,w)
return F.el(A.a([A.bZ(A.c(u?"Naar inloggen":"Go to login",w,w,w,w,w,w,w,w),new C.aWo(d),w)],y.u),v,w,t)},
$S:z+1}
C.aWo.prototype={
$0(){var x=this.a
A.aQ(x,!1).aU(null)
A.ei(x).dE(0,"/login",null)},
$S:0}
C.aWv.prototype={
$0(){return this.a.ay=J.t(this.b,"message")},
$S:0}
C.aWz.prototype={
$0(){var x=this.a
return x.t(new C.aWy(x))},
$S:0}
C.aWy.prototype={
$0(){var x=this.a
return x.ax=!x.ax},
$S:0}
C.aWA.prototype={
$1(d){return A.uZ(this.b).ws(this.a.x)},
$S:10}
C.aWB.prototype={
$1(d){return A.uZ(this.b).ws(this.a.y)},
$S:10}
C.aWC.prototype={
$0(){var x=this.a
return x.t(new C.aWx(x))},
$S:0}
C.aWx.prototype={
$0(){var x=this.a
return x.as=!x.as},
$S:0}
C.aWD.prototype={
$1(d){return A.uZ(this.b).ws(this.a.z)},
$S:10}
C.aWE.prototype={
$0(){var x=this.a
return x.t(new C.aWw(x))},
$S:0}
C.aWw.prototype={
$0(){var x=this.a
return x.at=!x.at},
$S:0}
C.aWF.prototype={
$1(d){return this.a.zg()},
$S:10}
C.aWG.prototype={
$0(){return A.ei(this.a).dE(0,"/login",null)},
$S:0};(function installTearOffs(){var x=a._instance_0u
x(C.Pd.prototype,"gaAM","zg",0)})();(function inheritance(){var x=a.inherit,w=a.inheritMany
x(C.rN,A.a_)
x(C.Pd,A.a2)
w(A.h_,[C.aWI,C.aWH,C.aWn,C.aWp,C.aWq,C.aWr,C.aWs,C.aWt,C.aWo,C.aWv,C.aWz,C.aWy,C.aWC,C.aWx,C.aWE,C.aWw,C.aWG])
w(A.eK,[C.aWu,C.aWA,C.aWB,C.aWD,C.aWF])})()
A.fB(b.typeUniverse,JSON.parse('{"rN":{"a_":[],"h":[]},"Pd":{"a2":["rN"]}}'))
var y={c:A.ab("C<bG>"),u:A.ab("C<h>"),y:A.ab("ah<p,@>"),x:A.ab("hs"),w:A.ab("p"),l:A.ab("h"),b:A.ab("@"),v:A.ab("~")};(function constants(){D.Va=new A.oP(null,null,null,"Email",null,null,null,null,null,null,null,null,null,null,null,null,!0,!0,!1,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,!0,null,null,null,null)
D.NW=new A.H(1,1,0.9529411764705882,0.8784313725490196,B.o)
D.Oo=new A.H(1,1,0.8784313725490196,0.6980392156862745,B.o)
D.OD=new A.H(1,1,0.8,0.5019607843137255,B.o)
D.NG=new A.H(1,1,0.7176470588235294,0.30196078431372547,B.o)
D.O6=new A.H(1,1,0.6549019607843137,0.14901960784313725,B.o)
D.Os=new A.H(1,0.984313725490196,0.5490196078431373,0,B.o)
D.O3=new A.H(1,0.9607843137254902,0.48627450980392156,0,B.o)
D.Or=new A.H(1,0.9372549019607843,0.4235294117647059,0,B.o)
D.NP=new A.H(1,0.9019607843137255,0.3176470588235294,0,B.o)
D.a2D=new A.dN([50,D.NW,100,D.Oo,200,D.OD,300,D.NG,400,D.O6,500,E.uH,600,D.Os,700,D.O3,800,D.Or,900,D.NP],A.ab("dN<x,H>"))
D.a2I=new A.I5(D.a2D,1,1,0.596078431372549,0,B.o)})()};
(a=>{a["KRkV6lgIaqvyt7eo7J9KjLPPYTk="]=a.current})($__dart_deferred_initializers__);