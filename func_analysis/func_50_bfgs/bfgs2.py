import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy.linalg as lin

eps = np.sqrt(np.finfo(float).eps)

def _approx_fprime_helper(xk, f, epsilon):
    f0 = f(xk)
    grad = np.zeros((len(xk),), float)
    ei = np.zeros((len(xk),), float)
    for k in range(len(xk)):
        ei[k] = 1.0
        d = epsilon * ei
        df = (f(xk + d) - f0) / d[k]
        if not np.isscalar(df):
            try:
                df = df.item()
            except (ValueError, AttributeError):
                raise ValueError("The user-provided "
                                 "objective function must "
                                 "return a scalar value.")
        grad[k] = df
        ei[k] = 0.0
    return grad

def rosen(x):
    return 100*(x[1]-x[0]**2)**2+(1-x[0])**2

def rosen_approx(x):
    g = _approx_fprime_helper(x, rosen, eps)
    return rosen(x),g

def linesearch_secant(f, d, x):
    epsilon=10**(-5)
    max = 500
    alpha_curr=0
    alpha=10**-5
    y,grad=f(x)
    dphi_zero=np.dot(np.array(grad).T,d)

    dphi_curr=dphi_zero
    i=0;
    while np.abs(dphi_curr)>epsilon*np.abs(dphi_zero):
        alpha_old=alpha_curr
        alpha_curr=alpha
        dphi_old=dphi_curr
        y,grad=f(x+alpha_curr*d)
        dphi_curr=np.dot(np.array(grad).T,d)
        alpha=(dphi_curr*alpha_old-dphi_old*alpha_curr)/(dphi_curr-dphi_old);
        i += 1
        if (i >= max) and (np.abs(dphi_curr)>epsilon*np.abs(dphi_zero)):
            print('Line search terminating with number of iterations:')
            print(i)
            print(alpha)
            break
        
    return alpha

x=np.array([-1.0,0])

H = np.eye(2)

tol = 1e-20

y,grad = rosen_approx(x)

dist=2*tol
epsilon = tol

iter=0;

while lin.norm(grad)>1e-6:
    value,grad=rosen_approx(x)
    p=np.dot(-H,grad)
    lam = linesearch_secant(rosen_approx,p,x)
    iter += 1
    xt = x
    x = x + lam*p
    s = lam*p
    dist=lin.norm(s)
    newvalue,newgrad=rosen_approx(x)
    y = np.array(newgrad)-grad
    rho=1/np.dot(y.T,s)
    s = s.reshape(2,1)
    y = y.reshape(2,1)
    tmp1 = np.eye(2)-rho*np.dot(s,y.T)
    tmp2 = np.eye(2)-rho*np.dot(y,s.T)
    tmp3 = rho*np.dot(s,s.T)
    H= np.dot(np.dot(tmp1,H),tmp2) + tmp3
    #print ('lambda:',lam)

print (xt)
print ('iter',iter)

