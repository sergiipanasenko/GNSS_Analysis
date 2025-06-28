import datetime
from utils.analysis import interp_data, use_sigma_criteria, bandpass_filter, apf
from utils.geo.geo_coords import GeoCoord


def load_parse_data(load_file: str, time_format: str, time_sep = '\t'):
    time_list = []
    coord_list = []
    dtec_list = []
    with open(load_file, 'r') as file:
        for line in file:
            str_data = line.split(time_sep)
            time_str = str_data[0]
            current_time = datetime.datetime.strptime(time_str, time_format)
            time_list.append(current_time)
            coord_list.append(float(str_data[1]))
            dtec_list.append(float(str_data[2]))
    return time_list, coord_list, dtec_list


def add_time_coord_to_file(file_name, time_format, time, coords, dTEC):
    with open(file_name, 'w') as file:
        for num in range(len(time)):
            for coord in coords:
                str_time = datetime.datetime.strftime(time[num], time_format)
                c_dTEC = dTEC[coord][num]
                file.write(f"{str_time}\t{coord}\t{c_dTEC}\n")


if __name__ == '__main__':
    year = 2017
    month = 9
    day = 30
    month_str = str(month).zfill(2)
    day_str = str(day).zfill(2)
    date_str = f"{year}-{month_str}-{day_str}"
    c_lat = GeoCoord(55, 0)
    c_lon = GeoCoord(10, 0)
    resol_lat = GeoCoord(0, 45)
    resol_lon = GeoCoord(0, 45)
    min_period = 30
    max_period = 120
    time_format = '%Y.%m.%d %H:%M:%S'
    flag = 'Lat'
    if flag == 'Lat':
        read_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/{flag}/1/{c_lat.degs}d{c_lat.mins}m_{resol_lat.degs}d{resol_lat.mins}m_lat_av.txt"
        corr_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/{flag}/2/{c_lat.degs}d{c_lat.mins}m_{resol_lat.degs}d{resol_lat.mins}m_lat_corr.txt"
        filter_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/{flag}/3/{c_lat.degs}d{c_lat.mins}m_{resol_lat.degs}d{resol_lat.mins}m_lat_filter.txt"
        out_file_name = f"{date_str}_{c_lat.degs}d{c_lat.mins}m_{resol_lat.degs}d{resol_lat.mins}m_lat_filter.txt"

    if flag == 'Lon':
        read_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/{flag}/1/{c_lon.degs}d{c_lon.mins}m_{resol_lon.degs}d{resol_lon.mins}m_lon_av.txt"
        corr_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/{flag}/2/{c_lon.degs}d{c_lon.mins}m_{resol_lon.degs}d{resol_lon.mins}m_lon_corr.txt"
        filter_file_name = f"C:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis/results/out/EU/{year}/{year}-{month_str}-{day_str}/7200/{flag}/3/{c_lon.degs}d{c_lon.mins}m_{resol_lon.degs}d{resol_lon.mins}m_lon_filter.txt"
        out_file_name = f'{date_str}_{c_lon.degs}d{c_lon.mins}m_{resol_lon.degs}d{resol_lon.mins}m_lon_params.txt'
    res = load_parse_data(read_file_name, time_format)
    coords = sorted(list(set(res[1])))
    print(coords)
    signal = dict()
    for coord in coords:
        time = []
        dTEC = []
        for j in range(len(res[0])):
            if res[1][j] == coord:
                time.append(res[0][j])
                dTEC.append(res[2][j])
        signal[coord] = (time, dTEC)
    time_start = datetime.datetime(year, month, day, 0, 0, 0)
    time_end = datetime.datetime(year, month, day, 23, 59, 30)
    time_delta = datetime.timedelta(seconds=30)
    n_time = int((time_end - time_start) / time_delta) + 1
    coord_time_interp = [time_start + j * time_delta for j in range(n_time)]
    coord_float_time_interp = [x.hour + x.minute / 60. + x.second / 3600 for x in coord_time_interp]
    coord_dTEC_corr = dict()
    coord_dTEC_filter = dict()
    n_time = len(coord_float_time_interp)
    for num in range(len(coords)):
        print(num)
        coord_time = signal[coords[num]][0]
        coord_dTEC = signal[coords[num]][1]
        coord_dTEC_interp = interp_data(coord_time, coord_dTEC, coord_time_interp, k=1)
        coord_dTEC_corr[coords[num]] = use_sigma_criteria(coord_dTEC_interp, window=120)
        coord_dTEC_filter[coords[num]] = bandpass_filter(coord_dTEC_corr[coords[num]], 2 * min_period, 2 * max_period)
    add_time_coord_to_file(corr_file_name, time_format, coord_time_interp, coords, coord_dTEC_corr)
    add_time_coord_to_file(filter_file_name, time_format, coord_time_interp, coords, coord_dTEC_filter)




