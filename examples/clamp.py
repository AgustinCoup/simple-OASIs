def clamp(x, lo, hi):
    """Limita x al intervalo [lo, hi] (se asume lo <= hi)."""
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
