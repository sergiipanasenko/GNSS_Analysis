LIMIT_DTEC = 1


def dtec_corr(val):
    if abs(val) < LIMIT_DTEC:
        return val
    else:
        return 0.0



