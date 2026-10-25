from utils.astron import calculate_terminators_simple, calculate_terminators_skyfield
import datetime as dt
import matplotlib.pyplot as plt
from utils.geo.geo_coords import GeoCoord


def get_terminator_coords(alt_km: float, c_time: dt.datetime,
                          lon_step: GeoCoord = GeoCoord(0, 30),
                          lat_step: GeoCoord = GeoCoord(0, 30)):
    sunrise_coords = {
        'lat': [],
        'lon': []
    }
    sunset_coords = {
        'lat': [],
        'lon': []
    }
    dest_date = c_time.date()
    dest_time = c_time.time()
    lat_min = GeoCoord(36, 0)
    lat_max = GeoCoord(71, 0)
    lon_min = GeoCoord(-10, 0)
    lon_max = GeoCoord(30, 0)
    c_lat = lat_min
    while c_lat <= lat_max:
        lat_float = c_lat.get_float_degs()
        c_lon = lon_min
        while c_lon <= lon_max:
            lon_float = c_lon.get_float_degs()
            term = calculate_terminators_simple(dest_date, lat_float, lon_float, alt_km, 0)
            if term['status'] == "Success":
                sunrise_math = term['sunrise_utc']
                sunset_math = term['sunset_utc']
                if (sunrise_math.hour == dest_time.hour) and (sunrise_math.minute == dest_time.minute):
                    sunrise_coords['lat'].append(lat_float)
                    sunrise_coords['lon'].append(lon_float)
                if (sunset_math.hour == dest_time.hour) and (sunset_math.minute == dest_time.minute):
                    sunset_coords['lat'].append(lat_float)
                    sunset_coords['lon'].append(lon_float)
            c_lon += lon_step
        c_lat += lat_step
    return sunrise_coords, sunset_coords


if __name__ == '__main__':
    c_time = dt.datetime(2024, 4, 1, 18, 0)
    alt_km = 150
    sunrise, sunset = get_terminator_coords(alt_km, c_time,
                                            lon_step=GeoCoord(0, 15),
                                            lat_step=GeoCoord(0, 15))
    print(sunset)