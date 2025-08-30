import numpy as np
import logging
import os
import argparse
import h5py
import datetime as dt

from utils.analysis import estimate_mean, interp_data
import madrigal

SITE_DIR = 'sites/'
KEYS_ALL = ('time', 'tec_data', 'gdlat', 'glon', 'azm', 'elm', 'sat_id', 'gps_site')
KEYS_SITE = KEYS_ALL[:-1]
KEYS_SAT = KEYS_SITE[:-1]
EU_BORDERS = {'min_lat': 28, 'max_lat': 80, 'min_lon': -10, 'max_lon': 50}

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def create_result_dict(keys: tuple) -> dict:
    results = dict()
    for key in keys:
        results[key] = []
    return results


def parse_date(date_str: str, format='%Y-%m-%d') -> dt.date:
    return dt.datetime.strptime(date_str, format).date()


def create_file_names(date: dt.date) -> tuple[str, str]:
    root_part = f"{str(date.year)}{str(date.month).zfill(2)}{str(date.day).zfill(2)}.001.h5"
    tec_file_name = f"los_{root_part}"
    site_file_name = f"site_{root_part}"
    return tec_file_name, site_file_name


def check_prepare_file(date: dt.date, input_file_path: str):
    if not os.path.isfile(input_file_path):
        input_file = input_file_path.split('/')[-1]
        logging.info(f"File {input_file} was not found.")
        logging.info(f"Start downloading {input_file} from Madrigal database")
        madrigal.download_hdf5(date, input_file, input_file_path)


def retrieve_receivers(file_path: str, borders=None):
    if borders is None:
        borders = EU_BORDERS
    sites = []
    with h5py.File(file_path, 'r') as hdf:
        data = hdf['Data/Table Layout'][:]
        for row in data:
            if (borders['min_lat'] <= row['gdlatr'] <= borders['max_lat'] and
                    borders['min_lon'] <= row['gdlonr'] <= borders['max_lon']):
                record = dict()
                record['gps_site'] = row['gps_site'].decode('utf-8').strip()
                record['gdlatr'] = row['gdlatr']
                record['gdlonr'] = row['gdlonr']
                sites.append(record)
    sites.sort(key=lambda x: x['gps_site'])
    return sites


def read_gnss_data(file_path):
    with h5py.File(file_path, 'r') as hdf:
        data = hdf['Data/Table Layout'][:]
    return data


def retrieve_chunk(gnss_data, gnss_type, gps_sites, row_chunk):
    for i in range(0, len(gnss_data), row_chunk):
        results = create_result_dict(KEYS_ALL)
        data = gnss_data[i:i + row_chunk]
        for row in data:
            gps_site_label = row['gps_site'].decode('utf-8').strip()
            if (row['gnss_type'].decode('utf-8').strip() == gnss_type and
                    gps_site_label in gps_sites):
                results['time'].append(dt.datetime(year=row['year'], month=row['month'], day=row['day'],
                                                   hour=row['hour'], minute=row['min'], second=row['sec']))
                results['tec_data'].append(row['los_tec'])
                results['gdlat'].append(row['gdlat'])
                results['glon'].append(row['glon'])
                results['azm'].append(row['azm']),
                results['elm'].append(row['elm'])
                results['sat_id'].append(row['sat_id'])
                results['gps_site'].append(gps_site_label)
        yield results


def append_output_file(file_path, res_final, min_elm=30.0):
    with open(file_path, mode='a') as file:
        for ind in range(len(res_final['tec_data'])):
            if res_final['elm'][ind] > min_elm:
                line = (f"{res_final['time'][ind].hour}\t"
                        f"{res_final['time'][ind].minute}\t"
                        f"{res_final['time'][ind].second}\t"
                        f"{res_final['tec_data'][ind]:.3f}\t"
                        f"{res_final['azm'][ind]:.2f}\t"
                        f"{res_final['elm'][ind]:.2f}\t"
                        f"{res_final['gdlat'][ind]:.2f}\t"
                        f"{res_final['glon'][ind]:.2f}\n")
                file.write(line)


def analyze_gnss_data(input_path, output_path, date_str, window, filter_order,
                      time_gap_int, chunk_size, min_elm, gnss_type, region):
    date = parse_date(date_str)
    directory = f"{input_path}/{date.year}/"
    data_file, site_file = create_file_names(date)
    data_file_path = f"{directory}{data_file}"
    site_file_path = f"{directory}{SITE_DIR}{site_file}"
    date_dir = date.strftime('%Y-%m-%d')
    output_dir = f"{output_path}/{region}/{date.year}/{date_dir}/{window}/"
    output_file = f"{date_dir}_{window}.txt"
    output_site_file = "Sites.txt"
    os.makedirs(output_dir, exist_ok=True)
    check_prepare_file(date, site_file_path)
    check_prepare_file(date, data_file_path)
    sites = retrieve_receivers(site_file_path)
    with open(output_dir + output_site_file, mode='w') as f_site:
        f_site.write('site\tlat\tlon\n')
        for site in sites:
            f_site.write(f"{site['gps_site']}\t{site['gdlatr']:.2f}\t{site['gdlonr']:.2f}\n")
    gps_sites = [item['gps_site'] for item in sites]
    delta_t = dt.timedelta(seconds=30)
    time_gap = dt.timedelta(seconds=time_gap_int)
    window_time = dt.timedelta(seconds=window)
    logging.info('Start GNSS data reading...')
    gnss_data = read_gnss_data(data_file_path)
    logging.info('End GNSS data reading...')
    res_sites = create_result_dict(KEYS_ALL)
    logging.info('Start chunk reading...')
    results_gen = retrieve_chunk(gnss_data, gnss_type, gps_sites, chunk_size)
    chunk_number = np.ceil(len(gnss_data) / chunk_size)
    chunk_num = 0
    for results in results_gen:
        chunk_num += 1
        logging.debug(f"chunk {chunk_num} of {chunk_number}")
        res_sites['time'].extend(results['time'])
        res_sites['tec_data'].extend(results['tec_data'])
        res_sites['gdlat'].extend(results['gdlat'])
        res_sites['glon'].extend(results['glon'])
        res_sites['azm'].extend(results['azm']),
        res_sites['elm'].extend(results['elm'])
        res_sites['gps_site'].extend(results['gps_site'])
        res_sites['sat_id'].extend(results['sat_id'])
    logging.info('End chunk reading...')
    del gnss_data
    win_points = int(window_time / delta_t)
    for gps_site in gps_sites:
        logging.info('gps_site = %s, (%d of %d)', gps_site, gps_sites.index(gps_site) + 1, len(gps_sites))
        res_filtered = create_result_dict(KEYS_SITE)
        for i in range(len(res_sites['time'])):
            if res_sites['gps_site'][i] == gps_site:
                res_filtered['time'].append(res_sites['time'][i])
                res_filtered['tec_data'].append(res_sites['tec_data'][i])
                res_filtered['gdlat'].append(res_sites['gdlat'][i])
                res_filtered['glon'].append(res_sites['glon'][i])
                res_filtered['azm'].append(res_sites['azm'][i]),
                res_filtered['elm'].append(res_sites['elm'][i])
                res_filtered['sat_id'].append(res_sites['sat_id'][i])
        sats = list(set(res_filtered['sat_id']))
        sats.sort()
        for sat_id in sats:
            res_sat = create_result_dict(KEYS_SAT)
            for i in range(len(res_filtered['time'])):
                if res_filtered['sat_id'][i] == sat_id:
                    res_sat['time'].append(res_filtered['time'][i])
                    res_sat['tec_data'].append(res_filtered['tec_data'][i])
                    res_sat['gdlat'].append(res_filtered['gdlat'][i])
                    res_sat['glon'].append(res_filtered['glon'][i])
                    res_sat['azm'].append(res_filtered['azm'][i]),
                    res_sat['elm'].append(res_filtered['elm'][i])
            if res_sat['time']:
                time_diff = np.diff(res_sat['time'])
                break_indices = np.where(time_diff > time_gap)[0]
                res_split = create_result_dict(KEYS_SAT)
                if len(break_indices) > 0:
                    res_split['tec_data'] = np.split(res_sat['tec_data'], np.array(break_indices) + 1)
                    res_split['time'] = np.split(res_sat['time'], np.array(break_indices) + 1)
                    res_split['azm'] = np.split(res_sat['azm'], np.array(break_indices) + 1)
                    res_split['elm'] = np.split(res_sat['elm'], np.array(break_indices) + 1)
                    res_split['gdlat'] = np.split(res_sat['gdlat'], np.array(break_indices) + 1)
                    res_split['glon'] = np.split(res_sat['glon'], np.array(break_indices) + 1)
                else:
                    res_split['tec_data'].append(res_sat['tec_data'])
                    res_split['time'].append(res_sat['time'])
                    res_split['azm'].append(res_sat['azm'])
                    res_split['elm'].append(res_sat['elm'])
                    res_split['gdlat'].append(res_sat['gdlat'])
                    res_split['glon'].append(res_sat['glon'])
                res_final = create_result_dict(KEYS_SAT)
                for ind in range(len(res_split['tec_data'])):
                    start = res_split['time'][ind][0]
                    end = res_split['time'][ind][-1]
                    if end - start < window_time:
                        continue
                    else:
                        time_interp = np.arange(start, end + delta_t, delta_t).astype(dt.datetime)
                        los_interp = interp_data(res_split['time'][ind], res_split['tec_data'][ind], time_interp, k=1)
                        azm_interp = interp_data(res_split['time'][ind], res_split['azm'][ind], time_interp, k=1)
                        elm_interp = interp_data(res_split['time'][ind], res_split['elm'][ind], time_interp, k=1)
                        gdlat_interp = interp_data(res_split['time'][ind], res_split['gdlat'][ind], time_interp, k=1)
                        glon_interp = interp_data(res_split['time'][ind], res_split['glon'][ind], time_interp, k=1)
                        if len(los_interp) < window:
                            window = len(los_interp)
                        current_mean_tec = estimate_mean(los_interp, window=win_points, order=filter_order)
                        current_d_tec = los_interp - current_mean_tec
                        res_final['tec_data'].extend(current_d_tec.tolist())
                        res_final['time'].extend(time_interp.tolist())
                        res_final['azm'].extend(azm_interp.tolist())
                        res_final['elm'].extend(elm_interp.tolist())
                        res_final['gdlat'].extend(gdlat_interp.tolist())
                        res_final['glon'].extend(glon_interp.tolist())

                append_output_file(output_dir + output_file, res_final, min_elm)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse Madrigal hdf5 GNSS files to estimate dTEC variations.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("date", help="Date in format YYYY-MM-DD.", type=str)
    parser.add_argument("-i", "--input_path", help="Path to the local h5 files in format path/to/the/files.", type=str,
                        default="c:/Users/Sergii/Dell_D/GNSS/Raw/")
    parser.add_argument("-o","--output_path", help="Path for output files in format path/to/the/files.", type=str,
                        default="results/in/")
    parser.add_argument("-w", "--window", help="Window length (in seconds) for data analysis.",
                        default=7200, type=int)
    parser.add_argument("-f", "--filter_order", help="Savitzky - Golay filter order.",
                        default=3, type=int)
    parser.add_argument("-t", "--time_gap", help="Minimal time gap (in seconds) between two items to form new record",
                        default=240, type=int)
    parser.add_argument("-c", "--chunk_size", help="Row number chunk for parsing hdf5 file",
                        default=20_000_000, type=int)
    parser.add_argument("-e", "--min_elevation", help="Minimal elevation angle value for data being included.",
                        default=30.0, type=float)
    parser.add_argument("-g", "--gnss_type", help="Type of analyzed GNSS data (GPS or GLONASS).",
                        default='GPS', type=str)
    parser.add_argument("-r", "--region", help="Earth region for analysis (EU, US, JP, UA, ...",
                        default='EU', type=str)
    args = parser.parse_args()
    analyze_gnss_data(input_path=args.input_path, output_path=args.output_path, date_str=args.date, window=args.window,
                      filter_order=args.filter_order, time_gap_int=args.time_gap,
                      chunk_size=args.chunk_size, min_elm=args.min_elevation,
                      gnss_type=args.gnss_type, region=args.region)
