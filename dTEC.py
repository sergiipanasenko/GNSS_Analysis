import os
import math
from numpy import median


from gnss import GnssDataParser

LIMIT_DTEC = 1


class DTEC_handling:
    def __init__(self, input_dir, output_dir, input_data_file=None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.gnss_parser = GnssDataParser()
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
            if not os.path.isfile(self.input_data_file):
                raise FileNotFoundError(f"Parsed file f'{self.input_data_file}' is not exist.")
            self.gnss_parser.read_gnss_data(self.input_data_file)

    def create_time_stamp_data(self):
        time_values = self.gnss_parser.time_values
        coord_coverage = self.gnss_parser.coord_coverage
        self.read_data()
        self.gnss_parser.get_lon_lat_dtec(self.output_dir, time_values)
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        lat_span = self.gnss_parser.coord_values['lat_span'].get_float_degs()
        lon_span = self.gnss_parser.coord_values['lon_span'].get_float_degs()
        time_file_name = f"{self.gnss_parser.get_lon_lat_dtec_file_stem(self.output_dir)}_av.txt"
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

    def create_coords_stamp_data(self):
        time_list = []
        dtec_list = []
        self.read_data()
        coord_values = self.gnss_parser.coord_values
        time_coverage = self.gnss_parser.time_coverage
        min_time = time_coverage['min_time']
        max_time = time_coverage['max_time']
        time_span = self.gnss_parser.time_values['time_span']
        current_date = min_time.date()
        self.gnss_parser.get_time_dtec(self.output_dir, coord_values, current_date)
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
        coord_file_name = f"{self.gnss_parser.get_time_dtec_file_stem(self.output_dir)}_av.txt"
        with open(coord_file_name, mode='w') as res_file:
            for line in list(zip(time_list, dtec_list)):
                current_time_value = line[0].strftime('%Y.%m.%d %H:%M:%S')
                current_dtec_value = line[1]
                res_file.write(f"{current_time_value}\t{current_dtec_value}\n")

    def create_lat_time_data(self):
        self.read_data()
        coord_values = self.gnss_parser.coord_values
        coord_coverage = self.gnss_parser.coord_coverage
        time_coverage = self.gnss_parser.time_coverage
        min_time = time_coverage['min_time']
        max_time = time_coverage['max_time']
        time_span = self.gnss_parser.time_values['time_span']
        current_date = min_time.date()
        self.gnss_parser.get_lat_time_dtec(self.output_dir, coord_values, current_date)
        n_time = math.ceil((max_time - min_time) / time_span)
        plot_time = [min_time + j * time_span for j in range(n_time)]
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        lat_span = coord_values['lat_span'].get_float_degs()
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        lat_file_name = f"{self.gnss_parser.get_lat_time_dtec_file_stem(self.output_dir)}_av.txt"
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

    def create_lon_time_data(self):
        self.read_data()
        coord_values = self.gnss_parser.coord_values
        coord_coverage = self.gnss_parser.coord_coverage
        time_coverage = self.gnss_parser.time_coverage
        min_time = time_coverage['min_time']
        max_time = time_coverage['max_time']
        time_span = self.gnss_parser.time_values['time_span']
        current_date = min_time.date()
        self.gnss_parser.get_lon_time_dtec(self.output_dir, coord_values, current_date)
        n_time = math.ceil((max_time - min_time) / time_span)
        plot_time = [min_time + j * time_span for j in range(n_time)]
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        corr_lon_span = self.get_corr_lon_span()
        n_lon = math.ceil((max_lon - min_lon) / corr_lon_span)
        plot_lon = [min_lon + corr_lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
        lon_file_name = f"{self.gnss_parser.get_lon_time_dtec_file_stem(self.output_dir)}_av.txt"
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
