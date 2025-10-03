import math
from datetime import datetime, timedelta, timezone


# --- Core Calculation Functions ---

def calculate_julian_day(year, month, day, hour=12, minute=0, second=0):
    """Calculates the Julian Day for a given date."""
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    JD = (math.floor(365.25 * (year + 4716)) +
          math.floor(30.6001 * (month + 1)) + day + B - 1524.5)
    fractional_day = (hour - 12) / 24 + minute / 1440 + second / 86400
    return JD + fractional_day


def calculate_solar_position(jd):
    """
    Calculates the Sun's declination and the Equation of Time.
    Based on the algorithm from the US Naval Observatory.
    """
    n = jd - 2451545.0
    # Mean longitude of the Sun
    L = (280.460 + 0.9856474 * n) % 360
    # Mean anomaly of the Sun
    g = (357.528 + 0.9856003 * n) % 360
    g_rad = math.radians(g)

    # Ecliptic longitude of the Sun
    lambda_sun = (L + 1.915 * math.sin(g_rad) + 0.020 * math.sin(2 * g_rad)) % 360
    lambda_sun_rad = math.radians(lambda_sun)

    # Obliquity of the ecliptic
    epsilon = (23.439 - 0.0000004 * n)
    epsilon_rad = math.radians(epsilon)

    # Solar Declination (delta)
    sin_delta = math.sin(epsilon_rad) * math.sin(lambda_sun_rad)
    delta_rad = math.asin(sin_delta)

    # Right Ascension (RA)
    y = math.cos(epsilon_rad) * math.sin(lambda_sun_rad)
    x = math.cos(lambda_sun_rad)
    ra_rad = math.atan2(y, x)

    # Equation of Time (minutes)
    eot_minutes = 4 * math.degrees((math.radians(L) - ra_rad) % (2 * math.pi))
    # Correct for quadrant and range issues
    if eot_minutes > 20: eot_minutes -= 2880
    if eot_minutes < -20: eot_minutes += 1440

    return delta_rad, eot_minutes


def calculate_terminators_simple(date, latitude, longitude, altitude_km, timezone_offset):
    """
    Estimates sunrise and sunset times for a given location, date, and altitude.

    Args:
        date (datetime.date): The date for the calculation.
        latitude (float): Observer's latitude in degrees.
        longitude (float): Observer's longitude in degrees (East is positive).
        altitude_km (float): Observer's altitude in kilometers.
        timezone_offset (int): Timezone offset from UTC in hours.

    Returns:
        A dictionary with sunrise and sunset times as datetime objects, or None.
    """
    # --- 1. Initial Setup ---
    lat_rad = math.radians(latitude)
    altitude_m = altitude_km * 1000

    # --- 2. Calculate Target Zenith Angle ---
    # Dip of the horizon correction in degrees
    if altitude_m > 0:
        dip_corr_deg = (1.75 * math.sqrt(altitude_m)) / 60.0
    else:
        dip_corr_deg = 0

    # Standard zenith for sunrise/sunset (90.8333 deg for sea level)
    zenith_deg = 90.8333 + dip_corr_deg
    zenith_rad = math.radians(zenith_deg)

    # --- 3. Calculate Solar Position for the day ---
    # Use noon UTC on the given day for the primary calculation
    jd_noon = calculate_julian_day(date.year, date.month, date.day, 12)
    delta_rad, eot_minutes = calculate_solar_position(jd_noon)

    # --- 4. Calculate Hour Angle ---
    cos_omega_0 = (math.cos(zenith_rad) - math.sin(lat_rad) * math.sin(delta_rad)) / \
                  (math.cos(lat_rad) * math.cos(delta_rad))

    if cos_omega_0 > 1:
        return {"status": "Polar Day (Sun never sets)"}
    if cos_omega_0 < -1:
        return {"status": "Polar Night (Sun never rises)"}

    omega_0_rad = math.acos(cos_omega_0)
    omega_0_deg = math.degrees(omega_0_rad)

    # --- 5. Calculate Solar Noon and Event Times in UTC ---
    # Solar noon in UTC
    solar_noon_utc_hour = 12.0 - (longitude / 15.0) - (eot_minutes / 60.0)

    # Hour angle in hours
    hour_angle_hours = omega_0_deg / 15.0

    # Sunrise and Sunset in UTC hours
    sunrise_utc_hour = solar_noon_utc_hour - hour_angle_hours
    sunset_utc_hour = solar_noon_utc_hour + hour_angle_hours

    # --- 6. Convert to datetime objects ---
    base_date = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)

    sunrise_utc = base_date + timedelta(hours=sunrise_utc_hour)
    sunset_utc = base_date + timedelta(hours=sunset_utc_hour)

    # Convert to local time
    local_tz = timezone(timedelta(hours=timezone_offset))
    sunrise_local = sunrise_utc.astimezone(local_tz)
    sunset_local = sunset_utc.astimezone(local_tz)

    return {
        "status": "Success",
        "sunrise_utc": sunrise_utc,
        "sunset_utc": sunset_utc,
        "sunrise_local": sunrise_local,
        "sunset_local": sunset_local
    }


# --- Example Usage ---
if __name__ == '__main__':
    lat = 50
    lon = 14.6
    alt_km = 100
    tz_offset = 1

    # Date
    calc_date = datetime(2023, 4, 1).date()

    results = calculate_terminators_simple(calc_date, lat, lon, alt_km, tz_offset)

    if results['status'] == 'Success':
        print(f"Results for\n\tlatitude:\t{lat}\n\tlongitude:\t{lon}\n\taltitude:\t{alt_km} km:")
        print(f"\t\tSunrise (UTC):\t{results['sunrise_utc'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"\t\tSunset (UTC):\t{results['sunset_utc'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print(results['status'])