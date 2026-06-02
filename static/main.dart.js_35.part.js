((a,b)=>{a[b]=a[b]||{}})(self,"$__dart_deferred_initializers__")
$__dart_deferred_initializers__.current=function(a,b,c,$){var J,A,B,C={
bup(){return new C.rN(null)},
rN:function rN(d){this.a=d},
P9:function P9(d,e,f,g,h,i,j,k){var _=this
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
aWo:function aWo(d){this.a=d},
aWn:function aWn(){},
aW3:function aW3(d,e){this.a=d
this.b=e},
aW5:function aW5(d){this.a=d},
aW6:function aW6(d){this.a=d},
aW7:function aW7(d){this.a=d},
aW8:function aW8(d){this.a=d},
aW9:function aW9(d){this.a=d},
aWa:function aWa(d){this.a=d},
aW4:function aW4(d){this.a=d},
aWb:function aWb(d,e){this.a=d
this.b=e},
aWf:function aWf(d){this.a=d},
aWe:function aWe(d){this.a=d},
aWg:function aWg(d,e){this.a=d
this.b=e},
aWh:function aWh(d,e){this.a=d
this.b=e},
aWi:function aWi(d){this.a=d},
aWd:function aWd(d){this.a=d},
aWj:function aWj(d,e){this.a=d
this.b=e},
aWk:function aWk(d){this.a=d},
aWc:function aWc(d){this.a=d},
aWl:function aWl(d){this.a=d},
aWm:function aWm(d){this.a=d},
EQ(d,e,f){return C.bp_(d,e,f)},
bp_(d,e,f){var x=0,w=A.o(y.y),v,u=2,t=[],s,r,q,p,o,n,m,l,k,j,i
var $async$EQ=A.k(function(g,h){if(g===1){t.push(h)
x=u}for(;;)switch(x){case 0:u=4
x=7
return A.e(A.co(),$async$EQ)
case 7:s=h
r=A.b3(J.r(s.a,"pending_referral_code"))
n=y.w
m=y.b
q=A.w(["email",d,"password",e,"full_name",f],n,m)
if(r!=null&&B.c.aK(r).length!==0)J.cl(q,"ref",B.c.aK(r))
l=A.aG("https://bigdogg-production.up.railway.app/api/v1/auth/register",0,null)
k=A.w(["Content-Type","application/json"],n,n)
x=8
return A.e(A.di(l,B.x.dJ(q,null),null,k),$async$EQ)
case 8:p=h
k=p
o=B.x.aW(0,A.bu(A.bt(k.e)).aE(0,k.w),null)
x=p.b===200?9:10
break
case 9:x=11
return A.e(J.mK(s,"pending_referral_code"),$async$EQ)
case 11:n=A.w(["success",!0,"data",o],n,m)
v=n
x=1
break
case 10:l=J.r(o,"detail")
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
return A.n($async$EQ,w)}},D,E,F,G,H
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
W(){var x=null,w=$.ao()
return new C.P9(new A.bE(B.ab,w),new A.bE(B.ab,w),new A.bE(B.ab,w),new A.bE(B.ab,w),A.hl(!0,x,!0,!0,x,x,!1),A.hl(!0,x,!0,!0,x,x,!1),A.hl(!0,x,!0,!0,x,x,!1),A.hl(!0,x,!0,!0,x,x,!1))}}
C.P9.prototype={
gP4(){var x=this.f,w=x.a.a,v=w.length>=8?1:0
if(B.c.p(w,A.cs("[A-Z]",!0,!1)))++v
if(B.c.p(x.a.a,A.cs("[0-9]",!0,!1)))++v
return B.c.p(x.a.a,A.cs('[!@#\\$%^&*(),.?":{}|<>]',!0,!1))?v+1:v},
ga3z(){switch(this.gP4()){case 1:return B.z
case 2:return G.ak
case 3:return D.a2I
case 4:return B.C
default:return B.w}},
gaD1(){var x=this
switch(x.gP4()){case 1:return x.ax?"Zwak":"Weak"
case 2:return x.ax?"Matig":"Fair"
case 3:return x.ax?"Goed":"Good"
case 4:return x.ax?"Sterk":"Strong"
default:return""}},
af(){var x=this
x.ap()
x.f.a2(0,new C.aWo(x))
x.xG()},
xG(){var x=0,w=A.o(y.v),v,u=this,t,s,r
var $async$xG=A.k(function(d,e){if(d===1)return A.l(e,w)
for(;;)switch(x){case 0:x=3
return A.e(A.co(),$async$xG)
case 3:t=e
s=A.b3(J.r(t.a,"pending_signup_email"))
r=B.c.aK(s==null?"":s)
if(r.length===0){x=1
break}x=4
return A.e(t.H(0,"pending_signup_email"),$async$xG)
case 4:if(u.c==null){x=1
break}u.t(new C.aW3(u,r))
case 1:return A.m(v,w)}})
return A.n($async$xG,w)},
l(){var x=this,w=x.d,v=w.N$=$.ao()
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
x.ao()},
ze(){var x=0,w=A.o(y.v),v,u=this,t,s,r,q
var $async$ze=A.k(function(d,e){if(d===1)return A.l(e,w)
for(;;)switch(x){case 0:q=u.d
if(B.c.aK(q.a.a).length===0){u.t(new C.aW5(u))
x=1
break}t=u.f
s=t.a.a
if(!(s.length>=8&&B.c.p(s,A.cs("[A-Z]",!0,!1))&&B.c.p(t.a.a,A.cs("[0-9]",!0,!1)))){u.t(new C.aW6(u))
x=1
break}if(t.a.a!==u.r.a.a){u.t(new C.aW7(u))
x=1
break}u.t(new C.aW8(u))
x=3
return A.e(C.EQ(B.c.aK(u.e.a.a),B.c.aK(t.a.a),B.c.aK(q.a.a)),$async$ze)
case 3:r=e
u.t(new C.aW9(u))
if(J.r(r,"success")){q=u.c
if(q!=null)A.dr(null,null,!1,null,new C.aWa(u),q,null,!0,!0,y.b)}else u.t(new C.aWb(u,r))
case 1:return A.m(v,w)}})
return A.n($async$ze,w)},
G(a1){var x,w,v,u,t,s,r,q,p,o,n,m,l,k,j,i=this,h=null,g="Account aanmaken",f=A.Y(a1).ax.a===B.b_,e=y.x,d=A.bB(a1,h,e).w.f.d,a0=A.fJ(0,A.B(h,h,B.h,B.p,h,h,h,h,h,h,h,h,h,h),h,h,0,h,0,5)
e=A.bB(a1,h,e).w
x=A.a0(31,B.p.m()>>>16&255,B.p.m()>>>8&255,B.p.m()&255)
w=A.D(6)
v=A.aw(A.a0(102,B.p.m()>>>16&255,B.p.m()>>>8&255,B.p.m()&255),1)
u=y.u
w=A.Z(A.a([A.cY(h,A.B(h,A.c(i.ax?"EN":"NL",h,h,h,h,B.h9,h,h,h),B.h,h,h,new A.L(x,h,v,w,h,h,B.m),h,h,h,h,B.eu,h,h,h),B.r,!1,h,h,h,h,h,h,h,h,h,h,h,h,h,h,new C.aWf(i),h,h,h,h,h,h)],u),B.j,B.eW,B.f,0)
v=A.k4("assets/images/logo.png",h,160,160)
x=f?B.kT:B.i
t=A.D(16)
s=A.aw(f?B.nY:B.w,1)
r=A.a([new A.bG(0,B.af,A.a0(B.e.am(255*(f?0.3:0.08)),B.B.m()>>>16&255,B.B.m()>>>8&255,B.B.m()&255),B.i0,32)],y.c)
q=i.ax?g:"Create your account"
q=A.c(q,h,h,h,h,A.aH(h,h,f?B.a1:B.l,h,h,h,h,h,h,h,h,24,h,h,B.E,h,h,!0,h,-0.5,h,h,h,h,h,h),h,h,h)
p=i.ax?"30 dagen gratis proberen":"Start your 30-day free trial"
q=A.a([q,B.av,A.c(p,h,h,h,h,A.aH(h,h,f?B.o8:B.G,h,h,h,h,h,h,h,h,14,h,h,h,h,h,!0,h,h,h,h,h,h,h,h),h,h,h),B.aR],u)
p=i.ay
if(p!=null){o=A.D(8)
q.push(A.B(h,A.c(p,h,h,h,h,B.mM,h,h,h),B.h,h,h,new A.L(B.cP,h,h,o,h,h,B.m),h,h,h,B.es,B.aQ,h,h,h))}q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),i.d,h,h,h,h,h,2,A.by(h,h,h,h,h,h,h,h,!0,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,i.ax?"Volledige naam":"Full name",!0,!0,!1,h,h,h,h,h,h,h,h,h,h,h,h,h,h),B.r,!0,h,!0,h,!1,i.w,B.R,h,h,h,h,h,h,h,h,1,h,h,!1,"\u2022",h,h,h,new C.aWg(i,a1),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.cK,h,h))
q.push(B.bB)
q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),i.e,h,h,h,h,h,2,D.Va,B.r,!0,h,!0,h,!1,i.x,B.R,h,h,h,h,B.f2,h,h,h,1,h,h,!1,"\u2022",h,h,h,new C.aWh(i,a1),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.cK,h,h))
q.push(B.bB)
p=i.f
o=i.ax?"Wachtwoord":"Password"
n=i.as
q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),p,h,h,h,h,h,2,A.by(h,h,h,h,h,h,h,h,!0,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,o,!0,!0,!1,h,h,h,h,h,h,h,h,new A.lV(!0,A.cw(h,h,A.bN(n?B.e3:B.e2,B.G,h,h),h,h,new C.aWi(i),h,h,h,h),h),h,h,h,h,h),B.r,!0,h,!0,h,!1,i.y,B.R,h,h,h,h,h,h,h,h,1,h,h,n,"\u2022",h,h,h,new C.aWj(i,a1),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.cK,h,h))
if(p.a.a.length!==0){o=y.l
m=J.ji(4,o)
for(l=0;l<4;++l){n=l<3?4:0
k=l<i.gP4()?i.ga3z():B.w
j=new A.b2(2,2)
m[l]=new A.h2(1,B.fC,A.B(h,h,B.h,h,h,new A.L(k,h,h,new A.cW(j,j,j,j),h,h,B.m),h,4,h,new A.a6(0,0,n,0),h,h,h,h),h)}o=A.ab(m,o)
o.push(B.a0)
o.push(A.c(i.gaD1(),h,h,h,h,A.aH(h,h,i.ga3z(),h,h,h,h,h,h,h,h,11,h,h,B.Q,h,h,!0,h,h,h,h,h,h,h,h),h,h,h))
o=A.Z(o,B.j,B.d,B.f,0)
n=p.a.a
k=i.ax?"Minimaal 8 tekens":"At least 8 characters"
k=i.Fu(n.length>=8,k)
n=B.c.p(p.a.a,A.cs("[A-Z]",!0,!1))
n=i.Fu(n,i.ax?"Een hoofdletter":"One uppercase letter")
j=B.c.p(p.a.a,A.cs("[0-9]",!0,!1))
j=i.Fu(j,i.ax?"Een cijfer":"One number")
p=B.c.p(p.a.a,A.cs('[!@#\\$%^&*(),.?":{}|<>]',!0,!1))
B.b.I(q,A.a([B.F,o,B.F,k,n,j,i.Fu(p,i.ax?"Speciaal teken (optioneel)":"Special character (optional)")],u))}q.push(B.bB)
p=i.ax?"Wachtwoord bevestigen":"Confirm password"
o=i.at
q.push(A.bQ(h,B.S,!1,h,!0,B.n,h,A.bS(),i.r,h,h,h,h,h,2,A.by(h,h,h,h,h,h,h,h,!0,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,h,p,!0,!0,!1,h,h,h,h,h,h,h,h,new A.lV(!0,A.cw(h,h,A.bN(o?B.e3:B.e2,B.G,h,h),h,h,new C.aWk(i),h,h,h,h),h),h,h,h,h,h),B.r,!0,h,!0,h,!1,i.z,B.R,h,h,h,h,h,h,h,h,1,h,h,o,"\u2022",h,h,h,new C.aWl(i),h,!1,h,h,!1,h,!0,h,B.N,h,h,h,h,h,h,h,h,h,h,h,h,!0,B.K,h,B.Y,h,B.h5,h,h))
q.push(B.aR)
p=i.Q
o=p?h:i.gaAt()
if(p)p=B.h2
else p=A.c(i.ax?g:"Create account",h,h,h,h,h,h,h,h)
q.push(A.b1(A.bZ(p,o,h),h,1/0))
q.push(B.y)
q.push(A.bH(A.ca(A.c(i.ax?"Al een account? Inloggen":"Already have an account? Sign in",h,h,h,h,h,h,h,h),new C.aWm(a1),h),h,h))
return A.fu(h,h,A.f1(B.bu,A.a([a0,A.b1(A.dm(new A.cH(new A.an(0,1/0,e.a.b-d,1/0),new A.A6(A.G(A.a([B.cr,new A.a9(B.j8,w,h),B.F,v,B.y,A.B(h,new A.a9(B.ew,A.G(q,B.q,B.d,B.I),h),B.h,h,B.iD,new A.L(x,h,s,t,r,h,B.m),h,h,h,B.j8,h,h,h,420),B.cr],u),B.j,B.b4,B.f),h),h),h,B.r,new A.a6(0,0,0,d),h,B.a8),1/0,1/0)],u),B.n,B.b7,h),h,!0)},
Fu(d,e){var x=null,w=d?B.c4:E.wD
w=A.bN(w,d?B.C:B.aq,x,14)
return new A.a9(H.vr,A.Z(A.a([w,B.aX,A.c(e,x,x,x,x,A.aH(x,x,d?B.C:B.aq,x,x,x,x,x,x,x,x,11,x,x,x,x,x,!0,x,x,x,x,x,x,x,x),x,x,x)],y.u),B.j,B.d,B.f,0),x)}}
var z=a.updateTypes(["al<~>()","kD(S)"])
C.aWo.prototype={
$0(){return this.a.t(new C.aWn())},
$S:0}
C.aWn.prototype={
$0(){},
$S:0}
C.aW3.prototype={
$0(){this.a.e.scn(0,this.b)},
$S:0}
C.aW5.prototype={
$0(){var x=this.a
return x.ay=x.ax?"Vul je naam in":"Please enter your name"},
$S:0}
C.aW6.prototype={
$0(){var x=this.a
return x.ay=x.ax?"Wachtwoord moet minimaal 8 tekens, een hoofdletter en een cijfer bevatten":"Password must be at least 8 characters with one uppercase letter and one number"},
$S:0}
C.aW7.prototype={
$0(){var x=this.a
return x.ay=x.ax?"Wachtwoorden komen niet overeen":"Passwords do not match"},
$S:0}
C.aW8.prototype={
$0(){var x=this.a
x.Q=!0
x.ay=null},
$S:0}
C.aW9.prototype={
$0(){return this.a.Q=!1},
$S:0}
C.aWa.prototype={
$1(d){var x,w=null,v=this.a,u=v.ax,t=A.c(u?"Bevestig je e-mail":"Confirm your email",w,w,w,w,w,w,w,w)
v=B.c.aK(v.e.a.a)
x="We hebben een bevestigingsmail gestuurd naar "+v+". Klik op de link om je account te activeren."
v="We sent a confirmation email to "+v+". Click the link to activate your account."
v=A.c(u?x:v,w,w,w,w,w,w,w,w)
return F.el(A.a([A.bZ(A.c(u?"Naar inloggen":"Go to login",w,w,w,w,w,w,w,w),new C.aW4(d),w)],y.u),v,w,t)},
$S:z+1}
C.aW4.prototype={
$0(){var x=this.a
A.aQ(x,!1).aU(null)
A.ei(x).dQ(0,"/login",null)},
$S:0}
C.aWb.prototype={
$0(){return this.a.ay=J.r(this.b,"message")},
$S:0}
C.aWf.prototype={
$0(){var x=this.a
return x.t(new C.aWe(x))},
$S:0}
C.aWe.prototype={
$0(){var x=this.a
return x.ax=!x.ax},
$S:0}
C.aWg.prototype={
$1(d){return A.uY(this.b).wo(this.a.x)},
$S:10}
C.aWh.prototype={
$1(d){return A.uY(this.b).wo(this.a.y)},
$S:10}
C.aWi.prototype={
$0(){var x=this.a
return x.t(new C.aWd(x))},
$S:0}
C.aWd.prototype={
$0(){var x=this.a
return x.as=!x.as},
$S:0}
C.aWj.prototype={
$1(d){return A.uY(this.b).wo(this.a.z)},
$S:10}
C.aWk.prototype={
$0(){var x=this.a
return x.t(new C.aWc(x))},
$S:0}
C.aWc.prototype={
$0(){var x=this.a
return x.at=!x.at},
$S:0}
C.aWl.prototype={
$1(d){return this.a.ze()},
$S:10}
C.aWm.prototype={
$0(){return A.ei(this.a).dQ(0,"/login",null)},
$S:0};(function installTearOffs(){var x=a._instance_0u
x(C.P9.prototype,"gaAt","ze",0)})();(function inheritance(){var x=a.inherit,w=a.inheritMany
x(C.rN,A.a_)
x(C.P9,A.a3)
w(A.fZ,[C.aWo,C.aWn,C.aW3,C.aW5,C.aW6,C.aW7,C.aW8,C.aW9,C.aW4,C.aWb,C.aWf,C.aWe,C.aWi,C.aWd,C.aWk,C.aWc,C.aWm])
w(A.eK,[C.aWa,C.aWg,C.aWh,C.aWj,C.aWl])})()
A.fB(b.typeUniverse,JSON.parse('{"rN":{"a_":[],"h":[]},"P9":{"a3":["rN"]}}'))
var y={c:A.aa("C<bG>"),u:A.aa("C<h>"),y:A.aa("ah<p,@>"),x:A.aa("hq"),w:A.aa("p"),l:A.aa("h"),b:A.aa("@"),v:A.aa("~")};(function constants(){D.Va=new A.oO(null,null,null,"Email",null,null,null,null,null,null,null,null,null,null,null,null,!0,!0,!1,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,!0,null,null,null,null)
D.NW=new A.H(1,1,0.9529411764705882,0.8784313725490196,B.o)
D.Oo=new A.H(1,1,0.8784313725490196,0.6980392156862745,B.o)
D.OD=new A.H(1,1,0.8,0.5019607843137255,B.o)
D.NG=new A.H(1,1,0.7176470588235294,0.30196078431372547,B.o)
D.O6=new A.H(1,1,0.6549019607843137,0.14901960784313725,B.o)
D.Os=new A.H(1,0.984313725490196,0.5490196078431373,0,B.o)
D.O3=new A.H(1,0.9607843137254902,0.48627450980392156,0,B.o)
D.Or=new A.H(1,0.9372549019607843,0.4235294117647059,0,B.o)
D.NP=new A.H(1,0.9019607843137255,0.3176470588235294,0,B.o)
D.a2D=new A.dN([50,D.NW,100,D.Oo,200,D.OD,300,D.NG,400,D.O6,500,E.uH,600,D.Os,700,D.O3,800,D.Or,900,D.NP],A.aa("dN<x,H>"))
D.a2I=new A.I1(D.a2D,1,1,0.596078431372549,0,B.o)})()};
(a=>{a["8t2uH3rBwuzeuzdUOZjCfogov0Q="]=a.current})($__dart_deferred_initializers__);