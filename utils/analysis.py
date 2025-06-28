import numpy as np
from scipy import interpolate
from scipy.signal import savgol_filter, windows
from scipy.special import erf
import matplotlib.pyplot as plt


def reshape1(x):
    return x.reshape(x.size)


def reshape2(x):
    return x.reshape(x.size, 1)


def estimate_mean(signal, window, order):
    return savgol_filter(signal, window_length=window, polyorder=order)


def define_indexes(i, signal, window):
    left_half = window // 2
    right_half = window - left_half
    s_length = len(signal)
    if (i - left_half) >= 0:
        left_ind = i - left_half
    else:
        left_ind = 0
    if (i + right_half) <= s_length - 1:
        right_ind = i + right_half
    else:
        right_ind = s_length
    return left_ind, right_ind


def estimate_sigma(signal, window):
    sigma = []
    s_length = len(signal)
    for i in range(0, s_length):
        left_ind, right_ind = define_indexes(i, signal, window)
        sigma.append(np.std(signal[left_ind: right_ind]))
    return sigma


def interp_data(x_input, y_input, x_res, k=3):
    time_input = np.array([x.timestamp() for x in x_input])
    time_res = np.array([x.timestamp() for x in x_res])
    tck = interpolate.splrep(time_input, y_input, k=k)
    return interpolate.splev(time_res, tck)


def use_sigma_criteria(signal, window=12, k_coef=2.5):
    flag = True
    loop_lim = 100
    cycle_count = 0
    s3 = None
    while flag:
        s2 = savgol_filter(signal, window_length=window, polyorder=2)
        delta_s = signal - s2
        s_length = len(delta_s)
        s3 = np.copy(signal)
        s3[0] = s2[0]
        s3[s_length - 1] = s2[s_length - 1]
        sigma = estimate_sigma(signal=delta_s, window=window)
        out_count = 0
        cycle_count += 1
        for i in range(1, s_length - 1):
            if abs(delta_s[i]) > k_coef * sigma[i]:
                out_count += 1
                if abs(delta_s[i + 1]) > k_coef * sigma[i + 1]:
                    s3[i] = s3[i - 1]
                else:
                    s3[i] = (s3[i - 1] + s3[i + 1]) / 2
        if (out_count == 0) or (cycle_count == loop_lim):
            flag = False
        else:
            signal = np.copy(s3)
    return s3


def bandpass_filter(signal, min_period, max_period, trend_removal=False, norm=False):
    def u(x, a, L):
        b = erf(np.pi * a)
        return (2. / (b * L)) * np.exp(-x * x / (a * a * L * L)) * np.sinc(2. * x / L)

    if trend_removal:
        trend_period = int(1.5 * max_period)
        trend = estimate_mean(signal, window=trend_period, order=2)
        signal = signal - trend
        if norm:
            signal = signal / (trend + 1E-7)
    a = 40
    s_length = len(signal)
    x = np.arange(-s_length + 1, s_length)
    y = u(x, a, min_period) - u(x, a, max_period)
    s2 = []
    for j in range(0, s_length):
        val = np.sum([signal[j - k] * y[s_length + k - 1] for k in range(j - s_length + 1, j + 1)])
        s2.append(val)
    return np.array(s2)


def get_distance_azimuth(lat1, long1, lat2, long2):
    R_E = 6372.795
    r_lat1 = np.radians(lat1)
    r_lat2 = np.radians(lat2)
    r_long1 = np.radians(long1)
    r_long2 = np.radians(long2)
    d_lon = (r_long2 - r_long1)

    x = np.cos(r_lat2) * np.sin(d_lon)
    y = np.cos(r_lat1) * np.sin(r_lat2) - np.sin(r_lat1) * np.cos(r_lat2) * np.cos(d_lon)
    z = np.sin(r_lat1) * np.sin(r_lat2) + np.cos(r_lat1) * np.cos(r_lat2) * np.cos(d_lon)
    dist = R_E * np.arccos(z)
    azm = np.degrees(np.arctan2(x, y))
    if azm < 0:
        azm += 360
    return dist, azm


def estimate_phase_velocity(set_1, set_2):
    dist_1, azm_1, tau1 = set_1
    dist_2, azm_2, tau2 = set_2
    k_1 = tau1 / dist_1
    if k_1 < 0:
        k_1 = - k_1
        azm_1 += 180
    k_2 = tau2 / dist_2
    if k_2 < 0:
        k_2 = - k_2
        azm_2 += 180
    k = np.sqrt(k_1 * k_1 + k_2 * k_2 - 2 * k_1 * k_2 *
                np.cos(np.pi + np.radians(azm_1) - np.radians(azm_2)))
    azm = np.degrees(np.arcsin((k_2 / (k + 1E-10)) * np.sin(np.pi + np.radians(azm_1) -
                                                  np.radians(azm_2)))) + azm_1
    if azm > 360:
        azm -= 360.0
    if azm < 0:
        azm += 360.0
    return 1 / (k + 1E-10), azm


def apf(signal, period, time=None, dt=1, nu=3):
    result = []
    s_length = len(signal)
    min_period, max_period, period_step = period
    if min_period < 2:
        min_period = 2
    if time is None:
        min_time, max_time, time_step = (0, s_length - 1, 1)
    else:
        min_time, max_time, time_step = time
    alpha1 = 0.54
    alpha2 = 0.46
    # cn = 1 / np.sqrt(alpha1 * alpha1 + alpha2 * alpha2 / 2)
    cn1 = 1 / alpha1
    for p in range(min_period, max_period + 1, period_step):
        win_length = nu * p + 1
        window = windows.hamming(win_length)
        x = np.array(range(win_length))
        base_func = np.exp(2j * np.pi * x / p)
        spectrum = []
        for t in range(min_time, max_time + 1, time_step):
            left_ind, right_ind = define_indexes(t, signal, win_length)
            y = signal[left_ind: right_ind]
            if len(y) < win_length:
                y_add = np.zeros(win_length - len(y))
                if left_ind == 0:
                    y = np.hstack([y_add, y])
                else:
                    y = np.hstack([y, y_add])
            current = cn1 * (2 / (win_length - 1)) * np.sum(y * window * base_func)
            spectrum.append(current)
        result.append(spectrum)
    return np.array(result).transpose()


def arg_loc_max(x):
    return np.where(np.append(np.nan, np.diff(np.sign(np.append(np.nan, np.diff(x))))) == -2)[0] - 1


def arg_loc_min(x):
    return np.where(np.append(np.nan, np.diff(np.sign(np.append(np.nan, np.diff(x))))) == 2)[0] - 1


if __name__ == '__main__':
    # print(get_distance_azimuth(0, 2, 1, 1))
    # t = np.array(range(121))
    #
    # signal = 2 * np.sin(2 * np.pi * t / 25)
    # period = (2, 40, 1)
    # p = list(range(2, 41))
    # res = apf(signal, period)
    # t_range, p_range = np.mgrid[0:121, 2:41]
    # plt.pcolormesh(t_range, p_range, np.abs(res) * np.abs(res), shading='auto')
    # plt.colorbar()
    # # plt.show()
    # set_1 = (20.0, 45, -1.0)
    # set_2 = (20.0, 0, 1.0)
    # print(estimate_phase_velocity(set_1, set_2))
    coords = (56.5, 31.72)
    coords_LVV = (49.9, 23.75)
    coords_DOU = (50.1, 4.6)
    coords_BEL = (51.836, 20.789)
    coords_HLP = (54.603, 18.811)
    coords_LYC = (64.612, 18.748)
    coords_NUR = (60.51, 24.66)
    coords_SOD = (67.37, 26.63)
    coords_SUA = (44.68, 26.25)
    coords_UPS = (59.903, 17.353)
    coords_BDV = (49.080, 14.020)
    coords_PAG = (42.515, 24.177)
    coords_BFO = (48.331, 8.325)
    coords_CLF = (48.025, 2.26)
    coords_NGK = (52.070, 12.680)
    coords_WNG = (53.725, 9.053)
    coords_WIC = (47.931, 15.866)
    coords_NCK = (47.63, 16.72)
    coords_IION = (49.6766, 36.29525)
    coords_ABK = (68.358, 18.823)
    coords_HRN = (77.0, 15.55)
    coords_LER = (60.138, 358.817 - 360)
    print(get_distance_azimuth(*coords, *coords_LER))