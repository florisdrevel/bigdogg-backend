((a,b)=>{a[b]=a[b]||{}})(self,"$__dart_deferred_initializers__")
$__dart_deferred_initializers__.current=function(a,b,c,$){var J,A,B,H,F,I,K,G,L,M,E,N,O,C={
buu(d){return new C.rI(d,null)},
rI:function rI(d,e){this.c=d
this.a=e},
a7x:function a7x(){var _=this
_.d=null
_.e=!0
_.f=!1
_.c=_.a=_.w=_.r=null},
aVW:function aVW(d){this.a=d},
aVX:function aVX(d,e){this.a=d
this.b=e},
aVY:function aVY(d,e){this.a=d
this.b=e},
aVZ:function aVZ(d){this.a=d},
aVN:function aVN(d){this.a=d},
aVO:function aVO(d,e){this.a=d
this.b=e},
aVP:function aVP(d){this.a=d},
aVQ:function aVQ(d,e){this.a=d
this.b=e},
aVR:function aVR(d){this.a=d},
aVU:function aVU(){},
aVV:function aVV(){},
aVS:function aVS(d){this.a=d},
aVT:function aVT(d){this.a=d}},D,P
J=c[1]
A=c[0]
B=c[2]
H=c[37]
F=c[35]
I=c[46]
K=c[41]
G=c[30]
L=c[23]
M=c[14]
E=c[55]
N=c[18]
O=c[64]
C=a.updateHolder(c[10],C)
D=c[63]
P=c[29]
C.rI.prototype={
V(){return new C.a7x()}}
C.a7x.prototype={
ae(){this.ap()
this.Fq()},
Fq(){var w=0,v=A.o(x.v),u=1,t=[],s=this,r,q,p,o,n
var $async$Fq=A.k(function(d,e){if(d===1){t.push(e)
w=u}for(;;)switch(w){case 0:s.t(new C.aVW(s))
u=3
w=6
return A.e(A.d8(A.aG(y.a+s.a.c,0,null),null),$async$Fq)
case 6:r=e
if(r.b===200){p=r
q=x.y.a(B.x.aW(0,A.bu(A.bt(p.e)).aE(0,p.w),null))
if(s.c!=null)s.t(new C.aVX(s,q))}else if(s.c!=null)s.t(new C.aVY(s,r))
u=1
w=5
break
case 3:u=2
n=t.pop()
if(s.c!=null)s.t(new C.aVZ(s))
w=5
break
case 2:w=1
break
case 5:return A.m(null,v)
case 1:return A.l(t.at(-1),v)}})
return A.n($async$Fq,v)},
xo(d){return this.ajR(d)},
ajR(d){var w=0,v=A.o(x.v),u,t=2,s=[],r=this,q,p,o,n,m,l
var $async$xo=A.k(function(e,f){if(e===1){s.push(f)
w=t}for(;;)switch(w){case 0:if(r.f){w=1
break}r.t(new C.aVN(r))
t=4
w=7
return A.e(A.di(A.aG(y.a+r.a.c+"/"+d,0,null),null,null,null),$async$xo)
case 7:q=f
if(q.b===200){n=q
p=x.y.a(B.x.aW(0,A.bu(A.bt(n.e)).aE(0,n.w),null))
if(r.c!=null)r.t(new C.aVO(r,p))}else{o=new C.aVP(q).$0()
if(r.c!=null)r.t(new C.aVQ(r,o))}t=2
w=6
break
case 4:t=3
l=s.pop()
if(r.c!=null)r.t(new C.aVR(r))
w=6
break
case 3:w=2
break
case 6:case 1:return A.m(u,v)
case 2:return A.l(s.at(-1),v)}})
return A.n($async$xo,v)},
G(d){var w=null
return A.fu(w,B.a1,A.fN(!0,A.bH(A.dm(new A.cH(D.L1,this.akF(0),w),w,B.r,B.li,w,B.a8),w,w),!0,B.a9,!0,!0),w,w)},
akF(d){var w,v,u,t,s,r,q,p,o,n,m,l=this,k=null
if(l.e)return D.a4a
w=l.r
if(w!=null&&l.d==null)return l.xB(A.G(A.a([D.TX,B.y,A.c(w,k,k,k,k,D.aaS,B.a3,k,k)],x.u),B.j,B.d,B.f))
w=l.d
w.toString
v=l.avH(w)
u=J.U(w)
t=u.h(w,"quote_date")
t=t==null?k:J.a3(t)
t=l.EJ("Offertedatum",t==null?"-":t)
s=u.h(w,"valid_until")
s=s==null?k:J.a3(s)
s=l.EJ("Geldig tot",s==null?"-":s)
r=u.h(w,"client_name")
if(r==null)r=u.h(w,"client_company")
q=x.u
r=A.a([t,s,l.EJ("T.a.v.",J.a3(r==null?"-":r))],q)
t=u.h(w,"notes")
if(J.a3(t==null?"":t).length!==0)r.push(l.EJ("Opmerking",J.a3(u.h(w,"notes"))))
t=l.xB(A.G(r,B.p,B.d,B.f))
s=l.awK(w)
r=u.h(w,"subtotal_ex_btw")
p=A.du(J.a3(r==null?0:r))
if(p==null)p=0
r=u.h(w,"btw_amount")
o=A.du(J.a3(r==null?0:r))
if(o==null)o=0
w=u.h(w,"total_incl_btw")
n=A.du(J.a3(w==null?0:w))
if(n==null)n=0
w=A.a([v,B.D,t,B.D,s,B.D,l.xB(A.G(A.a([l.a2P("Subtotaal ex BTW","\u20ac"+B.e.S(p,2)),l.a2P("BTW","\u20ac"+B.e.S(o,2)),E.dX,l.a2Q("Totaal incl BTW","\u20ac"+B.e.S(n,2),!0)],q),B.j,B.d,B.f)),B.aR],q)
if(l.w==null)w.push(l.ajS())
v=l.w
if(v!=null){m=v==="accepted"
v=m?B.c0:B.cP
u=A.D(12)
t=m?B.C:B.z
t=A.aw(A.a0(102,t.m()>>>16&255,t.m()>>>8&255,t.m()&255),1)
s=m?B.c4:O.wt
s=A.bN(s,m?B.C:B.z,k,32)
r=m?"Offerte geaccepteerd":"Offerte afgewezen"
r=A.c(r,k,k,k,k,A.aH(k,k,m?B.C:B.z,k,k,k,k,k,k,k,k,15,k,k,B.E,k,k,!0,k,k,k,k,k,k,k,k),k,k,k)
w.push(A.B(k,A.Z(A.a([s,H.br,A.a1(A.G(A.a([r,B.av,A.c(m?"Bedankt! De afzender is op de hoogte gebracht.":"De afzender is op de hoogte gebracht.",k,k,k,k,B.aU,k,k,k)],q),B.p,B.d,B.f),1)],q),B.j,B.d,B.f,0),B.h,k,k,new A.M(v,k,t,u,k,k,B.m),k,k,k,k,B.N,k,k,k))}w.push(B.aR)
w.push(A.bH(A.c("Verzonden via BigDogg \xb7 bigdogg.nl",k,k,k,k,A.aH(k,k,B.j_,k,k,k,k,k,k,k,k,11,k,k,k,k,k,!0,k,k,k,k,k,k,k,k),k,k,k),k,k))
return A.G(w,B.aN,B.d,B.f)},
avH(d){var w,v,u,t=null,s=J.U(d),r=s.h(d,"from_logo_url"),q=r==null?t:J.a3(r)
r=s.h(d,"from_business")
w=r==null?t:J.a3(r)
if(w==null)w=""
r=A.D(8)
v=A.aw(B.w,1)
u=q!=null&&q.length!==0?A.qz(A.D(7),M.beP(q,new C.aVU(),B.nM),B.bP):D.x2
r=A.B(t,u,B.h,t,t,new A.M(B.a1,t,v,r,t,t,B.m),t,56,t,t,t,t,t,56)
v=A.c("OFFERTE",t,t,t,t,A.aH(t,t,B.q,t,t,t,t,t,t,t,t,11,t,t,B.E,t,t,!0,t,1.5,t,t,t,t,t,t),t,t,t)
s=s.h(d,"quote_number")
s=s==null?t:J.a3(s)
u=x.u
return this.xB(A.Z(A.a([r,D.a8c,A.a1(A.G(A.a([v,B.bf,A.c(s==null?"":s,t,t,t,t,B.rw,t,t,t),B.bf,A.c("Van "+w,t,t,t,t,B.aU,t,t,t)],u),B.p,B.d,B.f),1)],u),B.j,B.d,B.f,0))},
awK(d){var w,v=x.d.a(J.t(d,"lines"))
if(v==null)v=[]
w=A.a([D.afQ,B.F],x.u)
B.b.I(w,J.dY(v,new C.aVV(),x.l))
return this.xB(A.G(w,B.p,B.d,B.f))},
ajS(){var w,v=this,u=null,t=A.a([],x.u),s=v.r
if(s!=null){w=A.D(8)
t.push(new A.a9(B.eT,A.B(u,A.c(s,u,u,u,u,I.eG,u,u,u),B.h,u,u,new A.M(B.cP,u,u,w,u,u,B.m),u,u,u,u,B.c2,u,u,u),u))}s=v.f
w=s?u:new C.aVS(v)
s=s?E.eC:D.T7
t.push(A.b0(L.fl(s,D.afZ,w,A.cE(u,u,B.C,u,u,u,u,u,u,B.i,u,u,u,u,u,u,u,u,u,u)),52,1/0))
t.push(B.aF)
s=v.f?u:new C.aVT(v)
t.push(A.b0(N.no(D.UG,D.ag3,s,A.l5(u,u,u,u,u,u,u,u,u,B.z,u,u,u,u,u,E.nE,u,u,u,u)),48,1/0))
return A.G(t,B.j,B.d,B.f)},
xB(d){var w=null,v=A.D(12)
return A.B(w,d,B.h,w,w,new A.M(B.i,w,A.aw(B.w,1),v,w,w,B.m),w,w,w,w,B.a5,w,w,w)},
EJ(d,e){var w=null
return new A.a9(B.cF,A.Z(A.a([A.b0(A.c(d,w,w,w,w,F.az,w,w,w),w,110),A.a1(A.c(e,w,w,w,w,E.eF,w,w,w),1)],x.u),B.p,B.d,B.f,0),w)},
a2Q(d,e,f){var w=null,v=f?B.am:B.P,u=f?16:14,t=A.aH(w,w,B.l,w,w,w,w,w,w,w,w,u,w,w,v,w,w,!0,w,w,w,w,w,w,w,w)
return new A.a9(B.cF,A.Z(A.a([A.a1(A.c(d,w,w,w,w,t,w,w,w),1),A.c(e,w,w,w,w,t,w,w,w)],x.u),B.j,B.d,B.f,0),w)},
a2P(d,e){return this.a2Q(d,e,!1)}}
var z=a.updateTypes([])
C.aVW.prototype={
$0(){var w=this.a
w.e=!0
w.r=null},
$S:0}
C.aVX.prototype={
$0(){var w="status",v="accepted",u="declined",t=this.a,s=t.d=this.b,r=J.U(s)
if(J.d(r.h(s,w),v)||J.d(r.h(s,w),"converted"))s=v
else s=J.d(r.h(s,w),u)?u:null
t.w=s
t.e=!1},
$S:0}
C.aVY.prototype={
$0(){var w=this.a
w.r=this.b.b===404?"Deze offerte bestaat niet of is verwijderd.":"Kon offerte niet laden."
w.e=!1},
$S:0}
C.aVZ.prototype={
$0(){var w=this.a
w.r="Geen verbinding."
w.e=!1},
$S:0}
C.aVN.prototype={
$0(){return this.a.f=!0},
$S:0}
C.aVO.prototype={
$0(){var w=this.a
w.w=J.t(this.b,"status")
w.f=!1},
$S:0}
C.aVP.prototype={
$0(){var w,v
try{w=this.a
w=J.t(x.B.a(B.x.aW(0,A.bu(A.bt(w.e)).aE(0,w.w),null)),"detail")
w=w==null?null:J.a3(w)
return w}catch(v){return null}},
$S:254}
C.aVQ.prototype={
$0(){var w=this.a,v=this.b
w.r=v==null?"Er ging iets mis. Probeer het opnieuw.":v
w.f=!1},
$S:0}
C.aVR.prototype={
$0(){var w=this.a
w.r="Geen verbinding."
w.f=!1},
$S:0}
C.aVU.prototype={
$3(d,e,f){return D.x2},
$S:262}
C.aVV.prototype={
$1(d){var w,v=null,u=J.U(d),t=u.h(d,"line_total_ex_btw"),s=A.du(J.a3(t==null?0:t))
if(s==null)s=0
t=u.h(d,"description")
t=t==null?v:J.a3(t)
w=x.u
return new A.a9(G.es,A.Z(A.a([A.a1(A.G(A.a([A.c(t==null?"":t,v,v,v,v,E.eF,v,v,v),A.c(A.j(u.h(d,"quantity"))+"x \u20ac"+A.j(u.h(d,"unit_price_ex_btw"))+" ("+A.j(u.h(d,"btw_rate"))+"% BTW)",v,v,v,v,F.az,v,v,v)],w),B.p,B.d,B.f),1),A.c("\u20ac"+B.e.S(s,2),v,v,v,v,B.eE,v,v,v)],w),B.p,B.d,B.f,0),v)},
$S:41}
C.aVS.prototype={
$0(){return this.a.xo("accept")},
$S:0}
C.aVT.prototype={
$0(){return this.a.xo("decline")},
$S:0};(function inheritance(){var w=a.inherit,v=a.inheritMany
w(C.rI,A.a_)
w(C.a7x,A.a2)
v(A.h_,[C.aVW,C.aVX,C.aVY,C.aVZ,C.aVN,C.aVO,C.aVP,C.aVQ,C.aVR,C.aVS,C.aVT])
v(A.eK,[C.aVU,C.aVV])})()
A.fB(b.typeUniverse,JSON.parse('{"rI":{"a_":[],"h":[]},"a7x":{"a2":["rI"]}}'))
var y={a:"https://bigdogg-production.up.railway.app/api/v1/quotes/public/"}
var x={u:A.ab("C<h>"),y:A.ab("ah<p,@>"),B:A.ab("ah<@,@>"),l:A.ab("h"),d:A.ab("P<@>?"),v:A.ab("~")};(function constants(){D.L1=new A.ao(0,720,0,1/0)
D.T7=new A.aq(B.lD,null,null,null,null)
D.x2=new A.aq(E.wJ,null,B.aq,null,null)
D.TX=new A.aq(P.py,48,B.z,null,null)
D.Sg=new A.aj(63047,"MaterialIcons",null,!1)
D.UG=new A.aq(D.Sg,null,null,null,null)
D.Qj=new A.a6(0,64,0,64)
D.a4a=new A.a9(D.Qj,K.b2,null)
D.a8c=new A.cd(14,null,null,null)
D.aaS=new A.q(!0,null,null,null,null,null,15,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)
D.afQ=new A.dn("Regels",null,G.kg,null,null,null,null,null,null,null,null)
D.afZ=new A.dn("Offerte accepteren",null,B.mL,null,null,null,null,null,null,null,null)
D.ag3=new A.dn("Afwijzen",null,null,null,null,null,null,null,null,null,null)})()};
(a=>{a["MvNHts7aZUziihF6KQc7daU1qgE="]=a.current})($__dart_deferred_initializers__);