((a,b)=>{a[b]=a[b]||{}})(self,"$__dart_deferred_initializers__")
$__dart_deferred_initializers__.current=function(a,b,c,$){var J,A,B,H,K,L,S,T,N,U,O,P,V,Q,I,G,E,M,F,R,W,X,C={
bw9(d){return new C.tk(d,null)},
tk:function tk(d,e){this.c=d
this.a=e},
QJ:function QJ(d){var _=this
_.d=!0
_.e=null
_.f=d
_.r=!1
_.c=_.a=null},
b2y:function b2y(d){this.a=d},
b2z:function b2z(d,e){this.a=d
this.b=e},
b2A:function b2A(d){this.a=d},
b2B:function b2B(){},
b2C:function b2C(d,e,f){this.a=d
this.b=e
this.c=f},
b2D:function b2D(d,e){this.a=d
this.b=e},
b2H:function b2H(d,e,f){this.a=d
this.b=e
this.c=f},
b2G:function b2G(d,e){this.a=d
this.b=e},
b2E:function b2E(d){this.a=d},
b2F:function b2F(d,e,f){this.a=d
this.b=e
this.c=f},
b2r:function b2r(d){this.a=d},
b2v:function b2v(){},
b2w:function b2w(){},
b2x:function b2x(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
b2t:function b2t(){},
b2u:function b2u(d,e){this.a=d
this.b=e},
b2s:function b2s(d,e,f){this.a=d
this.b=e
this.c=f},
y2:function y2(d,e,f,g){var _=this
_.c=d
_.d=e
_.e=f
_.a=g},
QI:function QI(){this.d=!1
this.c=this.a=null},
b1W:function b1W(d,e,f){this.a=d
this.b=e
this.c=f},
b1X:function b1X(d){this.a=d},
b1Y:function b1Y(d){this.a=d},
b1Z:function b1Z(d){this.a=d},
b2o:function b2o(d){this.a=d},
b2p:function b2p(d){this.a=d},
b2q:function b2q(d){this.a=d},
b2h:function b2h(d){this.a=d},
b2i:function b2i(d){this.a=d},
b2m:function b2m(){},
b2n:function b2n(d,e){this.a=d
this.b=e},
b2l:function b2l(){},
b2k:function b2k(d,e){this.a=d
this.b=e},
b2j:function b2j(d,e){this.a=d
this.b=e},
b25:function b25(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
b24:function b24(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
b21:function b21(d,e,f){this.a=d
this.b=e
this.c=f},
b20:function b20(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
b2_:function b2_(d,e,f){this.a=d
this.b=e
this.c=f},
b22:function b22(d){this.a=d},
b23:function b23(d){this.a=d},
b26:function b26(d){this.a=d},
b27:function b27(d){this.a=d},
b2e:function b2e(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
b2d:function b2d(d,e,f,g){var _=this
_.a=d
_.b=e
_.c=f
_.d=g},
b2a:function b2a(d,e,f){this.a=d
this.b=e
this.c=f},
b29:function b29(d,e,f){this.a=d
this.b=e
this.c=f},
b28:function b28(d,e){this.a=d
this.b=e},
b2b:function b2b(d){this.a=d},
b2c:function b2c(d){this.a=d},
b2f:function b2f(d){this.a=d},
b2g:function b2g(d){this.a=d},
yF(d,e,f){return C.bp9(d,e,f)},
bp9(d,e,f){var w=0,v=A.o(x.P),u,t=2,s=[],r,q,p,o,n,m,l,k,j,i,h,g
var $async$yF=A.k(function(a1,a2){if(a1===1){s.push(a2)
w=t}for(;;)switch(w){case 0:w=3
return A.e(G.kG(),$async$yF)
case 3:h=a2
t=5
l=A.aG(y.d+f+"/link",0,null)
k=x.N
j=A.w(["Authorization","Bearer "+A.j(h),"Content-Type","application/json"],k,k)
w=8
return A.e(A.di(l,B.x.dJ(A.w(["link_type",d,"linked_id",e],k,x.T),null),null,j),$async$yF)
case 8:r=a2
if(r.b===200){q=A.z(k,x.z)
J.cl(q,"success",!0)
for(l=r,l=J.jO(B.x.aW(0,A.bu(A.bt(l.e)).aE(0,l.w),null)),l=l.gaj(l);l.B();){p=l.gP(l)
o=p.a
n=p.b
J.cl(q,o,n)}u=q
w=1
break}try{q=r
m=B.x.aW(0,A.bu(A.bt(q.e)).aE(0,q.w),null)
q=J.r(m,"detail")
q=A.w(["success",!1,"message",q==null?null:J.a2(q)],k,x.z)
u=q
w=1
break}catch(a0){q=A.w(["success",!1],k,x.z)
u=q
w=1
break}t=2
w=7
break
case 5:t=4
g=s.pop()
q=A.w(["success",!1,"message","Connection error"],x.N,x.z)
u=q
w=1
break
w=7
break
case 4:w=2
break
case 7:case 1:return A.m(u,v)
case 2:return A.l(s.at(-1),v)}})
return A.n($async$yF,v)},
Tw(d,e,f,g,h){var w="general"
return C.bp5(d,e,f,g,h)},
bp5(d,e,a0,a1,a2){var w=0,v=A.o(x.P),u,t=2,s=[],r,q,p,o,n,m,l,k,j,i,h,g,f
var $async$Tw=A.k(function(a4,a5){if(a4===1){s.push(a5)
w=t}for(;;)switch(w){case 0:h="general"
w=3
return A.e(G.kG(),$async$Tw)
case 3:g=a5
t=5
l=A.aG(y.d+a2+"/create-investment",0,null)
k=x.N
j=A.w(["Authorization","Bearer "+A.j(g),"Content-Type","application/json"],k,k)
w=8
return A.e(A.di(l,B.x.dJ(A.w(["description",a0,"amount",d,"purchase_date",a1,"depreciation_years",e,"category",h],k,x.K),null),null,j),$async$Tw)
case 8:r=a5
if(r.b===200){q=A.z(k,x.z)
J.cl(q,"success",!0)
for(l=r,l=J.jO(B.x.aW(0,A.bu(A.bt(l.e)).aE(0,l.w),null)),l=l.gaj(l);l.B();){p=l.gP(l)
o=p.a
n=p.b
J.cl(q,o,n)}u=q
w=1
break}try{q=r
m=B.x.aW(0,A.bu(A.bt(q.e)).aE(0,q.w),null)
q=J.r(m,"detail")
q=A.w(["success",!1,"message",q==null?null:J.a2(q)],k,x.z)
u=q
w=1
break}catch(a3){q=A.w(["success",!1],k,x.z)
u=q
w=1
break}t=2
w=7
break
case 5:t=4
f=s.pop()
q=A.w(["success",!1,"message","Connection error"],x.N,x.z)
u=q
w=1
break
w=7
break
case 4:w=2
break
case 7:case 1:return A.m(u,v)
case 2:return A.l(s.at(-1),v)}})
return A.n($async$Tw,v)},
Tv(d,e,f,g,h){var w="general"
return C.bp4(d,e,f,g,h)},
bp4(d,e,a0,a1,a2){var w=0,v=A.o(x.P),u,t=2,s=[],r,q,p,o,n,m,l,k,j,i,h,g,f
var $async$Tv=A.k(function(a4,a5){if(a4===1){s.push(a5)
w=t}for(;;)switch(w){case 0:h="general"
w=3
return A.e(G.kG(),$async$Tv)
case 3:g=a5
t=5
l=A.aG(y.d+a2+"/create-expense",0,null)
k=x.N
j=A.w(["Authorization","Bearer "+A.j(g),"Content-Type","application/json"],k,k)
w=8
return A.e(A.di(l,B.x.dJ(A.w(["description",a0,"amount_ex_btw",d,"btw_rate",e,"expense_date",a1,"category",h],k,x.K),null),null,j),$async$Tv)
case 8:r=a5
if(r.b===200){q=A.z(k,x.z)
J.cl(q,"success",!0)
for(l=r,l=J.jO(B.x.aW(0,A.bu(A.bt(l.e)).aE(0,l.w),null)),l=l.gaj(l);l.B();){p=l.gP(l)
o=p.a
n=p.b
J.cl(q,o,n)}u=q
w=1
break}try{q=r
m=B.x.aW(0,A.bu(A.bt(q.e)).aE(0,q.w),null)
q=J.r(m,"detail")
q=A.w(["success",!1,"message",q==null?null:J.a2(q)],k,x.z)
u=q
w=1
break}catch(a3){q=A.w(["success",!1],k,x.z)
u=q
w=1
break}t=2
w=7
break
case 5:t=4
f=s.pop()
q=A.w(["success",!1,"message","Connection error"],x.N,x.z)
u=q
w=1
break
w=7
break
case 4:w=2
break
case 7:case 1:return A.m(u,v)
case 2:return A.l(s.at(-1),v)}})
return A.n($async$Tv,v)},
Tz(d){return C.bp6(d)},
bp6(d){var w=0,v=A.o(x.P),u,t=2,s=[],r,q,p,o,n,m,l,k
var $async$Tz=A.k(function(e,f){if(e===1){s.push(f)
w=t}for(;;)switch(w){case 0:w=3
return A.e(G.kG(),$async$Tz)
case 3:l=f
t=5
p=x.N
w=8
return A.e(A.d8(A.aG("https://bigdogg-production.up.railway.app/api/v1/banking/transactions?page_size="+d,0,null),A.w(["Authorization","Bearer "+A.j(l)],p,p)),$async$Tz)
case 8:r=f
if(r.b===200){o=r
p=A.w(["success",!0,"data",B.x.aW(0,A.bu(A.bt(o.e)).aE(0,o.w),null)],p,x.z)
u=p
w=1
break}try{o=r
q=B.x.aW(0,A.bu(A.bt(o.e)).aE(0,o.w),null)
o=r.b
n=J.r(q,"detail")
o=A.w(["success",!1,"status",o,"message",n==null?null:J.a2(n)],p,x.z)
u=o
w=1
break}catch(j){p=A.w(["success",!1,"status",r.b],p,x.z)
u=p
w=1
break}t=2
w=7
break
case 5:t=4
k=s.pop()
p=A.w(["success",!1,"message","Connection error"],x.N,x.z)
u=p
w=1
break
w=7
break
case 4:w=2
break
case 7:case 1:return A.m(u,v)
case 2:return A.l(s.at(-1),v)}})
return A.n($async$Tz,v)}},D,Y,Z
J=c[1]
A=c[0]
B=c[2]
H=c[24]
K=c[37]
L=c[35]
S=c[34]
T=c[21]
N=c[54]
U=c[67]
O=c[41]
P=c[43]
V=c[40]
Q=c[19]
I=c[50]
G=c[16]
E=c[53]
M=c[22]
F=c[27]
R=c[23]
W=c[18]
X=c[29]
C=a.updateHolder(c[11],C)
D=c[68]
Y=c[17]
Z=c[31]
C.tk.prototype={
W(){return new C.QJ(D.a_s)}}
C.QJ.prototype={
af(){this.ap()
this.yH()},
yH(){var w=0,v=A.o(x.H),u,t=this,s,r,q,p
var $async$yH=A.k(function(d,e){if(d===1)return A.l(e,v)
for(;;)switch(w){case 0:t.t(new C.b2y(t))
w=3
return A.e(C.Tz(100),$async$yH)
case 3:s=e
if(t.c==null){w=1
break}r=J.V(s)
if(J.d(r.h(s,"success"),!0)){q=x.h.a(r.h(s,"data"))
r=q==null?null:J.r(q,"transactions")
x.g.a(r)
t.t(new C.b2z(t,r==null?B.dg:r))
if(!t.r){r=t.a.c
r=r!=null&&r.length!==0}else r=!1
if(r){t.r=!0
r=t.c
r.toString
r=A.cM(r,!1,x.C).b
p=J.bo2(t.f,new C.b2A(t),new C.b2B())
if(J.dX(p))$.ag.k4$.push(new C.b2C(t,p,r==="nl"))}}else t.t(new C.b2D(t,s))
case 1:return A.m(u,v)}})
return A.n($async$yH,v)},
ZH(d,e){var w=B.e.S(Math.abs(d),2),v=A.es(w,".",","),u=e==="EUR"?"\u20ac":e
return(d>=0?"+":"\u2212")+" "+u+" "+v},
aq6(d,e){var w,v,u,t
if(d.length===0)return"\u2014"
try{w=A.kK(d)
v=e?D.a0o:B.pT
u=J.r(v,A.bo(w)-1)
return""+A.c9(w)+" "+u+" "+A.aU(w)}catch(t){return d}},
awt(d,e){var w,v,u,t,s,r,q,p,o=null
if(d==null)return B.aH
w=J.V(d)
v=w.h(d,"type")
u=v==null?o:J.a2(v)
w=w.h(d,"linked_label")
t=w==null?o:J.a2(w)
if(t==null)t=""
switch(u){case"invoice":s=e?"Factuur "+t:"Invoice "+t
r=B.c0
q=B.C
p=B.c4
break
case"expense":s=e?"Kosten \xb7 "+t:"Expense \xb7 "+t
r=B.c0
q=B.C
p=B.c4
break
case"investment":s=e?"Investering \xb7 "+t:"Investment \xb7 "+t
r=B.c0
q=B.C
p=B.c4
break
case"private":s=e?"Priv\xe9":"Private"
r=B.og
q=B.G
p=B.jj
break
case"suggested_invoice":case"suggested_expense":case"suggested_investment":s="Match? "+t
r=F.eo
q=I.ak
p=D.wr
break
default:return B.aH}w=A.D(6)
return A.B(o,A.Z(A.a([A.bN(p,q,o,11),B.be,new A.fF(1,B.c3,A.c(s,o,B.ad,o,o,A.aH(o,o,q,o,o,o,o,o,o,o,o,10.5,o,o,B.Q,o,o,!0,o,o,o,o,o,o,o,o),o,o,o),o)],x.p),B.j,B.d,B.I,0),B.h,o,o,new A.L(r,o,o,w,o,o,B.m),o,o,o,U.vy,B.d5,o,o,o)},
yX(d,e){return this.ayz(d,e)},
ayz(d,e){var w=0,v=A.o(x.H),u=this,t
var $async$yX=A.k(function(f,g){if(f===1)return A.l(g,v)
for(;;)switch(w){case 0:t=u.c
t.toString
w=2
return A.e(G.mG(B.i,new C.b2H(u,d,e),t,!0,E.jS,x.H),$async$yX)
case 2:return A.m(null,v)}})
return A.n($async$yX,v)},
G(d){var w,v=this,u=null,t=A.cM(d,!0,x.C).b==="nl",s=A.mM(u,u,!0,B.i,u,!1,0,B.l,D.SI,u,u,u,B.J,A.c(t?"Transacties":"Transactions",u,u,u,u,F.il,u,u,u))
if(v.d)w=O.b2
else{if(v.e!=null)w=v.aDS(t)
else if(J.cP(v.f))w=M.oW(A.a([D.I9,E.x7,B.y,A.c(t?"Nog geen transacties gevonden":"No transactions yet",u,u,u,u,D.aev,B.a3,u,u)],x.p),B.ck,F.dO,u,!1)
else w=v.al5(t)
w=Y.Bh(w,v.ga0J())}return A.fu(s,B.a1,A.fM(!0,w,!0,B.a9,!0,!0),u,u)},
aDS(d){var w,v=null,u=this.e,t=u==null
if(B.c.p(t?"":u,"bank_session_expired")){u=A.c(d?"Bank-koppeling verlopen":"Bank connection expired",v,v,v,v,F.il,B.a3,v,v)
t=A.c(d?"Tink-toegang in sandbox is ~1 uur geldig. Koppel je bankrekening opnieuw om de meest recente transacties op te halen.":"Tink sandbox access is ~1 hour. Reconnect your bank to fetch the latest transactions.",v,v,v,v,B.aU,B.a3,v,v)
return M.oW(A.a([D.a8o,D.TL,B.D,u,B.F,new A.a9(D.Qo,t,v),B.aR,A.bH(R.fl(D.TK,A.c(d?"Ga naar instellingen":"Go to settings",v,v,v,v,B.bC,v,v,v),new C.b2r(this),A.cE(v,v,B.l,v,v,v,v,v,v,v,v,v,D.QH,v,new A.bp(A.D(8),B.v),v,v,v,v,v)),v,v)],x.p),B.ck,F.dO,v,!1)}w=A.c(d?"Kon transacties niet ophalen":"Could not fetch transactions",v,v,v,v,D.ac0,B.a3,v,v)
u=A.c(t?"":u,v,v,v,v,L.az,B.a3,v,v)
return M.oW(A.a([D.I9,D.TJ,B.y,w,B.aS,u,B.D,A.bH(W.no(D.T6,A.c(d?"Opnieuw proberen":"Try again",v,v,v,v,v,v,v,v),this.ga0J(),v),v,v)],x.p),B.ck,F.dO,v,!1)},
al5(d){var w,v,u,t,s=A.z(x.N,x.D)
for(w=J.bb(this.f);w.B();){v=w.gP(w)
u=J.r(v,"date")
J.eJ(s.bK(0,A.bg(u==null?"":u),new C.b2v()),v)}w=s.$ti.i("c8<1>")
t=A.ab(new A.c8(s,w),w.i("A.E"))
B.b.ej(t,new C.b2w())
return G.m8(new C.b2x(this,t,s,d),t.length,F.oE,F.dO)}}
C.y2.prototype={
W(){return new C.QI()},
jZ(d){return this.e.$1(d)}}
C.QI.prototype={
G(a2){var w,v,u,t,s,r,q,p,o,n,m,l,k,j,i,h,g,f,e=null,d=this.a,a0=d.c,a1=d.d
d=J.V(a0)
w=A.dR(d.h(a0,"amount"))
v=w==null?e:w
if(v==null)v=0
u=A.b3(d.h(a0,"description"))
if(u==null)u=""
t=A.b3(d.h(a0,"merchant"))
if(t==null)t=""
s=A.b3(d.h(a0,"date"))
if(s==null)s=""
r=x.h.a(d.h(a0,"link"))
if(r==null)q=e
else{d=J.r(r,"type")
q=d==null?e:J.a2(d)}p=v>0
d=t.length!==0
o=d?t:u
n=d&&u.length!==0&&u!==t?u:""
m=p?B.C:B.z
l=p?B.c0:B.cP
d=A.bB(a2,e,x.w).w
w=A.bH(A.B(e,e,B.h,e,e,new A.L(B.w,e,e,A.D(2),e,e,B.m),e,4,e,e,e,e,e,40),e,e)
k=A.D(12)
j=A.D(10)
j=A.B(e,A.bN(p?D.wH:D.wA,m,e,e),B.h,e,e,new A.L(B.i,e,e,j,e,e,B.m),e,44,e,e,e,e,e,44)
if(o.length===0)i=a1?"Transactie":"Transaction"
else i=o
h=x.p
i=A.a([A.c(i,1,B.ad,e,e,B.f4,e,e,e)],h)
if(n.length!==0)B.b.I(i,A.a([B.bf,A.c(n,1,B.ad,e,e,B.aA,e,e,e)],h))
if(s.length!==0)B.b.I(i,A.a([B.av,A.c(s,e,e,e,e,B.cX,e,e,e)],h))
i=A.a1(A.G(i,B.q,B.d,B.f),1)
g=p?"+":"\u2212"
f=B.e.S(Math.abs(v),2)
w=A.a([B.y,w,B.D,A.B(e,A.Z(A.a([j,K.br,i,K.br,A.c(g+" \u20ac "+A.es(f,".",","),e,e,e,e,A.aH(e,e,m,e,e,e,e,e,e,e,e,18,e,e,B.E,e,e,!0,e,e,e,e,e,e,e,e),e,e,e)],h),B.j,B.d,B.f,0),B.h,e,e,new A.L(l,e,e,k,e,e,B.m),e,e,e,B.dx,B.a5,e,e,e),B.D],h)
if(this.d)w.push(D.a4c)
else B.b.I(w,this.akM(q,p,a1))
w.push(B.y)
return A.fM(!0,new A.a9(new A.a6(0,0,0,d.f.d),A.dm(A.G(w,B.aN,B.d,B.I),e,B.r,e,e,B.a8),e),!0,B.a9,!0,!0)},
akM(a2,a3,a4){var w,v,u,t,s,r,q,p,o,n,m,l,k,j,i=this,h=null,g="suggested_investment",f="linked_label",e=x.h.a(J.r(i.a.c,"link")),d=x.p,a0=A.a([],d),a1=a2==="suggested_invoice"
if(a1||a2==="suggested_expense"||a2===g){w=e==null
if(w)v=h
else{u=J.r(e,"linked_id")
v=u==null?h:J.a2(u)}if(w)t=h
else{w=J.r(e,f)
w=w==null?h:J.a2(w)
t=w}if(t==null)t=""
if(a1)s="invoice"
else s=a2===g?"investment":"expense"
a1=A.D(12)
w=A.aw(A.a0(B.e.am(76.5),I.ak.m()>>>16&255,I.ak.m()>>>8&255,I.ak.m()&255),1)
u=A.Z(A.a([D.TU,B.aX,A.c(a4?"Mogelijk match":"Possible match",h,h,h,h,D.abd,h,h,h)],d),B.j,B.d,B.f,0)
if(s==="invoice")r=a4?"Wij denken dat dit een betaling is van factuur "+t+".":"We think this is a payment of invoice "+t+"."
else if(s==="investment")r=a4?"Wij denken dat dit hoort bij investering \xb7 "+t+".":"We think this matches investment \xb7 "+t+"."
else r=a4?"Wij denken dat dit hoort bij kosten \xb7 "+t+".":"We think this matches expense \xb7 "+t+"."
r=A.c(r,h,h,h,h,F.mK,h,h,h)
q=i.d?h:new C.b1W(i,s,v)
q=A.a1(R.fl(D.Tt,A.c(a4?"Klopt":"Confirm",h,h,h,h,B.bC,h,h,h),q,A.cE(h,h,B.C,h,h,h,h,h,h,h,h,h,E.fx,h,new A.bp(A.D(8),B.v),h,h,h,h,h)),1)
p=i.d?h:new C.b1X(i)
o=A.l5(h,h,h,h,h,h,h,h,h,B.G,h,h,E.fx,h,new A.bp(A.D(8),B.v),V.nF,h,h,h,h)
a0.push(A.B(h,A.G(A.a([u,B.F,r,B.y,A.Z(A.a([q,B.a0,A.a1(A.II(A.c(a4?"Anders":"Different",h,h,h,h,h,h,h,h),p,o),1)],d),B.j,B.d,B.f,0)],d),B.aN,B.d,B.f),B.h,h,h,new A.L(F.eo,h,w,a1,h,h,B.m),h,h,h,B.dx,B.d4,h,h,h))
a0.push(B.D)}a1=a2==="invoice"
if(a1||a2==="expense"||a2==="investment"||a2==="private"){if(e==null)n=h
else{w=J.r(e,f)
w=w==null?h:J.a2(w)
n=w}if(n==null)n=""
if(a1){m=a4?"Gekoppeld aan factuur "+n:"Linked to invoice "+n
l=B.c4
k=B.C
j=B.c0}else if(a2==="expense"){m=a4?"Gekoppeld aan kosten \xb7 "+n:"Linked to expense \xb7 "+n
l=B.c4
k=B.C
j=B.c0}else if(a2==="investment"){m=a4?"Gekoppeld aan investering \xb7 "+n:"Linked to investment \xb7 "+n
l=B.c4
k=B.C
j=B.c0}else{m=a4?"Gemarkeerd als priv\xe9":"Marked as private"
l=B.jj
k=B.G
j=B.og}w=A.D(12)
a0.push(A.B(h,A.Z(A.a([A.bN(l,k,h,18),B.bL,A.a1(A.c(m,h,h,h,h,A.aH(h,h,k,h,h,h,h,h,h,h,h,13,h,h,B.Q,h,h,!0,h,h,h,h,h,h,h,h),h,h,h),1)],d),B.j,B.d,B.f,0),B.h,h,h,new A.L(j,h,h,w,h,h,B.m),h,h,h,B.dx,B.d4,h,h,h))
a0.push(B.y)
d=a4?"Ontkoppel":"Unlink"
if(a4)a1=a1?"Factuur weer als verzonden markeren":"Verwijder de koppeling"
else a1="Remove the link"
a0.push(i.xl(E.pA,B.z,i.gaDT(),a1,d))
return a0}if(a3){d=a4?"Markeer als betaling van factuur":"Mark as invoice payment"
a1=a4?"Kies welke openstaande factuur is betaald":"Pick which unpaid invoice this settles"
a0.push(i.xl(E.wF,B.l,i.gazG(),a1,d))}else{d=a4?"Voeg toe als zakelijke kosten":"Add as business expense"
a1=a4?"Maak een kostenpost aan met BTW":"Create an expense entry with VAT"
a0.push(i.xl(Z.pJ,B.l,i.gani(),a1,d))
d=a4?"Voeg toe als investering":"Add as investment"
a1=a4?"Voor aankopen die je afschrijft over meerdere jaren":"For purchases depreciated over multiple years"
a0.push(i.xl(D.RX,B.l,i.ganl(),a1,d))}d=a4?"Priv\xe9 / negeren":"Private / ignore"
a1=a4?"Hoort niet bij je administratie":"Does not belong to your bookkeeping"
a0.push(i.xl(B.jj,B.G,i.gawK(),a1,d))
return a0},
xl(d,e,f,g,h){var w=null,v=this.d?w:f,u=A.D(10),t=A.D(10),s=A.aw(B.w,1),r=A.a0(B.e.am(25.5),e.m()>>>16&255,e.m()>>>8&255,e.m()&255),q=A.D(8),p=x.p
return new A.a9(B.oK,A.eD(!1,B.a_,!0,w,A.ea(!1,u,!0,H.WJ(new A.a9(S.oI,A.Z(A.a([A.B(w,A.bN(d,e,w,18),B.h,w,w,new A.L(r,w,w,q,w,w,B.m),w,36,w,w,w,w,w,36),K.br,A.a1(A.G(A.a([A.c(h,w,w,w,w,N.rt,w,w,w),B.bf,A.c(g,w,w,w,w,B.aA,w,w,w)],p),B.q,B.d,B.f),1),D.Tn],p),B.j,B.d,B.f,0),w),w,new A.L(B.i,w,s,t,w,w,B.m)),w,!0,w,w,w,w,w,w,w,w,w,w,v,w,w,w,w,w,w,w),B.h,B.J,0,w,w,w,w,w,B.ca),w)},
xF(d,e){return this.amY(d,e)},
amY(d,e){var w=0,v=A.o(x.H),u,t=this,s,r,q,p
var $async$xF=A.k(function(f,g){if(f===1)return A.l(g,v)
for(;;)switch(w){case 0:if(e==null){w=1
break}t.t(new C.b1Y(t))
w=3
return A.e(C.yF(d,e,J.a2(J.r(t.a.c,"id"))),$async$xF)
case 3:s=g
if(t.c==null){w=1
break}r=J.V(s)
if(J.d(r.h(s,"success"),!0)){r=x.U.a(J.r(t.a.c,"link"))
if(r==null)q=null
else{r=J.r(r,"linked_label")
r=r==null?null:J.a2(r)
q=r}if(q==null)q=""
r=t.a
r.toString
p=x.N
r.jZ(A.w(["link",A.w(["type",d,"linked_id",e,"linked_label",q,"auto",!1],p,x.K)],p,x.z))
p=t.c
p.toString
A.aQ(p,!1).aU(null)}else{t.t(new C.b1Z(t))
p=t.c.O(x.q).f
r=r.h(s,"message")
r=r==null?null:J.a2(r)
p.b2(H.bw(null,null,null,B.z,null,B.n,null,A.c(r==null?"Error":r,null,null,null,null,null,null,null,null),null,B.a4,null,null,null,null,null,null,null,null,null,null))}case 1:return A.m(u,v)}})
return A.n($async$xF,v)},
uI(d){return this.aE4(d)},
aDU(){return this.uI(!1)},
aE4(d){var w=0,v=A.o(x.H),u,t=this,s,r
var $async$uI=A.k(function(e,f){if(e===1)return A.l(f,v)
for(;;)switch(w){case 0:t.t(new C.b2o(t))
w=3
return A.e(C.yF(null,null,J.a2(J.r(t.a.c,"id"))),$async$uI)
case 3:s=f
if(t.c==null){w=1
break}if(J.d(J.r(s,"success"),!0)){r=t.a
r.toString
r.jZ(A.w(["link",null],x.N,x.z))
J.cl(t.a.c,"link",null)
t.t(new C.b2p(t))
if(!d){r=t.c
r.toString
A.aQ(r,!1).aU(null)}}else t.t(new C.b2q(t))
case 1:return A.m(u,v)}})
return A.n($async$uI,v)},
EV(){var w=0,v=A.o(x.H),u,t=this,s,r,q,p
var $async$EV=A.k(function(d,e){if(d===1)return A.l(e,v)
for(;;)switch(w){case 0:t.t(new C.b2h(t))
w=3
return A.e(C.yF("private",null,J.a2(J.r(t.a.c,"id"))),$async$EV)
case 3:s=e
if(t.c==null){w=1
break}if(J.d(J.r(s,"success"),!0)){r=t.a
q=r.d?"Priv\xe9":"Private"
p=x.N
r.jZ(A.w(["link",A.w(["type","private","linked_id",null,"linked_label",q,"auto",!1],p,x.X)],p,x.z))
p=t.c
p.toString
A.aQ(p,!1).aU(null)}else t.t(new C.b2i(t))
case 1:return A.m(u,v)}})
return A.n($async$EV,v)},
ur(){var w=0,v=A.o(x.H),u,t=this,s,r,q,p,o
var $async$ur=A.k(function(d,e){if(d===1)return A.l(e,v)
for(;;)switch(w){case 0:w=3
return A.e(G.Hv(),$async$ur)
case 3:o=e
if(t.c==null){w=1
break}s=J.V(o)
if(!J.d(s.h(o,"success"),!0)){s=t.c.O(x.q).f
s.b2(H.bw(null,null,null,B.z,null,B.n,null,A.c(t.a.d?"Kon facturen niet laden":"Could not load invoices",null,null,null,null,null,null,null,null),null,B.a4,null,null,null,null,null,null,null,null,null,null))
w=1
break}r=x.g.a(s.h(o,"invoices"))
if(r==null)r=B.dg
s=J.u9(r,new C.b2m())
q=A.ab(s,s.$ti.i("A.E"))
if(q.length===0){s=t.c.O(x.q).f
s.b2(H.bw(null,null,null,null,null,B.n,null,A.c(t.a.d?"Geen openstaande facturen":"No unpaid invoices",null,null,null,null,null,null,null,null),null,B.a4,null,null,null,null,null,null,null,null,null,null))
w=1
break}s=t.c
s.toString
w=4
return A.e(G.mG(B.i,new C.b2n(t,q),s,!0,E.jS,x.P),$async$ur)
case 4:p=e
if(t.c==null||p==null){w=1
break}w=5
return A.e(t.xF("invoice",J.a2(J.r(p,"id"))),$async$ur)
case 5:case 1:return A.m(u,v)}})
return A.n($async$ur,v)},
xK(){return this.anj()},
anj(){var w=0,v=A.o(x.H),u,t=this,s,r,q,p,o,n,m,l,k,j,i,h,g,f
var $async$xK=A.k(function(d,e){if(d===1)return A.l(e,v)
for(;;)switch(w){case 0:i={}
h=t.a
g=h.c
f=h.d
h=J.V(g)
s=h.h(g,"merchant")
s=s==null?null:J.a2(s)
if(s==null){s=h.h(g,"description")
s=s==null?null:J.a2(s)}r=B.c.aK(s==null?"":s)
s=A.dR(h.h(g,"amount"))
if(s==null)s=null
q=Math.abs(s==null?0:s)
p=A.b3(h.h(g,"date"))
if(p==null)p=B.b.gV(new A.aY(Date.now(),0,!1).iU().split("T"))
o=new A.bE(new A.ch(r,B.b5,B.ay),$.ao())
i.a=21
i.b=q/1.21
s=t.c
s.toString
w=3
return A.e(A.dr(null,null,!0,null,new C.b25(i,f,o,q),s,null,!0,!0,x.y),$async$xK)
case 3:n=e
if(t.c==null||n!==!0){w=1
break}t.t(new C.b26(t))
h=J.a2(h.h(g,"id"))
s=B.c.aK(o.a.a)
if(s.length===0)s="Bank transactie"
w=4
return A.e(C.Tv(A.b5S(B.e.S(i.b,2)),i.a,s,p,h),$async$xK)
case 4:m=e
if(t.c==null){w=1
break}i=J.V(m)
if(J.d(i.h(m,"success"),!0)){l=x.h.a(i.h(m,"expense"))
i=t.a
i.toString
h=l==null
if(h)s=null
else{s=J.r(l,"id")
s=s==null?null:J.a2(s)}if(h)k=null
else{k=J.r(l,"description")
k=k==null?null:J.a2(k)}if(k==null)k=""
if(h)h=null
else{h=J.r(l,"description")
h=h==null?null:J.a2(h)}j=x.N
i.jZ(A.w(["link",A.w(["type","expense","linked_id",s,"linked_label",B.c.a7(k,0,B.k.cK((h==null?"":h).length,0,40)),"auto",!1],j,x.X)],j,x.z))
j=t.c
j.toString
A.aQ(j,!1).aU(null)
j=t.c.O(x.q).f
j.b2(H.bw(null,null,null,B.C,null,B.n,null,A.c(f?"Kosten toegevoegd":"Expense added",null,null,null,null,null,null,null,null),null,B.a4,null,null,null,null,null,null,null,null,null,null))}else{t.t(new C.b27(t))
h=t.c.O(x.q).f
i=i.h(m,"message")
i=i==null?null:J.a2(i)
h.b2(H.bw(null,null,null,B.z,null,B.n,null,A.c(i==null?"Error":i,null,null,null,null,null,null,null,null),null,B.a4,null,null,null,null,null,null,null,null,null,null))}case 1:return A.m(u,v)}})
return A.n($async$xK,v)},
xL(){return this.anm()},
anm(){var w=0,v=A.o(x.H),u,t=this,s,r,q,p,o,n,m,l,k,j,i,h,g,f
var $async$xL=A.k(function(d,e){if(d===1)return A.l(e,v)
for(;;)switch(w){case 0:i={}
h=t.a
g=h.c
f=h.d
h=J.V(g)
s=h.h(g,"merchant")
s=s==null?null:J.a2(s)
if(s==null){s=h.h(g,"description")
s=s==null?null:J.a2(s)}r=B.c.aK(s==null?"":s)
s=A.dR(h.h(g,"amount"))
if(s==null)s=null
q=Math.abs(s==null?0:s)
p=A.b3(h.h(g,"date"))
if(p==null)p=B.b.gV(new A.aY(Date.now(),0,!1).iU().split("T"))
o=new A.bE(new A.ch(r,B.b5,B.ay),$.ao())
i.a=5
s=t.c
s.toString
w=3
return A.e(A.dr(null,null,!0,null,new C.b2e(i,f,o,q),s,null,!0,!0,x.y),$async$xL)
case 3:n=e
if(t.c==null||n!==!0){w=1
break}t.t(new C.b2f(t))
h=J.a2(h.h(g,"id"))
s=B.c.aK(o.a.a)
if(s.length===0)s="Bank transactie"
w=4
return A.e(C.Tw(q,i.a,s,p,h),$async$xL)
case 4:m=e
if(t.c==null){w=1
break}i=J.V(m)
if(J.d(i.h(m,"success"),!0)){l=x.h.a(i.h(m,"investment"))
i=t.a
i.toString
h=l==null
if(h)s=null
else{s=J.r(l,"id")
s=s==null?null:J.a2(s)}if(h)k=null
else{k=J.r(l,"description")
k=k==null?null:J.a2(k)}if(k==null)k=""
if(h)h=null
else{h=J.r(l,"description")
h=h==null?null:J.a2(h)}j=x.N
i.jZ(A.w(["link",A.w(["type","investment","linked_id",s,"linked_label",B.c.a7(k,0,B.k.cK((h==null?"":h).length,0,40)),"auto",!1],j,x.X)],j,x.z))
j=t.c
j.toString
A.aQ(j,!1).aU(null)
j=t.c.O(x.q).f
j.b2(H.bw(null,null,null,B.C,null,B.n,null,A.c(f?"Investering toegevoegd":"Investment added",null,null,null,null,null,null,null,null),null,B.a4,null,null,null,null,null,null,null,null,null,null))}else{t.t(new C.b2g(t))
h=t.c.O(x.q).f
i=i.h(m,"message")
i=i==null?null:J.a2(i)
h.b2(H.bw(null,null,null,B.z,null,B.n,null,A.c(i==null?"Error":i,null,null,null,null,null,null,null,null),null,B.a4,null,null,null,null,null,null,null,null,null,null))}case 1:return A.m(u,v)}})
return A.n($async$xL,v)}}
var z=a.updateTypes(["al<~>()","kD(S,~(~()))","y2(S)","al<~>({silent:M})","re(S,x)"])
C.b2y.prototype={
$0(){var w=this.a
w.d=!0
w.e=null},
$S:0}
C.b2z.prototype={
$0(){var w=this.a
w.f=J.i1(this.b,x.P)
w.d=!1},
$S:0}
C.b2A.prototype={
$1(d){return J.d(J.r(d,"id"),this.a.a.c)},
$S:50}
C.b2B.prototype={
$0(){return B.jH},
$S:263}
C.b2C.prototype={
$1(d){var w=this.a
if(w.c!=null)w.yX(this.b,this.c)},
$S:4}
C.b2D.prototype={
$0(){var w=this.a,v=J.r(this.b,"message")
v=v==null?null:J.a2(v)
w.e=v==null?"transactions_error":v
w.d=!1},
$S:0}
C.b2H.prototype={
$1(d){var w=this.b
return new C.y2(w,this.c,new C.b2G(this.a,w),null)},
$S:z+2}
C.b2G.prototype={
$1(d){var w=this.a,v=J.bck(w.f,new C.b2E(this.b))
if(v>=0)w.t(new C.b2F(w,v,d))},
$S:248}
C.b2E.prototype={
$1(d){return J.d(J.r(d,"id"),J.r(this.a,"id"))},
$S:50}
C.b2F.prototype={
$0(){var w=this.a.f,v=this.b,u=J.V(w),t=A.eC(u.h(w,v),x.N,x.z)
t.I(0,this.c)
u.n(w,v,t)},
$S:0}
C.b2r.prototype={
$0(){var w=this.a.c
w.toString
return A.ei(w).dQ(0,"/dashboard?tab=settings",null)},
$S:0}
C.b2v.prototype={
$0(){return A.a([],x.t)},
$S:706}
C.b2w.prototype={
$2(d,e){return B.c.b6(e,d)},
$S:707}
C.b2x.prototype={
$2(d,e){var w,v,u,t,s,r,q,p=this,o=null,n=p.b[e],m=p.c.h(0,n)
m.toString
w=J.cz(m)
v=w.fq(m,0,new C.b2t(),x.i)
u=p.a
t=p.d
s=A.c(u.aq6(n,t),o,o,o,o,B.ce,o,o,o)
r=u.ZH(v,"EUR")
q=x.p
q=A.a([new A.a9(D.QB,A.Z(A.a([s,A.c(r,o,o,o,o,A.aH(o,o,v>=0?B.C:B.z,o,o,o,o,o,o,o,o,12,o,o,B.Q,o,o,!0,o,o,o,o,o,o,o,o),o,o,o)],q),B.j,B.c9,B.f,0),o)],q)
B.b.I(q,w.cO(m,new C.b2u(u,t),x.l))
return A.G(q,B.q,B.d,B.f)},
$S:708}
C.b2t.prototype={
$2(d,e){var w=A.dR(J.r(e,"amount"))
if(w==null)w=null
return d+(w==null?0:w)},
$S:709}
C.b2u.prototype={
$1(d){var w,v,u,t,s,r,q,p,o,n,m,l,k=null,j=J.V(d),i=A.dR(j.h(d,"amount")),h=i==null?k:i
if(h==null)h=0
w=A.b3(j.h(d,"currency"))
if(w==null)w="EUR"
v=A.b3(j.h(d,"description"))
if(v==null)v=""
u=A.b3(j.h(d,"merchant"))
if(u==null)u=""
t=x.h.a(j.h(d,"link"))
j=A.D(10)
i=this.a
s=this.b
r=A.D(10)
q=A.aw(B.w,1)
p=h>=0
o=p?D.wH:D.wA
o=A.bN(o,p?B.C:B.z,k,16)
n=u.length!==0
m=x.p
l=A.a([A.c(n?u:v,1,B.ad,k,k,E.f3,k,k,k)],m)
if(n&&v.length!==0&&v!==u)l.push(A.c(v,1,B.ad,k,k,B.cX,k,k,k))
l.push(i.awt(t,s))
n=A.a1(A.G(l,B.q,B.d,B.f),1)
l=i.ZH(h,w)
return A.ea(!1,j,!0,A.B(k,A.Z(A.a([o,B.bL,n,B.a0,A.c(l,k,k,k,k,A.aH(k,k,p?B.C:B.z,k,k,k,k,k,k,k,k,k,k,k,B.E,k,k,!0,k,k,k,k,k,k,k,k),k,k,k)],m),B.j,B.d,B.f,0),B.h,k,k,new A.L(B.i,k,q,r,k,k,B.m),k,k,k,E.vF,F.d3,k,k,k),k,!0,k,k,k,k,k,k,k,k,k,k,new C.b2s(i,d,s),k,k,k,k,k,k,k)},
$S:710}
C.b2s.prototype={
$0(){return this.a.yX(this.b,this.c)},
$S:0}
C.b1W.prototype={
$0(){return this.a.xF(this.b,this.c)},
$S:0}
C.b1X.prototype={
$0(){return this.a.uI(!0)},
$S:0}
C.b1Y.prototype={
$0(){return this.a.d=!0},
$S:0}
C.b1Z.prototype={
$0(){return this.a.d=!1},
$S:0}
C.b2o.prototype={
$0(){return this.a.d=!0},
$S:0}
C.b2p.prototype={
$0(){return this.a.d=!1},
$S:0}
C.b2q.prototype={
$0(){return this.a.d=!1},
$S:0}
C.b2h.prototype={
$0(){return this.a.d=!0},
$S:0}
C.b2i.prototype={
$0(){return this.a.d=!1},
$S:0}
C.b2m.prototype={
$1(d){var w=J.r(d,"status")
w=w==null?null:J.a2(w)
return(w==null?"":w)!=="paid"},
$S:19}
C.b2n.prototype={
$1(d){var w=null,v=A.B(w,w,B.h,w,w,new A.L(B.w,w,w,A.D(2),w,w,B.m),w,4,w,w,w,w,w,40),u=this.b
return A.fM(!0,A.b1(A.G(A.a([B.y,v,B.y,new A.a9(D.vJ,new A.dE(B.hm,w,w,A.c(this.a.a.d?"Kies een factuur":"Pick an invoice",w,w,w,w,N.aZ,w,w,w),w),w),B.F,A.a1(G.b8z(w,new C.b2k(u,d),u.length,D.vJ,new C.b2l()),1)],x.p),B.j,B.d,B.f),480,w),!0,B.a9,!0,!0)},
$S:711}
C.b2l.prototype={
$2(d,e){return B.d1},
$S:256}
C.b2k.prototype={
$2(d,e){var w,v,u,t,s=null,r=x.P.a(this.a[e]),q=J.V(r),p=q.h(r,"invoice_number"),o=p==null?s:J.a2(p)
if(o==null)o=""
p=q.h(r,"client_name")
w=p==null?s:J.a2(p)
if(w==null)w=""
p=q.h(r,"client_company")
v=p==null?s:J.a2(p)
if(v==null)v=""
q=A.dR(q.h(r,"total_incl_btw"))
u=q==null?s:q
if(u==null)u=0
q=A.c(o,s,s,s,s,E.cd,s,s,s)
p=A.c(v.length!==0?v:w,s,s,s,s,F.eh,s,s,s)
t=B.e.S(u,2)
return T.oV(!1,B.a9,s,s,!0,s,s,!0,s,s,s,s,s,s,new C.b2j(this.b,r),!1,s,s,s,s,p,s,q,s,A.c("\u20ac "+A.es(t,".",","),s,s,s,s,B.eF,s,s,s),s)},
$S:z+4}
C.b2j.prototype={
$0(){A.aQ(this.a,!1).aU(this.b)
return null},
$S:0}
C.b25.prototype={
$1(d){var w=this
return new A.eG(new C.b24(w.a,w.b,w.c,w.d),null)},
$S:18}
C.b24.prototype={
$2(d,e){var w,v=this,u=null,t=v.b,s=A.c(t?"Nieuwe kostenpost":"New expense",u,u,u,u,u,u,u,u),r=A.bQ(u,B.S,!1,u,!0,B.n,u,A.bS(),v.c,u,u,u,u,u,2,A.by(u,P.i2,u,u,u,u,u,u,!0,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,!0,u,u,t?"Omschrijving":"Description",!0,!0,!1,u,u,u,u,u,u,u,u,u,u,u,u,u,u),B.r,!0,u,!0,u,!1,u,B.R,u,u,u,u,u,u,u,u,1,u,u,!1,"\u2022",u,u,u,u,u,!1,u,u,!1,u,!0,u,B.N,u,u,u,u,u,u,u,u,u,u,u,u,!0,B.K,u,B.Y,u,u,u,u),q=x.p,p=A.a([A.c(t?"BTW:":"VAT:",u,u,u,u,F.eh,u,u,u),K.br],q),o=v.a,n=v.d
B.b.I(p,new A.ad(A.a([0,9,21],x.Y),new C.b21(o,e,n),x.Q))
p=A.Z(p,B.j,B.d,B.f,0)
w=t?"Bedrag excl. BTW":"Amount ex VAT"
o=A.c(w+": \u20ac "+B.e.S(o.b,2),u,u,u,u,L.az,u,u,u)
w=t?"Totaal incl. BTW":"Total incl VAT"
n=A.b1(A.G(A.a([r,B.y,p,B.y,o,A.c(w+": \u20ac "+B.e.S(n,2),u,u,u,u,L.az,u,u,u)],q),B.q,B.d,B.I),u,360)
r=A.ca(A.c(t?"Annuleren":"Cancel",u,u,u,u,u,u,u,u),new C.b22(d),u)
p=A.cE(u,u,B.l,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u)
return Q.el(A.a([r,A.bZ(A.c(t?"Aanmaken":"Create",u,u,u,u,B.bC,u,u,u),new C.b23(d),p)],q),n,u,s)},
$S:z+1}
C.b21.prototype={
$1(d){var w=null,v=this.a
return new A.a9(B.oD,G.b7y(A.c(""+d+"%",w,w,w,w,w,w,w,w),w,new C.b20(v,this.b,d,this.c),v.a===d,w),w)},
$S:271}
C.b20.prototype={
$1(d){var w=this
return w.b.$1(new C.b2_(w.a,w.c,w.d))},
$S:8}
C.b2_.prototype={
$0(){var w=this.b,v=this.a
v.a=w
v.b=this.c/(1+w/100)},
$S:0}
C.b22.prototype={
$0(){A.aQ(this.a,!1).aU(!1)
return null},
$S:0}
C.b23.prototype={
$0(){A.aQ(this.a,!1).aU(!0)
return null},
$S:0}
C.b26.prototype={
$0(){return this.a.d=!0},
$S:0}
C.b27.prototype={
$0(){return this.a.d=!1},
$S:0}
C.b2e.prototype={
$1(d){var w=this
return new A.eG(new C.b2d(w.a,w.b,w.c,w.d),null)},
$S:18}
C.b2d.prototype={
$2(d,e){var w,v=this,u=null,t=v.b,s=A.c(t?"Nieuwe investering":"New investment",u,u,u,u,u,u,u,u),r=A.bQ(u,B.S,!1,u,!0,B.n,u,A.bS(),v.c,u,u,u,u,u,2,A.by(u,P.i2,u,u,u,u,u,u,!0,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,!0,u,u,t?"Omschrijving":"Description",!0,!0,!1,u,u,u,u,u,u,u,u,u,u,u,u,u,u),B.r,!0,u,!0,u,!1,u,B.R,u,u,u,u,u,u,u,u,1,u,u,!1,"\u2022",u,u,u,u,u,!1,u,u,!1,u,!0,u,B.N,u,u,u,u,u,u,u,u,u,u,u,u,!0,B.K,u,B.Y,u,u,u,u),q=x.p,p=A.a([A.c(t?"Afschrijving:":"Depreciation:",u,u,u,u,F.eh,u,u,u),K.br],q)
B.b.I(p,new A.ad(A.a([3,5,10],x.Y),new C.b2a(v.a,t,e),x.Q))
p=A.Z(p,B.j,B.d,B.f,0)
w=t?"Aankoopbedrag":"Purchase amount"
w=A.b1(A.G(A.a([r,B.y,p,B.y,A.c(w+": \u20ac "+B.e.S(v.d,2),u,u,u,u,L.az,u,u,u)],q),B.q,B.d,B.I),u,360)
r=A.ca(A.c(t?"Annuleren":"Cancel",u,u,u,u,u,u,u,u),new C.b2b(d),u)
p=A.cE(u,u,B.l,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u,u)
return Q.el(A.a([r,A.bZ(A.c(t?"Aanmaken":"Create",u,u,u,u,B.bC,u,u,u),new C.b2c(d),p)],q),w,u,s)},
$S:z+1}
C.b2a.prototype={
$1(d){var w=null,v=""+d,u=this.a
return new A.a9(B.oD,G.b7y(A.c(this.b?v+" jaar":v+" yr",w,w,w,w,w,w,w,w),w,new C.b29(u,this.c,d),u.a===d,w),w)},
$S:271}
C.b29.prototype={
$1(d){return this.b.$1(new C.b28(this.a,this.c))},
$S:8}
C.b28.prototype={
$0(){return this.a.a=this.b},
$S:0}
C.b2b.prototype={
$0(){A.aQ(this.a,!1).aU(!1)
return null},
$S:0}
C.b2c.prototype={
$0(){A.aQ(this.a,!1).aU(!0)
return null},
$S:0}
C.b2f.prototype={
$0(){return this.a.d=!0},
$S:0}
C.b2g.prototype={
$0(){return this.a.d=!1},
$S:0};(function installTearOffs(){var w=a._instance_0u,v=a.installInstanceTearOff
w(C.QJ.prototype,"ga0J","yH",0)
var u
v(u=C.QI.prototype,"gaDT",0,0,null,["$1$silent","$0"],["uI","aDU"],3,0,0)
w(u,"gawK","EV",0)
w(u,"gazG","ur",0)
w(u,"gani","xK",0)
w(u,"ganl","xL",0)})();(function inheritance(){var w=a.inheritMany
w(A.a_,[C.tk,C.y2])
w(A.a3,[C.QJ,C.QI])
w(A.fZ,[C.b2y,C.b2z,C.b2B,C.b2D,C.b2F,C.b2r,C.b2v,C.b2s,C.b1W,C.b1X,C.b1Y,C.b1Z,C.b2o,C.b2p,C.b2q,C.b2h,C.b2i,C.b2j,C.b2_,C.b22,C.b23,C.b26,C.b27,C.b28,C.b2b,C.b2c,C.b2f,C.b2g])
w(A.eK,[C.b2A,C.b2C,C.b2H,C.b2G,C.b2E,C.b2u,C.b2m,C.b2n,C.b25,C.b21,C.b20,C.b2e,C.b2a,C.b29])
w(A.j9,[C.b2w,C.b2x,C.b2t,C.b2l,C.b2k,C.b24,C.b2d])})()
A.fB(b.typeUniverse,JSON.parse('{"y2":{"a_":[],"h":[]},"tk":{"a_":[],"h":[]},"QJ":{"a3":["tk"]},"QI":{"a3":["y2"]}}'))
var y={d:"https://bigdogg-production.up.railway.app/api/v1/banking/transactions/"}
var x=(function rtii(){var w=A.aa
return{C:w("lI"),t:w("C<ah<p,@>>"),p:w("C<h>"),Y:w("C<x>"),D:w("P<ah<p,@>>"),P:w("ah<p,@>"),Q:w("ad<x,h>"),w:w("hq"),K:w("N"),N:w("p"),l:w("h"),q:w("nW"),y:w("M"),i:w("R"),z:w("@"),g:w("P<@>?"),h:w("ah<p,@>?"),U:w("ah<@,@>?"),X:w("N?"),T:w("p?"),H:w("~")}})();(function constants(){var w=a.makeConstList
D.Qo=new A.a6(12,0,12,0)
D.QB=new A.a6(16,16,16,6)
D.vJ=new A.a6(20,0,20,0)
D.QH=new A.a6(22,12,22,12)
D.wr=new A.aj(57582,"MaterialIcons",null,!1)
D.wA=new A.aj(58435,"MaterialIcons",null,!1)
D.wH=new A.aj(58839,"MaterialIcons",null,!1)
D.RX=new A.aj(62151,"MaterialIcons",null,!1)
D.SI=new A.dj(null,null,null,null,null,B.l,null,null,null)
D.T6=new A.aq(E.wG,null,null,null,null)
D.Tn=new A.aq(E.jg,null,B.aq,null,null)
D.Tt=new A.aq(E.wu,16,B.i,null,null)
D.TJ=new A.aq(X.py,56,B.z,null,null)
D.TK=new A.aq(E.wm,16,B.i,null,null)
D.S6=new A.aj(62537,"MaterialIcons",null,!1)
D.TL=new A.aq(D.S6,64,I.ak,null,null)
D.TU=new A.aq(D.wr,16,I.ak,null,null)
D.a_s=w([],x.t)
D.a0o=w(["januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"],A.aa("C<p>"))
D.Qh=new A.a6(0,32,0,32)
D.a4c=new A.a9(D.Qh,O.b2,null)
D.a8o=new A.cc(null,60,null,null)
D.I9=new A.cc(null,80,null,null)
D.abd=new A.q(!0,I.ak,null,null,null,null,12,B.E,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)
D.ac0=new A.q(!0,B.z,null,null,null,null,null,B.E,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)
D.aev=new A.q(!0,B.G,null,null,null,null,null,B.E,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)})()};
(a=>{a["igjI7fKxZPo6eD+8+jH+n3S2lb0="]=a.current})($__dart_deferred_initializers__);