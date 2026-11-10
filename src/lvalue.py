"""Certified computation of L(E,1) for E : y^2 = x^3 - x.

FORMULA (derivation in PROOF.md, section "The Fricke exponential sum"):
Let f(z) = sum_{n>=1} a_n q^n be the weight-2 newform of level N = 32 attached
to E, and let lambda = +/-1 be its Fricke eigenvalue in the normalisation

    (f|_2 W_N) = lambda * f,   W_N = [[0,-1],[N,0]],
    (f|_2 W_N)(z) = N^{-1} z^{-2} f(-1/(N z)),

i.e.  f(-1/(N z)) = lambda * N * z^2 * f(z).                       (F)

Mellin at s = 1 gives  L(E,1) = 2 pi * int_0^inf f(i t) dt.  Split the
integral at t = 1/sqrt(N), writing I1 for the part on (0, 1/sqrt(N)) and I2
for the part on (1/sqrt(N), inf).  Substituting t = 1/(N u) in I1 and using
(F) with z = i u gives

    I1 = int_{1/sqrt(N)}^inf f(i/(N u)) du/(N u^2)
       = int_{1/sqrt(N)}^inf [lambda N (i u)^2 f(i u)] du/(N u^2)
       = -lambda * I2.

Hence L(E,1) = 2 pi (1 - lambda) I2.  On t >= 1/sqrt(N) the q-expansion
converges uniformly (a_n = O(sqrt(n)) and e^{-2 pi n t} decays), so it may be
integrated term by term:

    I2 = sum_{n>=1} a_n e^{-2 pi n / sqrt(N)} / (2 pi n).

Therefore

    lambda = -1  ==>  L(E,1) = 2 * sum_{n>=1} (a_n / n) * exp(-2 pi n / sqrt(N)),  (L)
    lambda = +1  ==>  L(E,1) = 0.

Our curve has analytic rank 0 (L(E,1) != 0), so lambda = -1 and (L) applies.

ERROR BOUND.  Deligne's bound gives |a_n| <= d(n) * sqrt(n) for every n, and
d(n) <= 2 sqrt(n), so |a_n / n| <= 2 for every n.  Therefore for any cutoff N0

    | L(E,1) - 2 * sum_{n<=N0} (a_n/n) e^{-2 pi n/sqrt(N)} |
        <= 4 * e^{-c (N0+1)} / (1 - e^{-c}),        c = 2 pi / sqrt(N).    (E)

All arithmetic below is certified integer fixed-point interval arithmetic
(cert.py); no floating point is used, and every interval returned is a proven
enclosure of the true value.
"""

from fractions import Fraction

import cert
from a_n import build_table

N_CONDUCTOR = 32


def exp_weights(cutoff):
    """exp(-c n) for n = 1..cutoff as certified intervals, c = 2*pi/sqrt(N)."""
    sqrtN = cert.sqrt_bounds((N_CONDUCTOR * cert.S, N_CONDUCTOR * cert.S))
    # c = 2 pi / sqrt(N)
    two_pi = cert.scale(cert.PI, 2)
    c = cert.div(two_pi, sqrtN)
    out = []
    for n in range(1, cutoff + 1):
        x = cert.mul_rat(c, n, 1)
        out.append(cert.exp_neg_bounds(x[0], x[1]))
    return c, out


def lvalue(cutoff=400):
    """Return (interval_for_L, diagnostics)."""
    counting, eta, ap = build_table(cutoff)
    mismatches = [n for n in range(1, cutoff + 1) if counting[n] != eta[n]]
    if mismatches:
        raise AssertionError("a_n methods disagree at n=%r" % mismatches[:5])

    c, weights = exp_weights(cutoff)

    # sum (a_n / n) * exp(-c n)
    total = (0, 0)
    for n in range(1, cutoff + 1):
        a = counting[n]
        if a == 0:
            continue
        term = cert.mul_rat_iv(weights[n - 1], a, n)
        total = cert.add(total, term)
    L_sum = cert.scale(total, 2)          # L(E,1) = 2 * sum

    # certified tail bound: 4 e^{-c (N0+1)} / (1 - e^{-c})
    x_next = cert.mul_rat(c, cutoff + 1, 1)
    e_next = cert.exp_neg_bounds(x_next[0], x_next[1])   # e^{-c(N0+1)}
    e_c = cert.exp_neg_bounds(c[0], c[1])                 # e^{-c}
    one_minus = cert.sub((cert.S, cert.S), e_c)           # 1 - e^{-c}
    tail = cert.div(cert.scale(e_next, 4), one_minus)

    lo = cert.sub(L_sum, tail)[0]      # lower endpoint of the certified interval
    hi = cert.add(L_sum, tail)[1]      # upper endpoint of the certified interval
    diag = {
        "cutoff": cutoff,
        "c": c,
        "tail_bound": tail,
        "an_methods_agree": True,
        "max_a_n": max(abs(v) for v in counting[1:cutoff + 1]),
    }
    return (lo, hi), diag


def main():
    cutoff = 400
    (lo, hi), diag = lvalue(cutoff)
    lo, hi = int(lo), int(hi)
    dlo, dhi = cert.to_decimal((lo, hi))
    diag["dec"] = (dlo, dhi)
    print("cutoff N0            : %d" % cutoff)
    print("c = 2 pi / sqrt(32)   : %s" % cert.to_decimal(diag["c"])[0])
    print("certified tail bound  : < %.3e" % (float(diag["tail_bound"][1]) / cert.S))
    print("L(E,1) lower bound    : %s" % dlo)
    print("L(E,1) upper bound    : %s" % dhi)
    print("L(E,1) width          : %.3e" % ((hi - lo) / cert.S))


if __name__ == "__main__":
    main()
