# Tendon simulation model

* D(t): fraction of teh tendon collagen that is compromised
* C(t): Effective maintenance capacity of resident tendon cells
* S(t): fraction of the tendon cells that are senescents
* L(t): Mechanical loading stimulus, relative to a healthy reference

dD/dt = kd * (1-D) - kr * C * f(L) * D

dS/dt = ks * (1-S) - kc * S

C = C0 (1 - a.S)

* kd is the rate of matrix damage accumulation.
* kr is the maximum effective matrix repair rate.
* f(L) describes how appropriate mechanical loading stimulates maintenance.
* ks is the rate of entry into senescence
* kc is the clearance rate of senescent cells.
* a represents the loss of maintenance effectiveness associated with senescence.

f(L) = b + (1-b) * L^2 / (K^2 + L^2)

With b = 0.2 and K = 0.5


