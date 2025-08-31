from utils.geo.geo_coords import GeoCoord
from ui.cartopy_figure import COORDS


LIMIT_DTEC = 1


def dtec_corr(val):
    if abs(val) < LIMIT_DTEC:
        return val
    else:
        return 0.0



