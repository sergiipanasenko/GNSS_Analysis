import numpy as np
from skyfield.api import load, wgs84
from skyfield import almanac
import datetime as dt

# Earth's mean radius in meters for dip calculation
EARTH_MEAN_RADIUS_M = 6371000.0


def calculate_terminators_skyfield(latitude, longitude, altitude_km, year, month, day):
    """
    Calculates sunrise and sunset times using the Skyfield library, correctly
    accounting for observer altitude by calculating the dip of the horizon.

    Args:
        latitude (float): Observer's latitude in degrees.
        longitude (float): Observer's longitude in degrees (East is positive).
        altitude_km (float): Observer's altitude in kilometers.
        year (int): Year of the desired date.
        month (int): Month of the desired date.
        day (int): Day of the desired date.

    Returns:
        A tuple (sunrise_time, sunset_time) as datetime objects (UTC), or a string
        indicating a polar day/night condition.
    """
    # --- 1. Load Ephemeris and Timescale ---
    eph = load('de421.bsp')
    ts = load.timescale()
    sun = eph['sun']
    earth = eph['earth']

    # --- 2. Define Observer Location ---
    observer_geodetic = wgs84.latlon(
        latitude_degrees=latitude,
        longitude_degrees=longitude,
        elevation_m=altitude_km * 1000
    )
    observer_location = earth + observer_geodetic

    # --- 3. Calculate Effective Horizon for the Elevated Observer ---
    altitude_m = altitude_km * 1000

    # Standard horizon for sea-level (accounts for refraction and Sun's radius)
    standard_horizon_deg = -0.8333

    # Calculate the geometric dip of the horizon in degrees
    cos_dip = EARTH_MEAN_RADIUS_M / (EARTH_MEAN_RADIUS_M + altitude_m)
    dip_rad = np.arccos(cos_dip)
    dip_deg = np.rad2deg(dip_rad)

    # The effective horizon is the standard horizon lowered by the dip angle
    effective_horizon_deg = standard_horizon_deg - dip_deg

    # --- 4. Define Time Range for the Search ---
    t0 = ts.utc(year, month, day)
    t1 = ts.utc(year, month, day + 1)

    # --- 5. Find Events Using the Custom Horizon ---
    # Pass the calculated effective_horizon_deg to the almanac functions.
    rise_times, _ = almanac.find_risings(
        observer_location, sun, t0, t1, horizon_degrees=effective_horizon_deg
    )

    set_times, _ = almanac.find_settings(
        observer_location, sun, t0, t1, horizon_degrees=effective_horizon_deg
    )

    # --- 6. Extract and Return Results ---
    sunrise_time = rise_times.utc_datetime() if len(rise_times) > 0 else None
    sunset_time = set_times.utc_datetime() if len(set_times) > 0 else None

    # Handle cases of polar day/night
    if not sunrise_time and not sunset_time:
        alt, _, _ = observer_location.at(t0).observe(sun).apparent().altaz()
        if alt.degrees > effective_horizon_deg:
            return "Polar Day", "Polar Day"
        else:
            return "Polar Night", "Polar Night"

    return sunrise_time[0], sunset_time[0]


# --- Example Usage ---
if __name__ == '__main__':
    lat = 50.0
    lon = 14.6
    alt_km = 100

    # Date
    dest_date = dt.datetime(2023, 4, 1).date()

    sunrise, sunset = calculate_terminators_skyfield(latitude=lat, longitude=lon, altitude_km=alt_km,
                                                     year=dest_date.year, month=dest_date.month, day=dest_date.month)

    if isinstance(sunrise, str):
        print(f"  Status: {sunrise}")
    else:
        print(f"  Sunrise (UTC): {sunrise.strftime('%Y-%m-%d %H:%M:%S %Z') if sunrise else 'N/A'}")
        print(f"  Sunset (UTC):  {sunset.strftime('%Y-%m-%d %H:%M:%S %Z') if sunset else 'N/A'}")
