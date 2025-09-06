import os
import argparse
import math
import datetime as dt
from numpy import median
import logging
from concurrent.futures import ProcessPoolExecutor

from gnss import GnssDataParser
from utils.geo.geo_coords import GeoCoord, COORDS

LIMIT_DTEC = 1
TIME_DIR = 'Time/1'
COORD_DIR = 'Map/1'
LAT_DIR = 'Lat/1'
LON_DIR = 'Lon/1'

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class DTEC_handling:
    def __init__(self, output_dir, input_data_file=None):
        self.output_dir = output_dir
        self.gnss_parser = GnssDataParser(output_dir)
        self.input_data_file = input_data_file

    @staticmethod
    def dtec_corr(val):
        if abs(val) < LIMIT_DTEC:
            return val
        else:
            return 0.0

    def get_corr_lon_span(self):
        lat = self.gnss_parser.coord_values['lat'].get_float_degs()
        lon_span = self.gnss_parser.coord_values['lon_span'].get_float_degs()
        return lon_span / math.cos(math.radians(lat))

    def read_data(self):
        if not self.gnss_parser.data:
            logging.info(f"Start reading from {self.input_data_file}.")
            if not os.path.isfile(self.input_data_file):
                raise FileNotFoundError(f"Parsed file f'{self.input_data_file}' is not exist.")
            self.gnss_parser.read_gnss_data(self.input_data_file)
            logging.info(f"End reading from {self.input_data_file}.")

    def create_time_stamp_data(self, store_dir=TIME_DIR, time_stamp=None):
        coord_coverage = self.gnss_parser.coord_coverage
        self.read_data()
        self.gnss_parser.get_lon_lat_dtec(store_dir, time_stamp)
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        lat_span = self.gnss_parser.coord_values['lat_span'].get_float_degs()
        lon_span = self.gnss_parser.coord_values['lon_span'].get_float_degs()
        time_file_name = f"{self.gnss_parser.get_lon_lat_dtec_file_stem(store_dir, time_stamp)}_av.txt"
        logging.info(f"Start creating {time_file_name}.")
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        with open(time_file_name, mode='w') as res_file:
            for lat in plot_lat:
                lat_data = list(filter(lambda x: abs(x[1] - lat) <= lat_span / 2,
                                       self.gnss_parser.lon_lat_dtec))
                if lat_data:
                    corr_lon_span = lon_span / math.cos(math.radians(lat))
                    n_lon = math.ceil((max_lon - min_lon) / corr_lon_span)
                    plot_lon = [min_lon + corr_lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
                    for lon in plot_lon:
                        lat_lon_data = list(filter(lambda x: abs(x[0] - lon) <= corr_lon_span / 2, lat_data))
                        if lat_lon_data:
                            lat_lon_dtec = list(zip(*lat_lon_data))[2]
                            dtec_value = median(lat_lon_dtec)
                            res_file.write(f"{lat}\t{lon}\t{dtec_value}\n")
        logging.info(f"End creating {time_file_name}.")

    def create_coords_stamp_data(self, store_dir=COORD_DIR, point=None):
        time_list = []
        dtec_list = []
        self.read_data()
        time_coverage = self.gnss_parser.time_coverage
        min_time = time_coverage['min_time']
        max_time = time_coverage['max_time']
        time_span = self.gnss_parser.time_values['time_span']
        self.gnss_parser.get_time_dtec(store_dir, point)
        n_time = math.ceil((max_time - min_time) / time_span)
        plot_time = [min_time + j * time_span for j in range(n_time)]
        for c_time in plot_time:
            time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2,
                                    self.gnss_parser.time_dtec))
            if time_data:
                time_dtec = list(zip(*time_data))[1]
                c_dtec = median(time_dtec)
                dtec_list.append(c_dtec)
                time_list.append(c_time)
        coord_file_name = f"{self.gnss_parser.get_time_dtec_file_stem(store_dir, point)}_av.txt"
        logging.info(f"Start creating {coord_file_name}.")
        with open(coord_file_name, mode='w') as res_file:
            for line in list(zip(time_list, dtec_list)):
                current_time_value = line[0].strftime('%Y.%m.%d %H:%M:%S')
                current_dtec_value = line[1]
                res_file.write(f"{current_time_value}\t{current_dtec_value}\n")
        logging.info(f"End creating {coord_file_name}.")

    def create_lat_time_data(self, store_dir=LON_DIR, longitude=None):
        self.read_data()
        coord_values = self.gnss_parser.coord_values
        coord_coverage = self.gnss_parser.coord_coverage
        time_coverage = self.gnss_parser.time_coverage
        min_time = time_coverage['min_time']
        max_time = time_coverage['max_time']
        time_span = self.gnss_parser.time_values['time_span']
        self.gnss_parser.get_lat_time_dtec(store_dir, longitude)
        n_time = math.ceil((max_time - min_time) / time_span)
        plot_time = [min_time + j * time_span for j in range(n_time)]
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        lat_span = coord_values['lat_span'].get_float_degs()
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        lat_file_name = f"{self.gnss_parser.get_lat_time_dtec_file_stem(store_dir, longitude)}_av.txt"
        logging.info(f"Start creating {lat_file_name}.")
        with open(lat_file_name, mode='w') as res_file:
            for c_time in plot_time:
                time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2,
                                        self.gnss_parser.lat_time_dtec))
                if time_data:
                    for lat in plot_lat:
                        lat_time_data = list(filter(lambda x: abs(x[1] - lat) <= lat_span / 2, time_data))
                        if lat_time_data:
                            lat_time_dtec = list(zip(*lat_time_data))[2]
                            dtec_value = median(lat_time_dtec)
                            res_file.write(f"{c_time.strftime('%Y.%m.%d %H:%M:%S')}\t{lat}\t{dtec_value}\n")
        logging.info(f"End creating {lat_file_name}.")

    def create_lon_time_data(self, store_dir=LAT_DIR, latitude=None):
        self.read_data()
        coord_coverage = self.gnss_parser.coord_coverage
        time_coverage = self.gnss_parser.time_coverage
        min_time = time_coverage['min_time']
        max_time = time_coverage['max_time']
        time_span = self.gnss_parser.time_values['time_span']
        self.gnss_parser.get_lon_time_dtec(store_dir, latitude)
        n_time = math.ceil((max_time - min_time) / time_span)
        plot_time = [min_time + j * time_span for j in range(n_time)]
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        corr_lon_span = self.get_corr_lon_span()
        n_lon = math.ceil((max_lon - min_lon) / corr_lon_span)
        plot_lon = [min_lon + corr_lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
        lon_file_name = f"{self.gnss_parser.get_lon_time_dtec_file_stem(store_dir, latitude)}_av.txt"
        logging.info(f"Start creating {lon_file_name}.")
        with open(lon_file_name, mode='w') as res_file:
            for c_time in plot_time:
                time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2,
                                        self.gnss_parser.lon_time_dtec))
                if time_data:
                    for lon in plot_lon:
                        lon_time_data = list(filter(lambda x: abs(x[1] - lon) <= corr_lon_span / 2, time_data))
                        if lon_time_data:
                            lon_time_dtec = list(zip(*lon_time_data))[2]
                            dtec_value = median(lon_time_dtec)
                            res_file.write(f"{c_time.strftime('%Y.%m.%d %H:%M:%S')}\t{lon}\t{dtec_value}\n")
        logging.info(f"End creating {lon_file_name}.")

    def analyze_all_coords(self, lat):
        point = dict()
        max_lon = self.gnss_parser.coord_coverage['max_lon']
        lon = self.gnss_parser.coord_coverage['min_lon']
        point['lat'] = lat
        while lon <= max_lon:
            point['lon'] = lon
            self.create_coords_stamp_data(store_dir=f'{COORD_DIR}/Nodes', point=point)
            lon += GeoCoord(1,0)


if __name__ == '__main__':
    # Set up basic logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    OUTPUT_DIR = 'results/test'
    INPUT_DIR = 'results/in'
    TIME_SAMPLE = dt.timedelta(seconds=30)
    LAT_SPAN = GeoCoord(0, 45)
    LON_SPAN = GeoCoord(0, 45)
    parser = argparse.ArgumentParser(
        description="Form output files with dTEC variations.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("date", help="Date in format YYYY-MM-DD.", type=str)
    parser.add_argument("-d", "--directory", help="Path to the current directory in format path/to/the/directory.", type=str,
                        default="c:/Users/Sergii/Dell_D/Coding/Python/PyCharm/GNSS_Analysis")
    parser.add_argument("-r", "--region", help="Earth region for analysis (EU, US, JP, UA, ...",
                        default='EU', type=str)
    parser.add_argument("-w", "--window", help="Window length (in seconds) for data analysis.",
                        default=7200, type=int)
    parser.add_argument("-t", "--time", help="Specific time in format HH:MM:SS.",
                        default='12:00:00', type=str)
    parser.add_argument("-j", "--latitude", help="Specific latitude in format DD:MM.",
                        default='50:00', type=str)
    parser.add_argument("-i", "--longitude", help="Specific longitude in format DD:MM.",
                        default='14:36', type=str)
    parser.add_argument("-a", "--all_times", help="Analysis for all times.", action='store_true')

    args = parser.parse_args()
    year = int(args.date[:4])
    month = int(args.date[5:7])
    day = int(args.date[8:])
    time = dt.datetime.strptime(args.time, '%H:%M:%S')
    lat_deg = int(args.latitude[:2])
    lat_min = int(args.latitude[3:])
    lat = GeoCoord(lat_deg, lat_min)
    lon_deg = int(args.longitude[:2])
    lon_min = int(args.longitude[3:])
    lon = GeoCoord(lon_deg, lon_min)
    input_data_file = f"{args.directory}/{INPUT_DIR}/{args.region}/{year}/{args.date}/{args.window}/{args.date}_{args.window}.txt"
    dTEC_parser = DTEC_handling(OUTPUT_DIR, input_data_file)
    dTEC_parser.gnss_parser.add_dir = f"{args.region}/{year}/{args.date}/{args.window}/"
    start_time = dt.datetime(year, month, day, 0, 0, 0)
    end_time = dt.datetime(year, month, day, 23, 59, 59)
    dTEC_parser.gnss_parser.time_coverage = {'min_time': start_time, 'max_time': end_time}
    dTEC_parser.gnss_parser.coord_coverage = {
        'min_lat': COORDS[args.region]['min_lat'],
        'max_lat': COORDS[args.region]['max_lat'],
        'min_lon': COORDS[args.region]['min_lon'],
        'max_lon': COORDS[args.region]['max_lon'],
    }
    dTEC_parser.gnss_parser.time_values = {'time': time, 'time_span': TIME_SAMPLE}
    dTEC_parser.read_data()
    dTEC_parser.gnss_parser.coord_values = {
        'lat': lat, 'lat_span': LAT_SPAN,
        'lon': lon, 'lon_span': LON_SPAN,
    }
    if not args.all_times:
        with ProcessPoolExecutor() as executor:
            executor.submit(dTEC_parser.create_time_stamp_data)
            executor.submit(dTEC_parser.create_coords_stamp_data)
            executor.submit(dTEC_parser.create_lat_time_data)
            executor.submit(dTEC_parser.create_lon_time_data)
    else:
        lat_min = dTEC_parser.gnss_parser.coord_coverage['min_lat']
        lat_max = dTEC_parser.gnss_parser.coord_coverage['max_lat']
        latitudes = []
        current_lat = lat_min
        while current_lat <= lat_max:
            latitudes.append(current_lat)
            current_lat += GeoCoord(1, 0)
        with ProcessPoolExecutor() as executor:
            executor.map(dTEC_parser.analyze_all_coords, latitudes)







