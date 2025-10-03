from utils.astron import calculate_terminators_simple, calculate_terminators_skyfield
import datetime as dt
import matplotlib.pyplot as plt

lat = 50
lon = 14.36
alt = [x for x in range(500)]
alt1 = 350
dest_date = dt.date(2023, 11, 1)
sunrise, sunset = calculate_terminators_skyfield(latitude=lat,
                                                 longitude=lon,
                                                 altitude_km=alt1,
                                                 year=dest_date.year,
                                                 month=dest_date.month,
                                                 day=dest_date.day)
term = calculate_terminators_simple(dest_date, lat, lon, alt1, 0)
sunrise_math = term['sunrise_utc']
sunset_math = term['sunset_utc']
print(f"Sunrise (UTC):\t{sunrise.strftime('%H:%M:%S %Z')}\t{sunrise_math.strftime('%H:%M:%S %Z')}")
print(f"Sunset (UTC):\t{sunset.strftime('%H:%M:%S %Z')}\t{sunset_math.strftime('%H:%M:%S %Z')}")
draw = True
if draw:
    sunrise_simple = []
    sunset_simple = []
    sunrise_sky = []
    sunset_sky = []

    for altitude in alt:
        terms = calculate_terminators_simple(dest_date, lat, lon, altitude, 0)
        sunrise_simple.append(terms['sunrise_utc'])
        sunset_simple.append(terms['sunset_utc'])
        sunrise_new, sunset_new = calculate_terminators_skyfield(latitude=lat,
                                                                 longitude=lon,
                                                                 altitude_km=altitude,
                                                                 year=dest_date.year,
                                                                 month=dest_date.month,
                                                                 day=dest_date.day)
        sunrise_sky.append(sunrise_new)
        sunset_sky.append(sunset_new)

    plt.plot(sunrise_simple, alt, c='r')
    plt.plot(sunset_simple, alt, c='r')
    plt.plot(sunrise_sky, alt, c='b')
    plt.plot(sunset_sky, alt, c='b')
    plt.show()
