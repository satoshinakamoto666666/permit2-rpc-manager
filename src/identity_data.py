"""Constants for E : y^2 = x^3 - x, each labelled with its epistemic status.

The labels are the point of this file.  Every number used anywhere in the
artefact comes from exactly one of these three places, and the label says
which:

    PROVED      -- derived in PROOF.md by a self-contained argument that a
                   reader can check from this repository alone.
    CITED       -- a classical published theorem, quoted here rather than
                   re-proved, with the reference named.
    COMPUTED    -- produced by a script in this repository, from a certified
                   computation whose error bound is proved in the script.

Nothing in this file is "believed" or "approximate".  If a number is not in
one of those three categories, it is not used.
"""

# --------------------------------------------------------------------------
# Curve
# --------------------------------------------------------------------------
# PROVED: the curve itself, and its identification with Cremona 32a2.
#   E : y^2 = x^3 - x has discriminant 64 and j-invariant 1728, conductor 32.
#   PARI/GP agrees (see data/pari-32a2.txt): ellglobalred -> [32,...],
#   ellidentify -> [["32a2",[0,0,0,-1,0],[]],...].
#   NOTE the LMFDB label: Cremona's own label file (alllabels, JohnCremona/
#   ecdata) maps Cremona 32a2 to LMFDB label 32.a3, NOT 32.a2 -- LMFDB's
#   isogeny-class ordering differs from Cremona's.  See data/ecdata-32a2.txt.
MODEL = [0, 0, 0, -1, 0]
CREMONA_LABEL = "32a2"
LMFDB_LABEL = "32.a3"
CONDUCTOR = 32
J_INVARIANT = 1728

# --------------------------------------------------------------------------
# Arithmetic side
# --------------------------------------------------------------------------
# PROVED (PROOF.md, "Fermat's descent"): E(Q) = E[2](Q) = {O,(0,0),(1,0),(-1,0)}.
# Hence rank 0 and torsion group (Z/2)^2, so the number of rational torsion
# points is 4.  (Fermat's right-triangle theorem: 1 is not a congruent number,
# which is exactly this statement.)
TORS_ORDER = 4
TORS_GROUP = "(Z/2)^2"
RANK = 0

# COMPUTED (tate.py, cross-checked against PARI/GP ellglobalred/elllocalred):
# the Tamagawa number at the only bad prime 2.  All other primes are good,
# so prod_p c_p = c_2.
#
# NOTE on the Kodaira symbol: the installed PARI/GP reports elllocalred(E,2)
# = [5, 3, [1,0,0,0], 2], and in THIS PARI version the 'kod' code 3 means
# type III (the enumeration is documented in ??elllocalred: "2, 3 and 4 mean
# types II, III and IV respectively").  Type III is also forced by Ogg's
# formula f_p = v_p(Delta_min) + 1 - m: here m = 6 + 1 - 5 = 2 components,
# and type I_0* has 5 components (it would force f_2 = 2, i.e. conductor 4,
# contradicting the conductor 32).  Some tables label this reduction I_0*;
# see PROOF.md, section "Tamagawa number and Kodaira symbol", for why that
# label is inconsistent with Ogg's formula.
TAMAGAWA_C2 = 2
KODAIRA_TYPE = "III"
MINIMAL_DISCRIMINANT = 64
C4 = 48
C6 = 0

# --------------------------------------------------------------------------
# Analytic side
# --------------------------------------------------------------------------
# COMPUTED (lvalue.py, certified interval, cross-checked against PARI ellL1):
#   L(E,1) = 0.65551438857302995261620989747277985342068873785596...
#
# COMPUTED (period.py, certified interval, two independent routes):
#   Omega_E = 5.244115108584239620929679179782238827365509902863246...
#
# CITED (classical CM theory; both routes above agree with these closed
# forms to 38+ digits, which is the check that the numerics are right):
#   L(E,1)      = Gamma(1/4)^2 / (8 sqrt(2 pi))
#   Omega_E     = Gamma(1/4)^2 / sqrt(2 pi)
# hence L(E,1) = Omega_E / 8 exactly.
L_CLOSED_FORM = "Gamma(1/4)^2 / (8*sqrt(2*pi))"
OMEGA_CLOSED_FORM = "Gamma(1/4)^2 / sqrt(2*pi)"

# --------------------------------------------------------------------------
# The remaining, unresolved piece
# --------------------------------------------------------------------------
# CITED: Sha(E) = 1 for this curve (Cremona's tables, and the 2-descent
# certificate in sha2.py).
#
# PRECISION ABOUT THE 2-PART (important -- the obvious shortcut is wrong):
# PARI's ellrank reports s = 0 for this curve, but per ??ellrank "s" is the
# rank of G[2]/2G[4] and gives only a MINORATION of S, the 2-rank of Sha.
# So "s = 0" does NOT imply Sha[2] = 0.  The valid inference uses the rank
# bounds: PARI reports r = R = 0, so the rank is exactly 0 and, since
# R_upper = C - T and C = T + R + S, we get S = R_upper - R_true = 0.
# sha2.py makes exactly this inference and validates it against PARI's own
# worked example.  The ODD-primary part is CITED, not proved here.
SHA_ORDER_CITED = 1

# OPEN: the general BSD conjecture is open.  This artefact verifies ONE
# special case's leading coefficient; it proves nothing about BSD in
# general, and says so.
GENERAL_BSD_STATUS = "OPEN"
