# -*- coding: UTF-8 -*-
#!/usr/bin/env python
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
# ====================
# sympyprt test script
# ====================
#
# Usage:
# cd  ../Lib/site-packages/IPython/extensions/ (or whereever it is)
# %loadpy test_sympyprt.py (or from URL)
#
#
# Workflow:
#  - calc some sympy objects and store them in Obj (list) by the func _()
#  - no rendering is performed during script run, hence the cache is empty
#  - use: for obj in Obj: display(obj), this generates all images.
#  - all but the binomial should display well.
#
# Note: if we use 'inline' mode some formulas may look ugly. Def. equation*
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

from __future__ import division
from sympy import *

Obj = [] # obj store

def _(obj): Obj.append(obj)

# define some symbols
x, y, z, t = symbols('x y z t')
k, m, n = symbols('k m n', integer=True)
f, g, h = symbols('f g h', cls=Function)

# load the extension
%load_ext sympyprt

#+
_(x)
_(n)

_((1/cos(x)).series(x, 0, 10))
_(pi**2)
_(oo+1)
_(1/( (x+2)*(x+1) ))
_(diff(sin(x), x))
e = 1/(x + y)
s = e.series(x, 0, 5)
_(e)
_(s)
_(integrate(exp(-x**2)*erf(x), x))
_(exp(I*x).expand(complex=True))

from sympy.abc import theta, phi

_(Ylm(2, 1, theta, phi))

_(factorial(x))
_(gamma(x + 1).series(x, 0, 3))
_(assoc_legendre(2, 1, x))

_(f(x).diff(x, x) + f(x))
_(dsolve(f(x).diff(x, x) + f(x), f(x)))

from sympy import Matrix
A = Matrix([[1,x], [y,1]])

_(A)
_(A**2)

_(Integral(x**2, x))
_(N(sqrt(2)*pi, 50))

_(Abs(-x))
_(binomial(x,y))
g = meijerg([1], [2], [3], [4], x)
_(integrate(x**2 * exp(x) * cos(x), x))

_(y | (x & y))
_(x >> y)

_(Matrix(3, 4, lambda i,j: 1 - (i+j) % 2))
M = Matrix(([1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]))
_(M)
_(M**4)

A = Matrix([[1,1,1],[1,1,3],[2,3,4]])
Q, R = A.QRdecomposition()
_(Q)
_(A)
_(R)

x, y, t, x0, y0, C1= symbols('x,y,t,x0,y0,C1')
P, Q, F= map(Function, ['P', 'Q', 'F'])
_(Eq(Eq(F(x, y), Integral(P(t, y), (t, x0, x)) + Integral(Q(x0, t), (t, y0, y))), C1))
_(dsolve(2*x*f(x) + (x**2 + f(x)**2)*f(x).diff(x), f(x),hint='1st_homogeneous_coeff_best'))

n=Symbol('n')
f, P, Q = map(Function, ['f', 'P', 'Q'])
genform = Eq(f(x).diff(x) + P(x)*f(x), Q(x)*f(x)**n)
_(genform)

_(dsolve(genform, f(x), hint='Bernoulli_Integral'))

from sympy.tensor import IndexedBase, Idx
M = IndexedBase('M')
i, j = map(Idx, ['i', 'j'])

_(M[i, j])

%sympyprt help

#%sympyprt textcolor Red

_(g) #cached
_((1/cos(x)).series(x, 0, 10)) #cached
_(x**n) # not cached

#%sympyprt reset cache
_(g)
_((1/cos(x)).series(x, 0, 10)) #after cache reset

_((1/cos(x)).series(x, 0, 20)) # without breqn

%sympyprt breqn on

_((1/cos(x)).series(x, 0, 21)) # with breqn on


# all objects in Obj
print str(Obj)
print "\n\n\n"
print "*** Let's hope the Obj list is not empty."
print "Next let's display the objects. Note: the cache is empty"
print "Repeat the next step to see the difference ;)\n"
print "Now type in the following code:"
print "  for obj in Obj: display(obj)"



