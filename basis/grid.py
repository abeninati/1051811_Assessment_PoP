import numpy as np 
import numbers
from basis.Dirichlet import nodal_basis, nodal_basis_x, nodal_basis_y
from basis.quadrature import GaussLegendre1
from scipy import linalg
from tqdm import trange


class EllipticDirichletBCS:


    def __init__(self, nodal_value=12, length=100):
        # Number of desiderd nodes = (nodal_value-2)^2
        if not isinstance(nodal_value, numbers.Integral) and nodal_value<=2:
            raise TypeError(f"{n} is not an integer greater then 2")
        xd, yd = np.meshgrid(
            np.linspace(0, length, nodal_value), np.linspace(0, length, nodal_value))
        self.nodes = np.transpose(
            (np.concatenate(xd[1:-1, 1:-1]), np.concatenate(yd[1:-1, 1:-1])))
        self.h = xd[0, 1]
        self.a, self.b , self.c, self.d =0,length,0,length
        self.phi = lambda x, y, k: nodal_basis(x, y, self.nodes[k], self.h)
        self.phi_x = lambda x, y, k: nodal_basis_x(x, y, self.nodes[k], self.h)
        self.phi_y = lambda x, y, k: nodal_basis_y(x, y, self.nodes[k], self.h)
        self.A = "Need to run the _A() method to get numerical value."
        self.L = "Need to run the _L() method to get numerical value."
        
        
class Poisson(EllipticDirichletBCS):

    def __init__(self, nodal_value=12, length=100):
        super().__init__(nodal_value, length)
        self.integrand_bilinear_form = lambda x, y, i, j: (
        self.phi_x(x,y,i) * self.phi_x(x,y,j) 
        + self.phi_y(x,y,i) * self.phi_y(x,y,j)
        )
    

    def _l(self, k, f=lambda x,y: 1, GL_degree=100):
        """Linear form of the variational formulation of 2D-Poisson PDE."""
        product_function=lambda x,y: self.phi(x,y,k)*f(x,y)
        return GaussLegendre1(product_function,self.a,self.b,self.c,self.d,GL_degree)

    def _L(self,f=lambda x,y: np.sin(x+y),GL_degree=100):
        """Returns and store as an attribute the b vector of the final linear system."""
        L=np.zeros(len(self.nodes))
        for i in range(len(self.nodes)):
            L[i]=self._l(i,f,GL_degree)
        self.L=L
        return L

    def _a(self,i,j,GL_degree=100):
        """Bilinear form of the variational formulation of 
        2D-Poisson PDE with Dirichelt BCs."""
        integrand=lambda x,y: self.integrand_bilinear_form(x,y,i,j)
        return GaussLegendre1(integrand,self.a,self.b,self.c,self.d,GL_degree)
        
    def _A(self,GL_degree=30):
        """Returns and store as an attribute the A matrix of the final linear system."""
        self.A=np.zeros((len(self.nodes),len(self.nodes)))
        for i in trange(len(self.nodes)): # the code uses trange to get loading bar
            for j in range(len(self.nodes)):
                self.A[i,j]=self._a(i,j,GL_degree)
        return self.A

    def _U(self): # requires running self._A() and self._L() beforehand
        """Returns and store as an attribute the U vector of coefficients."""
        if isinstance(self.A,str) or isinstance(self.L,str):
            raise AttributeError(f"{type(self).__name__} object has no numerical attribute A or L."
            " Make sure you run _L() and _A() before running _U() in order to store the relevant attributes.")
        self.U=linalg.solve(self.A,self.L)
        return self.U
    
    def u(self,x,y): # requires running self._U() beforehand
        """Approximated solution u(x,y)."""    
        if isinstance(self.U,str):
            raise AttributeError(f"{type(self).__name__} object has no attribute U."
            " Make sure you run _U() before running u() in order to store the relevant attribute.")
        res=np.zeros(len(self.nodes))
        for i in trange(len(self.nodes)):
            res[i]=nodal_basis(x,y,self.nodes[i],self.h)
        return np.dot(self.U,res)
    

class Helmotz(Poisson):
    

    def __init__(self, nodal_value=12, length=100, ksq=lambda x,y: 47):
        super().__init__(nodal_value, length)
        self.ksq = ksq
        self.integrand_bilinear_form = lambda x,y,i,j: (
        self.phi_x(x, y, i) * self.phi_x(x, y, j) 
        + self.phi_y(x, y, i) * self.phi_y(x, y, j) 
        + self.phi(x, y, i) * self.ksq(x, y) )

    # def _a(self,i,j,n=30):
    #     """Bilinear form of the variational formulation of 
    #     2D-Hoisson PDE with Zero BCs."""
    #     integrand=lambda x,y: self.integrand_bilinear_form(x,y,i,j) 
    #     return GaussLegendre1(integrand,self.a,self.b,self.c,self.d,n)

