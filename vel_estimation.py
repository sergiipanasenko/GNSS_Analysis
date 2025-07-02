import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import correlate, correlation_lags

from utils.geo.geo_coords import GeoCoord
from utils.analysis import estimate_phase_velocity, get_distance_azimuth
from corr_filter import load_parse_data

if __name__ == '__main__':
    year = 2017
    month = 7
    day = 16
    hour_start = 10
    min_start = 0
    hour_end = 13
    min_end = 0
    month_str = str(month).zfill(2)
    day_str = str(day).zfill(2)
    date_str = f"{year}-{month_str}-{day_str}"
    c_lat = GeoCoord(55, 0)
    c_lon = GeoCoord(10, 0)
    c_lat_float = c_lat.degs + c_lat.mins / 60.
    c_lon_float = c_lon.degs + c_lon.mins / 60.
    lat_num = 2
    lon_num = 1
    resol_lat = GeoCoord(0, 45)
    resol_lon = GeoCoord(0, 45)
    time_start = datetime.datetime(year, month, day, hour_start, min_start)
    time_end = datetime.datetime(year, month, day, hour_end, min_end)
    time_format = '%Y.%m.%d %H:%M:%S'
    lat_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/lat/1/{c_lat.degs}d{c_lat.mins}m_{resol_lat.degs}d{resol_lat.mins}m_lat_av.txt"
    lon_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/Lon/1/{c_lon.degs}d{c_lon.mins}m_{resol_lon.degs}d{resol_lon.mins}m_lon_av.txt"
    res_lat = load_parse_data(lat_file_name, time_format)
    res_lon = load_parse_data(lon_file_name, time_format)
    coords_lat = sorted(list(set(res_lat[1])))
    coords_lon = sorted(list(set(res_lon[1])))
    diff_coord_lat = [abs(cur_lon - c_lon_float) for cur_lon in coords_lat]
    diff_coord_lon = [abs(cur_lat - c_lat_float) for cur_lat in coords_lon]
    cur_lon_index = diff_coord_lat.index(min(diff_coord_lat))
    cur_lat_index = diff_coord_lon.index(min(diff_coord_lon))
    lon_dTEC_first = []
    lon_dTEC_second = []
    for i in range(len(res_lat[0])):
        if time_start <= res_lat[0][i] <= time_end:
            if res_lat[1][i] == coords_lat[cur_lon_index - lon_num]:
                lon_dTEC_first.append(res_lat[2][i])
            if res_lat[1][i] == coords_lat[cur_lon_index + lon_num]:
                lon_dTEC_second.append(res_lat[2][i])
    time_dTEC = []
    lat_dTEC_first = []
    lat_dTEC_second = []
    for i in range(len(res_lon[0])):
        if time_start <= res_lon[0][i] <= time_end:
            if res_lon[1][i] == coords_lon[cur_lat_index - lat_num]:
                lat_dTEC_first.append(res_lon[2][i])
                time_dTEC.append(res_lon[0][i])
            if res_lon[1][i] == coords_lon[cur_lat_index + lat_num]:
                lat_dTEC_second.append(res_lon[2][i])
    lat_corr = correlate(lat_dTEC_first, lat_dTEC_second)
    lat_corr /= np.max(lat_corr)
    lat_lags = correlation_lags(np.array(lat_dTEC_first).size, np.array(lat_dTEC_second).size, mode="full")
    lon_corr = correlate(lon_dTEC_first, lon_dTEC_second)
    lon_corr /= np.max(lon_corr)
    lon_lags = correlation_lags(np.array(lon_dTEC_first).size, np.array(lon_dTEC_second).size, mode="full")
    lat_max_num = lat_lags[np.argmax(lat_corr)]
    lon_max_num = lon_lags[np.argmax(lon_corr)]
    dist_lat, azm_lat = get_distance_azimuth(coords_lon[cur_lat_index + lat_num], c_lon_float,
                                             coords_lon[cur_lat_index - lat_num], c_lon_float)
    dist_lon, azm_lon = get_distance_azimuth(c_lat_float, coords_lat[cur_lon_index + lon_num],
                                             c_lat_float, coords_lat[cur_lon_index - lon_num])
    vel_abs, vel_azm = estimate_phase_velocity((dist_lat, azm_lat, lat_max_num * 30),
                                               (dist_lon, azm_lon, lon_max_num * 30))
    print(lat_max_num, lon_max_num)
    print(vel_abs * 1000, vel_azm)
    plt.plot(lat_lags, lat_corr)
    plt.show()