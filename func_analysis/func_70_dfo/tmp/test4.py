from __future__ import division, print_function, absolute_import
import numpy as np
from copy import deepcopy
from numpy.linalg import norm
from scipy.linalg import get_blas_funcs
from scipy.optimize import minimize

class HessianUpdateStrategy(object):
    """Interface for implementing Hessian update strategies.

    Many optimization methods make use of Hessian (or inverse Hessian)
    approximations, such as the quasi-Newton methods BFGS, SR1, L-BFGS.
    Some of these  approximations, however, do not actually need to store
    the entire matrix or can compute the internal matrix product with a
    given vector in a very efficiently manner. This class serves as an
    abstract interface between the optimization algorithm and the
    quasi-Newton update strategies, giving freedom of implementation
    to store and update the internal matrix as efficiently as possible.
    Different choices of initialization and update procedure will result
    in different quasi-Newton strategies.

    Four methods should be implemented in derived classes: ``initialize``,
    ``update``, ``dot`` and ``get_matrix``.

    Notes
    -----
    Any instance of a class that implements this interface,
    can be accepted by the method ``minimize`` and used by
    the compatible solvers to approximate the Hessian (or
    inverse Hessian) used by the optimization algorithms.
    """

    def initialize(self, n, approx_type):
        """Initialize internal matrix.

        Allocate internal memory for storing and updating
        the Hessian or its inverse.

        Parameters
        ----------
        n : int
            Problem dimension.
        approx_type : {'hess', 'inv_hess'}
            Selects either the Hessian or the inverse Hessian.
            When set to 'hess' the Hessian will be stored and updated.
            When set to 'inv_hess' its inverse will be used instead.
        """
        raise NotImplementedError("The method ``initialize(n, approx_type)``"
                                  " is not implemented.")

    def update(self, delta_x, delta_grad):
        """Update internal matrix.

        Update Hessian matrix or its inverse (depending on how 'approx_type'
        is defined) using information about the last evaluated points.

        Parameters
        ----------
        delta_x : ndarray
            The difference between two points the gradient
            function have been evaluated at: ``delta_x = x2 - x1``.
        delta_grad : ndarray
            The difference between the gradients:
            ``delta_grad = grad(x2) - grad(x1)``.
        """
        raise NotImplementedError("The method ``update(delta_x, delta_grad)``"
                                  " is not implemented.")

    def dot(self, p):
        """Compute the product of the internal matrix with the given vector.

        Parameters
        ----------
        p : array_like
            1-d array representing a vector.

        Returns
        -------
        Hp : array
            1-d  represents the result of multiplying the approximation matrix
            by vector p.
        """
        raise NotImplementedError("The method ``dot(p)``"
                                  " is not implemented.")

    def get_matrix(self):
        """Return current internal matrix.

        Returns
        -------
        H : ndarray, shape (n, n)
            Dense matrix containing either the Hessian
            or its inverse (depending on how 'approx_type'
            is defined).
        """
        raise NotImplementedError("The method ``get_matrix(p)``"
                                  " is not implemented.")


class FullHessianUpdateStrategy(HessianUpdateStrategy):
    """Hessian update strategy with full dimensional internal representation.
    """
    _syr = get_blas_funcs('syr', dtype='d')  # Symmetric rank 1 update
    _syr2 = get_blas_funcs('syr2', dtype='d')  # Symmetric rank 2 update
    # Symmetric matrix-vector product
    _symv = get_blas_funcs('symv', dtype='d')

    def __init__(self, init_scale='auto'):
        self.init_scale = init_scale
        # Until initialize is called we can't really use the class,
        # so it makes sense to set everything to None.
        self.first_iteration = None
        self.approx_type = None
        self.B = None
        self.H = None

    def initialize(self, n, approx_type):
        """Initialize internal matrix.

        Allocate internal memory for storing and updating
        the Hessian or its inverse.

        Parameters
        ----------
        n : int
            Problem dimension.
        approx_type : {'hess', 'inv_hess'}
            Selects either the Hessian or the inverse Hessian.
            When set to 'hess' the Hessian will be stored and updated.
            When set to 'inv_hess' its inverse will be used instead.
        """
        self.first_iteration = True
        self.n = n
        self.approx_type = approx_type
        if approx_type not in ('hess', 'inv_hess'):
            raise ValueError("`approx_type` must be 'hess' or 'inv_hess'.")
        # Create matrix
        if self.approx_type == 'hess':
            self.B = np.eye(n, dtype=float)
        else:
            self.H = np.eye(n, dtype=float)

    def _auto_scale(self, delta_x, delta_grad):
        # Heuristic to scale matrix at first iteration.
        # Described in Nocedal and Wright "Numerical Optimization"
        # p.143 formula (6.20).
        s_norm2 = np.dot(delta_x, delta_x)
        y_norm2 = np.dot(delta_grad, delta_grad)
        ys = np.abs(np.dot(delta_grad, delta_x))
        if ys == 0.0 or y_norm2 == 0 or s_norm2 == 0:
            return 1
        if self.approx_type == 'hess':
            return y_norm2 / ys
        else:
            return ys / y_norm2

    def _update_implementation(self, delta_x, delta_grad):
        raise NotImplementedError("The method ``_update_implementation``"
                                  " is not implemented.")

    def update(self, delta_x, delta_grad):
        """Update internal matrix.

        Update Hessian matrix or its inverse (depending on how 'approx_type'
        is defined) using information about the last evaluated points.

        Parameters
        ----------
        delta_x : ndarray
            The difference between two points the gradient
            function have been evaluated at: ``delta_x = x2 - x1``.
        delta_grad : ndarray
            The difference between the gradients:
            ``delta_grad = grad(x2) - grad(x1)``.
        """
        if np.all(delta_x == 0.0):
            return
        if np.all(delta_grad == 0.0):
            warn('delta_grad == 0.0. Check if the approximated '
                 'function is linear. If the function is linear '
                 'better results can be obtained by defining the '
                 'Hessian as zero instead of using quasi-Newton '
                 'approximations.', UserWarning)
            return
        if self.first_iteration:
            # Get user specific scale
            if self.init_scale == "auto":
                scale = self._auto_scale(delta_x, delta_grad)
            else:
                scale = float(self.init_scale)
            # Scale initial matrix with ``scale * np.eye(n)``
            if self.approx_type == 'hess':
                self.B *= scale
            else:
                self.H *= scale
            self.first_iteration = False
        self._update_implementation(delta_x, delta_grad)

    def dot(self, p):
        """Compute the product of the internal matrix with the given vector.

        Parameters
        ----------
        p : array_like
            1-d array representing a vector.

        Returns
        -------
        Hp : array
            1-d  represents the result of multiplying the approximation matrix
            by vector p.
        """
        if self.approx_type == 'hess':
            return self._symv(1, self.B, p)
        else:
            return self._symv(1, self.H, p)

    def get_matrix(self):
        """Return the current internal matrix.

        Returns
        -------
        M : ndarray, shape (n, n)
            Dense matrix containing either the Hessian or its inverse
            (depending on how `approx_type` was defined).
        """
        if self.approx_type == 'hess':
            M = np.copy(self.B)
        else:
            M = np.copy(self.H)
        li = np.tril_indices_from(M, k=-1)
        M[li] = M.T[li]
        return M


class BFGS(FullHessianUpdateStrategy):
    """Broyden-Fletcher-Goldfarb-Shanno (BFGS) Hessian update strategy.

    Parameters
    ----------
    exception_strategy : {'skip_update', 'damp_update'}, optional
        Define how to proceed when the curvature condition is violated.
        Set it to 'skip_update' to just skip the update. Or, alternatively,
        set it to 'damp_update' to interpolate between the actual BFGS
        result and the unmodified matrix. Both exceptions strategies
        are explained  in [1]_, p.536-537.
    min_curvature : float
        This number, scaled by a normalization factor, defines the
        minimum curvature ``dot(delta_grad, delta_x)`` allowed to go
        unaffected by the exception strategy. By default is equal to
        1e-8 when ``exception_strategy = 'skip_update'`` and equal
        to 0.2 when ``exception_strategy = 'damp_update'``.
    init_scale : {float, 'auto'}
        Matrix scale at first iteration. At the first
        iteration the Hessian matrix or its inverse will be initialized
        with ``init_scale*np.eye(n)``, where ``n`` is the problem dimension.
        Set it to 'auto' in order to use an automatic heuristic for choosing
        the initial scale. The heuristic is described in [1]_, p.143.
        By default uses 'auto'.

    Notes
    -----
    The update is based on the description in [1]_, p.140.

    References
    ----------
    .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
           Second Edition (2006).
    """

    def __init__(self, exception_strategy='skip_update', min_curvature=None,
                 init_scale='auto'):
        if exception_strategy == 'skip_update':
            if min_curvature is not None:
                self.min_curvature = min_curvature
            else:
                self.min_curvature = 1e-8
        elif exception_strategy == 'damp_update':
            if min_curvature is not None:
                self.min_curvature = min_curvature
            else:
                self.min_curvature = 0.2
        else:
            raise ValueError("`exception_strategy` must be 'skip_update' "
                             "or 'damp_update'.")

        super(BFGS, self).__init__(init_scale)
        self.exception_strategy = exception_strategy

    def _update_inverse_hessian(self, ys, Hy, yHy, s):
        """Update the inverse Hessian matrix.

        BFGS update using the formula:

            ``H <- H + ((H*y).T*y + s.T*y)/(s.T*y)^2 * (s*s.T)
                     - 1/(s.T*y) * ((H*y)*s.T + s*(H*y).T)``

        where ``s = delta_x`` and ``y = delta_grad``. This formula is
        equivalent to (6.17) in [1]_ written in a more efficient way
        for implementation.

        References
        ----------
        .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
               Second Edition (2006).
        """
        self.H = self._syr2(-1.0 / ys, s, Hy, a=self.H)
        self.H = self._syr((ys+yHy)/ys**2, s, a=self.H)

    def _update_hessian(self, ys, Bs, sBs, y):
        """Update the Hessian matrix.

        BFGS update using the formula:

            ``B <- B - (B*s)*(B*s).T/s.T*(B*s) + y*y^T/s.T*y``

        where ``s`` is short for ``delta_x`` and ``y`` is short
        for ``delta_grad``. Formula (6.19) in [1]_.

        References
        ----------
        .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
               Second Edition (2006).
        """
        self.B = self._syr(1.0 / ys, y, a=self.B)
        self.B = self._syr(-1.0 / sBs, Bs, a=self.B)

    def _update_implementation(self, delta_x, delta_grad):
        # Auxiliary variables w and z
        if self.approx_type == 'hess':
            w = delta_x
            z = delta_grad
        else:
            w = delta_grad
            z = delta_x
        # Do some common operations
        wz = np.dot(w, z)
        Mw = self.dot(w)
        wMw = Mw.dot(w)
        # Guarantee that wMw > 0 by reinitializing matrix.
        # While this is always true in exact arithmetics,
        # indefinite matrix may appear due to roundoff errors.
        if wMw <= 0.0:
            scale = self._auto_scale(delta_x, delta_grad)
            # Reinitialize matrix
            if self.approx_type == 'hess':
                self.B = scale * np.eye(self.n, dtype=float)
            else:
                self.H = scale * np.eye(self.n, dtype=float)
            # Do common operations for new matrix
            Mw = self.dot(w)
            wMw = Mw.dot(w)
        # Check if curvature condition is violated
        if wz <= self.min_curvature * wMw:
            # If the option 'skip_update' is set
            # we just skip the update when the condion
            # is violated.
            if self.exception_strategy == 'skip_update':
                return
            # If the option 'damp_update' is set we
            # interpolate between the actual BFGS
            # result and the unmodified matrix.
            elif self.exception_strategy == 'damp_update':
                update_factor = (1-self.min_curvature) / (1 - wz/wMw)
                z = update_factor*z + (1-update_factor)*Mw
                wz = np.dot(w, z)
        # Update matrix
        if self.approx_type == 'hess':
            self._update_hessian(wz, Mw, wMw, z)
        else:
            self._update_inverse_hessian(wz, Mw, wMw, z)


class SR1(FullHessianUpdateStrategy):
    """Symmetric-rank-1 Hessian update strategy.

    Parameters
    ----------
    min_denominator : float
        This number, scaled by a normalization factor,
        defines the minimum denominator magnitude allowed
        in the update. When the condition is violated we skip
        the update. By default uses ``1e-8``.
    init_scale : {float, 'auto'}, optional
        Matrix scale at first iteration. At the first
        iteration the Hessian matrix or its inverse will be initialized
        with ``init_scale*np.eye(n)``, where ``n`` is the problem dimension.
        Set it to 'auto' in order to use an automatic heuristic for choosing
        the initial scale. The heuristic is described in [1]_, p.143.
        By default uses 'auto'.

    Notes
    -----
    The update is based on the description in [1]_, p.144-146.

    References
    ----------
    .. [1] Nocedal, Jorge, and Stephen J. Wright. "Numerical optimization"
           Second Edition (2006).
    """

    def __init__(self, min_denominator=1e-8, init_scale='auto'):
        self.min_denominator = min_denominator
        super(SR1, self).__init__(init_scale)

    def _update_implementation(self, delta_x, delta_grad):
        # Auxiliary variables w and z
        #print ('here---------------')
        if self.approx_type == 'hess':
            #print ('hess')
            w = delta_x
            z = delta_grad
        else:
            w = delta_grad
            z = delta_x
        # Do some common operations
        Mw = self.dot(w)
        z_minus_Mw = z - Mw
        denominator = np.dot(w, z_minus_Mw)
        # If the denominator is too small
        # we just skip the update.
        if np.abs(denominator) <= self.min_denominator*norm(w)*norm(z_minus_Mw):
            return
        # Update matrix
        if self.approx_type == 'hess':
            self.B = self._syr(1/denominator, z_minus_Mw, a=self.B)
        else:
            self.H = self._syr(1/denominator, z_minus_Mw, a=self.H)


class Rosenbrock:

    def __init__(self, n=2, random_state=0):
        rng = np.random.RandomState(random_state)
        self.x0 = rng.uniform(-1, 1, n)
        self.x_opt = np.ones(n)

    def fun(self, x):
        x = np.asarray(x)
        r = np.sum(100.0 * (x[1:] - x[:-1]**2.0)**2.0 + (1 - x[:-1])**2.0,
                   axis=0)
        return r

    def grad(self, x):
        x = np.asarray(x)
        xm = x[1:-1]
        xm_m1 = x[:-2]
        xm_p1 = x[2:]
        der = np.zeros_like(x)
        der[1:-1] = (200 * (xm - xm_m1**2) -
                     400 * (xm_p1 - xm**2) * xm - 2 * (1 - xm))
        der[0] = -400 * x[0] * (x[1] - x[0]**2) - 2 * (1 - x[0])
        der[-1] = 200 * (x[-1] - x[-2]**2)
        return der

    def hess(self, x):
        x = np.atleast_1d(x)
        H = np.diag(-400 * x[:-1], 1) - np.diag(400 * x[:-1], -1)
        diagonal = np.zeros(len(x), dtype=x.dtype)
        diagonal[0] = 1200 * x[0]**2 - 400 * x[1] + 2
        diagonal[-1] = 200
        diagonal[1:-1] = 202 + 1200 * x[1:-1]**2 - 400 * x[2:]
        H = H + np.diag(diagonal)
        return H

prob = Rosenbrock(n=5)
# Define iteration points
x_list = [[0.0976270, 0.4303787, 0.2055267, 0.0897663, -0.15269040],
          [0.1847239, 0.0505757, 0.2123832, 0.0255081, 0.00083286],
          [0.2142498, -0.0188480, 0.0503822, 0.0347033, 0.03323606],
          [0.2071680, -0.0185071, 0.0341337, -0.0139298, 0.02881750],
          [0.1533055, -0.0322935, 0.0280418, -0.0083592, 0.01503699],
          [0.1382378, -0.0276671, 0.0266161, -0.0074060, 0.02801610],
          [0.1651957, -0.0049124, 0.0269665, -0.0040025, 0.02138184],
          [0.2354930, 0.0443711, 0.0173959, 0.0041872, 0.00794563],
          [0.4168118, 0.1433867, 0.0111714, 0.0126265, -0.00658537],
          [0.4681972, 0.2153273, 0.0225249, 0.0152704, -0.00463809],
          [0.6023068, 0.3346815, 0.0731108, 0.0186618, -0.00371541],
          [0.6415743, 0.3985468, 0.1324422, 0.0214160, -0.00062401],
          [0.7503690, 0.5447616, 0.2804541, 0.0539851, 0.00242230],
          [0.7452626, 0.5644594, 0.3324679, 0.0865153, 0.00454960],
          [0.8059782, 0.6586838, 0.4229577, 0.1452990, 0.00976702],
          [0.8549542, 0.7226562, 0.4991309, 0.2420093, 0.02772661],
          [0.8571332, 0.7285741, 0.5279076, 0.2824549, 0.06030276],
          [0.8835633, 0.7727077, 0.5957984, 0.3411303, 0.09652185],
          [0.9071558, 0.8299587, 0.6771400, 0.4402896, 0.17469338],
          [0.9190793, 0.8486480, 0.7163332, 0.5083780, 0.26107691],
          [0.9371223, 0.8762177, 0.7653702, 0.5773109, 0.32181041],
          [0.9554613, 0.9119893, 0.8282687, 0.6776178, 0.43162744],
          [0.9545744, 0.9099264, 0.8270244, 0.6822220, 0.45237623],
          [0.9688112, 0.9351710, 0.8730961, 0.7546601, 0.56622448],
          [0.9743227, 0.9491953, 0.9005150, 0.8086497, 0.64505437],
          [0.9807345, 0.9638853, 0.9283012, 0.8631675, 0.73812581],
          [0.9886746, 0.9777760, 0.9558950, 0.9123417, 0.82726553],
          [0.9899096, 0.9803828, 0.9615592, 0.9255600, 0.85822149],
          [0.9969510, 0.9935441, 0.9864657, 0.9726775, 0.94358663],
          [0.9979533, 0.9960274, 0.9921724, 0.9837415, 0.96626288],
          [0.9995981, 0.9989171, 0.9974178, 0.9949954, 0.99023356],
          [1.0002640, 1.0005088, 1.0010594, 1.0021161, 1.00386912],
          [0.9998903, 0.9998459, 0.9997795, 0.9995484, 0.99916305],
          [1.0000008, 0.9999905, 0.9999481, 0.9998903, 0.99978047],
          [1.0000004, 0.9999983, 1.0000001, 1.0000031, 1.00000297],
          [0.9999995, 1.0000003, 1.0000005, 1.0000001, 1.00000032],
          [0.9999999, 0.9999997, 0.9999994, 0.9999989, 0.99999786],
          [0.9999999, 0.9999999, 0.9999999, 0.9999999, 0.99999991]]
# Get iteration points
grad_list = [prob.grad(x) for x in x_list]
hess_list = [prob.hess(x) for x in x_list]
delta_x = [np.array(x_list[i+1])-np.array(x_list[i])
           for i in range(len(x_list)-1)]
delta_grad = [grad_list[i+1]-grad_list[i]
              for i in range(len(grad_list)-1)]

quasi_newton = SR1(init_scale=1)
quasi_newton.initialize(len(x_list[0]), 'hess')
#quasi_newton = deepcopy(quasi_newton)
#quasi_newton.initialize(len(x_list[0]), 'hess')

# Compare the hessian and its inverse
for i in range(len(delta_x)):
    print (hess_list[i])
    s = delta_x[i]
    y = delta_grad[i]
    quasi_newton.update(s, y)
    B = quasi_newton.get_matrix()
    print (B)
    print ('------------------')
    
