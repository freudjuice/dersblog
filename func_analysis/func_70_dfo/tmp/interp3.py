from scipy.interpolate import Rbf
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy.linalg as lin
import scipy.linalg as slin
import numpy as np, math
import itertools

LIM=5.0
N = 20

def rosenbrock(x):
    return (1 - x[0])**2 + 100*(x[1] - x[0]**2)**2

def Rosenbrock(x,y):
    return (1 - x)**2 + 100*(y - x**2)**2

def peaks(x):
    return \
    3*(1-x[0])**2 * np.exp(-x[0]**2 - (x[1] + 1)**2) - \
    10*(1/5. * x[0] - x[0]**3 - x[1]**5) * np.exp(-x[0]**2 - x[1]**2) - \
    1/3. * np.exp(-(x[0]+1)**2 - x[0]**2)  + \
    np.log(LIM+x[0]) + np.log(LIM-x[0]) + \
    np.log(LIM+x[1]) + np.log(LIM-x[1]) 

def Peaks(x1,x2):
    return \
    3*(1-x1)**2 * np.exp(-x1**2 - (x2 + 1)**2) - \
    10*(1/5. * x1 - x1**3 - x2**5) * np.exp(-x1**2 - x2**2) - \
    1/3. * np.exp(-(x1+1)**2 - x1**2)


def get_boundaries_intersections(z, d, trust_radius):
    a = np.dot(d, d)
    b = 2 * np.dot(z, d)
    c = np.dot(z, z) - trust_radius**2
    print (b,a,c)
    print (b*b - 4*a*c)
    sqrt_discriminant = math.sqrt(b*b - 4*a*c)
    aux = b + math.copysign(sqrt_discriminant, b)
    ta = -aux / (2*a)
    tb = -2*c / aux
    return sorted([ta, tb])

def random_ball(num_points, dimension, radius=1):
    from numpy import random, linalg
    random_directions = random.normal(size=(dimension,num_points))
    random_directions /= linalg.norm(random_directions, axis=0)
    random_radii = random.random(num_points) ** (1/dimension)
    return radius * (random_directions * random_radii).T

def get_fvals_in_region(xcurr, f, radius):    
    b = random_ball(N, 2, radius)
    pts = xcurr+b
    vals = [f(p) for p in pts]
    return xcurr+b, np.array(vals)

def eval_model(xcurr, f, radius):
    xs,vs = get_fvals_in_region(xcurr, f, 0.5)
    res = []
    for i in range(vs.shape[0]):
        res.append((xs[i,0],xs[i,1],vs[i]))
    res = np.array(res).reshape(vs.shape[0], 3)
    xi = res[:,[0,1]]
    yi = res[:,[2]]
    xi = np.hstack((xi, np.ones((1,len(xi))).T  ))
    D = xi.shape[1]
    X_train = []
    for row in xi:
        X_train.append([row[i]*row[j] for i,j in itertools.product(range(D),range(D)) ])
    X_train = np.array(X_train)
    coef,_,_,_ = lin.lstsq(X_train, yi)
    coefs = coef.reshape(3,3)
    jac = (2 * np.dot(coefs[:2,:2],np.array(xcurr).reshape(2,1)))
    hess = 2*coefs[:2,:2]
    def q_interp(x1,x2):
        x = np.array([[x1,x2,1]])
        A = coef.reshape(3,3)
        res = np.dot(np.dot(x,A),x.T)
        return np.float(res)
    
    val = q_interp(xcurr[0],xcurr[1])
    return val, jac, hess
    
#x0 = np.array([1.0,2.5])
#x0 = np.array([-2.0,2.5])
x0 = np.array([-2.0,-1.0])


np.random.seed(0)
initial_trust_radius=1.0
trust_radius = initial_trust_radius
gtol = 1.0
#gtol = 1.5
alpha = 1.0
eta=0.15
max_trust_radius=1000.0
model_radius = 0.5

xcurr = x0
f = rosenbrock
F = Rosenbrock
#f = peaks
#F = Peaks
val, jac, hess = eval_model(xcurr, f, model_radius)
print (val)
print (jac)
print (hess)

for i in range(10):
    print ('iteration', i)
    print ('norm jac', lin.norm(jac))
    print ('trust region',trust_radius)
    model_radius = trust_radius
    #if lin.norm(jac) < gtol: break
    x = np.linspace(-3,3,250)
    y = np.linspace(-3,3,250)
    X, Y = np.meshgrid(x, y)
    Z = F(X, Y)
    fig = plt.figure()
    ax = fig.gca()
    
    ax.contour(X,Y,Z, 50, cmap = 'jet')
    ax.plot(xcurr[0],xcurr[1], 'r.')
    circle=plt.Circle((xcurr[0],xcurr[1]),trust_radius,fill=False)
    ax.add_artist(circle)

    val, jac, hess = eval_model(xcurr, f, model_radius)
    newton_dir = -np.dot(lin.inv(hess.reshape(2,2)),jac)
    newton_dir = newton_dir.flatten()
    print ('jac',jac.reshape(2,1))
    print ('hess',hess.reshape(2,2))
    
    p_best = xcurr + newton_dir
    p_u = jac

    hits_boundary,p = None,None
    
    print ('p_u',p_u)
    p_u_norm = lin.norm(p_u)
    
    if lin.norm(newton_dir) < trust_radius:
        hits_boundary,p=False,p_best
        print ('method 1',hits_boundary,p)       
    elif p_u_norm >= trust_radius:
        p_boundary = p_u * (trust_radius / p_u_norm)
        hits_boundary,p=True, xcurr-p_boundary.flatten()
        print ('method 2',hits_boundary,p)
    else:        
        _, tb = get_boundaries_intersections(p_u, p_best - p_u,trust_radius)
        p_boundary = p_u + tb * (p_best - p_u)
        hits_boundary,p=True,p_boundary
        print ('method 3',tb)

    mv,dummy1,dummy2  = eval_model(p,f,trust_radius)
    model_prop_value = np.float(mv)
    mv,dummy1,dummy2  =  eval_model(xcurr,f,trust_radius)
    model_curr_value = np.float(mv)

    real_prop_value = f(p)
    real_curr_value = f(xcurr)

    print ('model params: mprop, mcurr, realprop, realcurr')
    print (model_prop_value, model_curr_value, real_prop_value,real_curr_value)

    rho = (real_curr_value-real_prop_value) / (model_curr_value-model_prop_value)
    print ('rho',rho)
    if rho < 0.25:
        trust_radius *= 0.25
    elif rho > 0.75 and hits_boundary:
        print ('larger')
        trust_radius = min(2*trust_radius, max_trust_radius)
        
    if rho > eta:
        xcurr = p
    else:
        print ('do nothing')

    print ('xcurr',xcurr)
    print ('\n')
    ax.plot(xcurr[0],xcurr[1], 'rx')
    
    plt.savefig('/tmp/quad/out-%d.png' % i)
    #break

