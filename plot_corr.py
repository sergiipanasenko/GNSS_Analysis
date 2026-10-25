import matplotlib.pyplot as plt
import numpy as np
from agw_corr_all import plot_stat_params
from numpy import median


def plot_hist(x: np.array, bins=None):
    if bins is None:
        q25, q75 = np.percentile(x, [25, 75])
        bin_width = 2 * (q75 - q25) * len(x) ** (-1 / 3)
        bins = round((x.max() - x.min()) / bin_width)
        print("Freedman–Diaconis number of bins:", bins)
    plt.hist(x, density=False, bins=bins, rwidth=0.95)


def get_param_lists(current_set):
    file_period, file_vel, file_azm = current_set
    raw_period = []
    raw_vel = []
    raw_azm = []
    raw_lat = []
    raw_lon = []
    with open(file_period, mode='r') as file:
        for line in file:
            raw_data = line.split('\t')
            raw_period.append(float(raw_data[2]))
            raw_lat.append(float(raw_data[0]))
            raw_lon.append(float(raw_data[1]))
    with open(file_vel, mode='r') as file:
        for line in file:
            raw_data = line.split('\t')
            raw_vel.append(float(raw_data[2]))
    with open(file_azm, mode='r') as file:
        for line in file:
            raw_data = line.split('\t')
            raw_azm.append(float(raw_data[2]))
    return raw_lat, raw_lon, raw_period, raw_vel, raw_azm


def get_medians(x, y):
    x_out = list(set(x))
    y_out = []
    for ind in range(len(x_out)):
        temp = []
        for ind2 in range(len(y)):
            if x[ind2] == x_out[ind]:
                temp.append(y[ind2])
        if temp:
            y_out.append(median(temp))
        else:
            y_out.append(None)
    return x_out, y_out


def limit_coords(lim_lats, lim_lons, current_set):
    lat_min, lat_max = lim_lats
    lon_min, lon_max = lim_lons
    raw_lat, raw_lon, raw_period, raw_vel, raw_azm = get_param_lists(current_set)
    period = []
    velocity = []
    azm = []
    lat = []
    lon = []
    wave_length = []
    for ind in range(len(raw_lat)):
        if (lat_min <= raw_lat[ind] <= lat_max) and (lon_min <= raw_lon[ind] <= lon_max):
            period.append(raw_period[ind])
            velocity.append(raw_vel[ind])
            wave_length.append(raw_vel[ind] * raw_period[ind] * 0.06)
            lat.append(raw_lat[ind])
            lon.append(raw_lon[ind])
            azm.append(raw_azm[ind])
    return lat, lon, period, velocity, azm, wave_length


if __name__ == '__main__':
    file_period_500 = r"LSTID_Period_500.txt"
    file_vel_500 = r"LSTID_Velocity_500.txt"
    file_azm_500 = r"LSTID_Azimuth_500.txt"
    file_period_1000 = r"LSTID_Period_new1.txt"
    file_vel_1000 = r"LSTID_Velocity_new1.txt"
    file_azm_1000 = r"LSTID_Azimuth_new1.txt"
    file_period_100 = r"LSTID_Period_Node.txt"
    file_vel_100 = r"LSTID_Velocity_Node.txt"
    file_azm_100 = r"LSTID_Azimuth_Node.txt"
    set_100 = (file_period_100, file_vel_100, file_azm_100)
    set_500 = (file_period_500, file_vel_500, file_azm_500)
    set_1000 = (file_period_1000, file_vel_1000, file_azm_1000)
    lim_lats = (0, 55)
    lim_lons = (-90, 90)
    x_label = "Latitude (deg)"
    y_label = r"Period (min)"
    params_period = []
    params_velocity = []
    for cur_set in (set_100, set_500, set_1000):
        lat, lon, period, velocity, azm, wave_length = limit_coords(lim_lats, lim_lons, cur_set)
        x_in_per, y_in_per = lat, period
        x_in_vel, y_in_vel = lat, velocity
        x_out_per, y_out_per = get_medians(x_in_per, y_in_per)
        x_out_vel, y_out_vel = get_medians(x_in_vel, y_in_vel)
        params_period.append(y_out_per)
        params_velocity.append(y_out_vel)
        plt.plot(x_out_per, y_out_per, marker='o')
    # plot_stat_params(np.array(lat), np.array(velocity), x_label, y_label)
    # x = np.array(period)
    # plot_hist(x)
    print(np.corrcoef(params_period[2], params_velocity[2]))
    lim_lats = (38, 59)
    lim_lons = (-8, 20)
    lat1, lon1, period1, velocity1, azm1, wave_length1 = limit_coords(lim_lats, lim_lons, set_1000)
    output_file = "LSTID_Wavelength_new1.txt"
    with open(output_file, mode='w') as out_file:
        for ind in range(len(wave_length1)):
            out_file.write(f"{lat1[ind]}\t{lon1[ind]}\t{wave_length1[ind] / 10.0}\n")
    plt.show()
