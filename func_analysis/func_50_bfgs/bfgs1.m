
x=[-1.0;0];
%x=[-1.2;1];
%H=diag([2,6]);
H=eye(2);

%exit;

tol = 10^(-20);

[y,grad]=rosenbrock_withjac(x);

dist=2*tol;
epsilon = tol;

iter=0;
%while dist>tol || abs(xt(1)-x(1)) > epsilon || abs(xt(2)-x(2)) > epsilon
while norm(grad) > 1e-6
    
    [value,grad]=rosenbrock_withjac(x);
    p=-H*grad;

    lambda=linesearch_secant(@rosenbrock_withjac,p,x);

    iter=iter+1;
    xt = x;
    x=x+lambda*p;
      
    s=lambda*p;

    dist=norm(s);
    
    [newvalue,newgrad]=rosenbrock_withjac(x);

    y = newgrad-grad;

    rho=1/(y'*s);

    H=(eye(2)-rho*s*y')*H*(eye(2)-rho*y*s')+rho*s*s';
    disp('lambda:')
    disp(lambda)
    
end
disp('Ending (x,y):')
disp(xt)
iter
