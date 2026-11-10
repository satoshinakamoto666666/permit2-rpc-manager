"""Fourier coefficients a_n of the weight-2 newform of level 32 attached to
E : y^2 = x^3 - x  (Cremona 32a2), computed by TWO INDEPENDENT methods.

Method A -- POINT COUNTING (the definition of the Euler factor):
    a_p = p + 1 - #E(F_p) for a good prime p.
Method B -- ETA PRODUCT (a closed form for the newform itself):
    f(z) = eta(4z)^2 eta(8z)^2 = q * prod_{n>=1} (1-q^{4n})^2 (1-q^{8n})^2,
    so a_n = [q^n] f(z), computed here with exact integer polynomial arithmetic.

Then the Hecke recursion extends a_p to all n:
    a_{mn} = a_m a_n          for (m,n)=1
    a_{p^{k+1}} = a_p a_{p^k} - p a_{p^{k-1}}.

Agreement between A and B is an INTERNAL control: two different mathematical
definitions of the same integers must produce the same table.  A disagreement
would mean one of the two is wrong -- neither is assumed correct.

Everything here is exact integer arithmetic.
"""

# ---------------------------------------------------------------------------
# Method A: point counting
# ---------------------------------------------------------------------------

def primes_upto(n):
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
    return [i for i in range(2, n + 1) if sieve[i]]


def count_points_mod_p(p):
    """#E(F_p) for E: y^2 = x^3 - x, by brute force over (x,y)."""
    total = 1  # the point at infinity
    for x in range(p):
        rhs = (x * x * x - x) % p
        for y in range(p):
            if (y * y - rhs) % p == 0:
                total += 1
    return total


def a_p_by_counting(p):
    return p + 1 - count_points_mod_p(p)


# ---------------------------------------------------------------------------
# Method B: eta product, exact integer polynomial arithmetic
# ---------------------------------------------------------------------------

def _poly_mul(a, b, N):
    out = [0] * (N + 1)
    for i, ai in enumerate(a):
        if not ai:
            continue
        if i > N:
            break
        for j, bj in enumerate(b):
            if i + j > N:
                break
            out[i + j] += ai * bj
    return out


def _poly_sq(a, N):
    return _poly_mul(a, a, N)


def eta_product_coeffs(N):
    """Coefficients of q * prod_{n>=1} (1-q^{4n})^2 (1-q^{8n})^2 up to q^N.

    Each factor (1 - q^d)^2 = 1 - 2 q^d + q^{2d} is applied as a sparse
    update, which keeps the whole product O(N) per factor instead of O(N^2)."""
    poly = [0] * (N + 1)
    poly[0] = 1
    for n in range(1, N + 1):
        for d in (4 * n, 8 * n):
            if d > N:
                continue
            new = list(poly)
            for i in range(N - d, -1, -1):
                new[i + d] -= 2 * poly[i]
            for i in range(N - 2 * d, -1, -1):
                new[i + 2 * d] += poly[i]
            poly = new
    # multiply by the leading q
    return [0] + poly[:N]


# ---------------------------------------------------------------------------
# Hecke recursion and the combined table
# ---------------------------------------------------------------------------

def build_table(N):
    """Return (a_n from counting, a_n from eta, agree?) for 1 <= n <= N."""
    P = primes_upto(N)
    ap_count = {}
    for p in P:
        if p == 2:
            ap_count[p] = 0          # additive reduction at 2 => a_2 = 0
        else:
            ap_count[p] = a_p_by_counting(p)

    def an_from_ap(n, ap):
        """a_n from a_p via the Hecke relations."""
        if n == 1:
            return 1
        if n % 2 == 0:
            return 0                  # a_{2^k} = 0
        result = 1
        m = n
        for p in P:
            if m % p:
                continue
            k = 0
            while m % p == 0:
                m //= p
                k += 1
            prev, cur = 1, ap[p]      # a_{p^0}=1, a_{p^1}=a_p
            for _ in range(2, k + 1):
                prev, cur = cur, ap[p] * cur - p * prev
            result *= cur
        assert m == 1, "factorisation incomplete"
        return result

    counting = [0] * (N + 1)
    for n in range(1, N + 1):
        counting[n] = an_from_ap(n, ap_count)

    eta = eta_product_coeffs(N)
    return counting, eta, ap_count


if __name__ == "__main__":
    import sys
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    counting, eta, ap = build_table(N)
    bad = [n for n in range(1, N + 1) if counting[n] != eta[n]]
    print("a_p (point counting):", {p: ap[p] for p in sorted(ap) if p <= 40})
    print("method A vs method B mismatches:", bad if bad else "NONE")
    print("a_1..a_20:", counting[1:21])
