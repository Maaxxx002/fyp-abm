import numpy as np
from scipy.integrate import solve_ivp

def sm(x,w=7):
    x=np.asarray(x,float)
    if len(x)<w: return x
    k=np.ones(w)/w
    return np.convolve(np.pad(x,(w//2,w//2),mode='edge'),k,mode='valid')[:len(x)]

def q_times(y):
    """times at which 10/25/50/75/90% of the cumulative total is reached"""
    c=np.cumsum(np.asarray(y,float)); T=c[-1]
    if T<=0: return None
    return [float(np.searchsorted(c,f*T)) for f in (0.10,0.25,0.50,0.75,0.90)]

def metrics(y):
    y=np.asarray(y,float)
    if y.sum()<=0: return {k:np.nan for k in ("sym_pt","sym_q","width50","peak_share","dur")}
    ys=sm(y); ip=int(ys.argmax()); pk=ys[ip]
    # 1. Weitz pointwise symmetry
    pre=np.where(ys[:ip]<=0.1*pk)[0]
    if len(pre) and ip+(ip-pre[-1])<len(ys):
        dt=ip-pre[-1]; post=ys[ip+dt]; sym_pt=(0.1*pk)/post if post>0 else np.inf
    else: sym_pt=np.nan
    # 2. quantile symmetry from the cumulative curve
    q=q_times(y)
    sym_q=(q[4]-q[2])/max(q[2]-q[0],1e-9) if q else np.nan
    # 3. width at half max, normalised by the 10-90 duration
    above=np.where(ys>=0.5*pk)[0]
    dur=(q[4]-q[0]) if q else np.nan
    width50=(above[-1]-above[0])/dur if (len(above)>1 and dur and dur>0) else np.nan
    # 4. share of the epidemic on its single busiest day
    peak_share=y.max()/y.sum()
    return dict(sym_pt=sym_pt,sym_q=sym_q,width50=width50,peak_share=peak_share,dur=dur)

BETA,MU,GAMMA,FD,N0=0.5,0.5,1/6,0.01,1e-6
def ode(dc,k=2,T_H=14,R0=3.0,days=900):
    gH=1/T_H; beta=R0*GAMMA
    def rhs(t,y):
        S,E,I,H,R,D=y; delta=gH*H
        foi=beta*S*I/(1+(delta/dc)**k) if dc>0 else beta*S*I
        return [-foi,foi-MU*E,MU*E-GAMMA*I,FD*GAMMA*I-gH*H,(1-FD)*GAMMA*I,gH*H]
    s=solve_ivp(rhs,[0,days],[1-N0,0,N0,0,0,0],dense_output=True,max_step=0.5,rtol=1e-10,atol=1e-14)
    t=np.arange(days); y=s.sol(t)
    inc=beta*y[0]*y[2]/(1+((gH*y[3])/dc)**k) if dc>0 else beta*y[0]*y[2]
    return inc, gH*y[3]

def _report():
    print("ODE ground truth: does the signature measured on INCIDENCE match the one on DEATHS?\n")
    cases=[("control (no behaviour)",0,2,14),("weak aware dc=2e-5",2e-5,2,14),
           ("Weitz dc=5e-6",5e-6,2,14),("strong aware dc=1e-6",1e-6,2,14),
           ("Weitz k=1",5e-6,1,14),("Weitz T_H=28",5e-6,2,28)]
    print(f"{'case':<26}{'sym_q(inc)':>11}{'sym_q(dth)':>11}{'w50(inc)':>10}{'w50(dth)':>10}{'symPT(inc)':>12}{'symPT(dth)':>12}")
    print("-"*92)
    rows=[]
    for lab,dc,k,TH in cases:
        inc,dth=ode(dc,k,TH); mi,md=metrics(inc),metrics(dth)
        rows.append((lab,mi,md))
        print(f"{lab:<26}{mi['sym_q']:>11.2f}{md['sym_q']:>11.2f}{mi['width50']:>10.3f}{md['width50']:>10.3f}{mi['sym_pt']:>12.2f}{md['sym_pt']:>12.2f}")
    si=[r[1]['sym_q'] for r in rows]; sd=[r[2]['sym_q'] for r in rows]
    wi=[r[1]['width50'] for r in rows]; wd=[r[2]['width50'] for r in rows]
    print(f"\nrank correlation incidence vs deaths:  sym_q {np.corrcoef(np.argsort(np.argsort(si)),np.argsort(np.argsort(sd)))[0,1]:.3f}"
          f"   width50 {np.corrcoef(np.argsort(np.argsort(wi)),np.argsort(np.argsort(wd)))[0,1]:.3f}")

if __name__ == "__main__":
    _report()
