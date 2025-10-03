import os
import argparse
import math
import datetime as dt

import numpy as np
from numpy import median
import logging
from concurrent.futures import ProcessPoolExecutor
import matplotlib.pyplot as plt

from gnss import GnssDataParser, TIME_FORMAT
from utils.geo.geo_coords import GeoCoord, COORDS
from utils.analysis import (get_distance_azimuth, interp_data, use_sigma_criteria,
                            estimate_phase_velocity, estimate_periods_lags_values, bandpass_filter,
                            arg_loc_max, arg_loc_min)
from utils.time import convert_to_hours

LIMIT_DTEC = 1
CORR_LIM = 0.5
SINGLE_TIME_ALL_DIR = 'Time/Single/All'
NODE_TIME_ALL_DIR = 'Time/Nodes/All'
SINGLE_MAP_ALL_DIR = 'Map/Single/All'
NODE_MAP_ALL_DIR = 'Map/Nodes/All'
NODE_MAP_DIR = 'Map/Nodes'
NODE_TIME_DIR = 'Tine/Nodes'
LSTID_MAP_DIR = 'Map/LSTID'
MSTID_MAP_DIR = 'Map/MSTID'
LSTID_TIME_DIR = 'Time/LSTID'
MSTID_TIME_DIR = 'Time/MSTID'
LSTID_TIME_ALL_DIR = 'Time/LSTID/All'
MSTID_TIME_ALL_DIR = 'Time/MSTID/All'
LSTID_MAP_ALL_DIR = 'Map/LSTID/All'
MSTID_MAP_ALL_DIR = 'Map/MSTID/All'
LSTID_LON_ALL_DIR = 'Lon/LSTID/All'
MSTID_LON_ALL_DIR = 'Lon/MSTID/All'
LSTID_LAT_ALL_DIR = 'Lat/LSTID/All'
MSTID_LAT_ALL_DIR = 'Lat/MSTID/All'
LSTID_MAP_VEL_DIR = 'Map/LSTID/Vel'
SINGLE_LAT_ALL_DIR = 'Lat/Single/All'
SINGLE_LON_ALL_DIR = 'Lon/Single/All'

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

    def create_time_stamp_data(self, store_dir=SINGLE_TIME_ALL_DIR, time_stamp=None):
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

    def create_coords_stamp_data(self, store_dir=SINGLE_MAP_ALL_DIR, point=None):
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

    def create_lat_time_data(self, store_dir=SINGLE_LON_ALL_DIR, longitude=None):
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

    def create_lon_time_data(self, store_dir=SINGLE_LAT_ALL_DIR, latitude=None):
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
            self.create_coords_stamp_data(store_dir=f'{NODE_MAP_ALL_DIR}', point=point)
            lon += GeoCoord(0, 30)

    def assemble_map(self, time_stamp: dt.datetime):
        time_str = time_stamp.strftime(TIME_FORMAT)
        # map_node_dir = f'{NODE_TIME_ALL_DIR}'
        map_node_dir = f'{MSTID_TIME_DIR}/10-60min'
        dir_name = f"{self.gnss_parser.out_dir}/{self.gnss_parser.add_dir}/{map_node_dir}"
        os.makedirs(dir_name, exist_ok=True)
        map_node_file = f'{self.gnss_parser.get_lon_lat_dtec_file_stem(map_node_dir, time_stamp)}_av.txt'
        # time_node_dir = f'{NODE_MAP_ALL_DIR}'
        time_node_dir = f'{MSTID_MAP_DIR}/10-60min'
        point = dict()
        with open(map_node_file, mode='w') as out_file:
            lat = dTEC_parser.gnss_parser.coord_coverage['min_lat']
            lat_max = dTEC_parser.gnss_parser.coord_coverage['max_lat']
            lon_max = dTEC_parser.gnss_parser.coord_coverage['max_lon']
            while lat <= lat_max:
                lon = dTEC_parser.gnss_parser.coord_coverage['min_lon']
                self.gnss_parser.coord_values['lat'] = lat
                point['lat'] = lat
                while lon <= lon_max:
                    self.gnss_parser.coord_values['lon'] = lon
                    point['lon'] = lon
                    time_node_file = f'{self.gnss_parser.get_time_dtec_file_stem(time_node_dir, point)}_av.txt'
                    if os.path.isfile(time_node_file):
                        with open(time_node_file, mode='r') as in_file:
                            for line in in_file:
                                if time_str in line:
                                    dtec_value = line.split()[-1]
                                    out_file.write(f"{lat.get_float_degs()}\t{lon.get_float_degs()}\t{dtec_value}\n")
                                    break
                    lon += GeoCoord(1, 0)
                lat += GeoCoord(1, 0)

    def get_lstid_map(self, time_stamp: dt.datetime, radius=500):
        coord_coverage = self.gnss_parser.coord_coverage
        output_dir = f"{LSTID_TIME_ALL_DIR}"
        dir_name = f"{self.gnss_parser.out_dir}/{self.gnss_parser.add_dir}/{output_dir}"
        os.makedirs(dir_name, exist_ok=True)
        lstid_file = f'{self.gnss_parser.get_lon_lat_dtec_file_stem(output_dir, time_stamp)}_av.txt'
        time_node_dir = f'{NODE_TIME_ALL_DIR}'
        time_node_file = f'{self.gnss_parser.get_lon_lat_dtec_file_stem(time_node_dir, time_stamp)}_av.txt'
        data = []
        with open(time_node_file, mode='r') as in_file:
            for row in in_file:
                row_float = list(map(float, row.split()))
                data.append(row_float)
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        lat_span = self.gnss_parser.coord_values['lat_span'].get_float_degs()
        lon_span = self.gnss_parser.coord_values['lon_span'].get_float_degs()
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        with open(lstid_file, mode='w') as res_file:
            for lat in plot_lat:
                corr_lon_span = lon_span / math.cos(math.radians(lat))
                n_lon = math.ceil((max_lon - min_lon) / corr_lon_span)
                plot_lon = [min_lon + corr_lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
                for lon in plot_lon:
                    lstid_dtec = []
                    for row in data:
                        node_lat, node_lon, nod_dtec = row
                        dist, _ = get_distance_azimuth(lat, lon, node_lat, node_lon)
                        if dist <= radius:
                            lstid_dtec.append(nod_dtec)
                    if lstid_dtec:
                        dtec_value = median(lstid_dtec)
                        res_file.write(f"{lat}\t{lon}\t{dtec_value}\n")

    def get_mstid_map(self, time_stamp: dt.datetime, radius=150):
        coord_coverage = self.gnss_parser.coord_coverage
        mstid_output_dir = f"{MSTID_TIME_ALL_DIR}"
        mstid_dir_name = f"{self.gnss_parser.out_dir}/{self.gnss_parser.add_dir}/{mstid_output_dir}"
        os.makedirs(mstid_dir_name, exist_ok=True)
        mstid_file = f'{self.gnss_parser.get_lon_lat_dtec_file_stem(mstid_output_dir, time_stamp)}_av.txt'
        lstid_output_dir = f"{LSTID_TIME_ALL_DIR}"
        lstid_file = f'{self.gnss_parser.get_lon_lat_dtec_file_stem(lstid_output_dir, time_stamp)}_av.txt'
        if os.path.isfile(lstid_file):
            lstid_rows = []
            with open(lstid_file, mode='r') as lstid_in_file:
                for line in lstid_in_file:
                    lstid_rows.append(line.split('\t'))
        else:
            print(f"File {lstid_file} does not exist.")
            exit(10)
        time_node_dir = f'{NODE_TIME_ALL_DIR}'
        time_node_file = f'{self.gnss_parser.get_lon_lat_dtec_file_stem(time_node_dir, time_stamp)}_av.txt'
        data = []
        with open(time_node_file, mode='r') as in_file:
            for row in in_file:
                row_float = list(map(float, row.split()))
                data.append(row_float)
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        lat_span = self.gnss_parser.coord_values['lat_span'].get_float_degs()
        lon_span = self.gnss_parser.coord_values['lon_span'].get_float_degs()
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        with open(mstid_file, mode='w') as res_file:
            for lat in plot_lat:
                corr_lon_span = lon_span / math.cos(math.radians(lat))
                n_lon = math.ceil((max_lon - min_lon) / corr_lon_span)
                plot_lon = [min_lon + corr_lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
                for lon in plot_lon:
                    mstid_dtec = []
                    for row in data:
                        node_lat, node_lon, nod_dtec = row
                        dist, _ = get_distance_azimuth(lat, lon, node_lat, node_lon)
                        if dist <= radius:
                            mstid_dtec.append(nod_dtec)
                    if mstid_dtec:
                        dtec_value = median(mstid_dtec)
                        for row in lstid_rows:
                            if (float(row[0]) == lat) and (float(row[1]) == lon):
                                lstid_dtec_value = float(row[2])
                                dtec_value -= lstid_dtec_value
                        res_file.write(f"{lat}\t{lon}\t{dtec_value}\n")

    def get_lstid_time(self, point, radius=500):
        spec_lat = point['lat'].get_float_degs()
        spec_lon = point['lon'].get_float_degs()
        time_coverage = self.gnss_parser.time_coverage
        lat = dTEC_parser.gnss_parser.coord_coverage['min_lat']
        lat_max = dTEC_parser.gnss_parser.coord_coverage['max_lat']
        lon_max = dTEC_parser.gnss_parser.coord_coverage['max_lon']
        dir_name = f"{self.gnss_parser.out_dir}/{self.gnss_parser.add_dir}/{LSTID_MAP_ALL_DIR}"
        os.makedirs(dir_name, exist_ok=True)
        lstid_time_file = f'{self.gnss_parser.get_time_dtec_file_stem(LSTID_MAP_ALL_DIR, point)}_av.txt'
        map_node_dir = f'{NODE_MAP_ALL_DIR}'
        time_stamp = time_coverage['min_time']
        time_max = time_coverage['max_time']
        data = dict()
        while lat <= lat_max:
            lat_float = lat.get_float_degs()
            self.gnss_parser.coord_values['lat'] = lat
            lon = dTEC_parser.gnss_parser.coord_coverage['min_lon']
            while lon <= lon_max:
                lon_float = lon.get_float_degs()
                self.gnss_parser.coord_values['lon'] = lon
                lstid_map_file = f'{self.gnss_parser.get_time_dtec_file_stem(map_node_dir)}_av.txt'
                dist, _ = get_distance_azimuth(spec_lat, spec_lon, lat_float, lon_float)
                if dist <= radius:
                    file_data = []
                    with open(lstid_map_file, mode='r') as in_file:
                        for row in in_file:
                            file_data.append(row.split('\t'))
                    data[(lat_float, lon_float)] = file_data
                lon += GeoCoord(1, 0)
            lat += GeoCoord(1, 0)
        with open(lstid_time_file, mode='w') as out_file:
            while time_stamp <= time_max:
                time_str = time_stamp.strftime(TIME_FORMAT)
                lstid_time_dtec = []
                for key in data:
                    for row in data[key]:
                        if row[0] == time_str:
                            lstid_time_dtec.append(float(row[1]))
                            break
                if lstid_time_dtec:
                    out_file.write(f"{time_str}\t{median(lstid_time_dtec)}\n")
                time_stamp += dt.timedelta(seconds=30)

    def get_mstid_time(self, point, radius=150):
        spec_lat = point['lat'].get_float_degs()
        spec_lon = point['lon'].get_float_degs()
        time_coverage = self.gnss_parser.time_coverage
        lat = dTEC_parser.gnss_parser.coord_coverage['min_lat']
        lat_max = dTEC_parser.gnss_parser.coord_coverage['max_lat']
        lon_max = dTEC_parser.gnss_parser.coord_coverage['max_lon']
        dir_name = f"{self.gnss_parser.out_dir}/{self.gnss_parser.add_dir}/{MSTID_MAP_ALL_DIR}"
        os.makedirs(dir_name, exist_ok=True)
        mstid_time_file = f'{self.gnss_parser.get_time_dtec_file_stem(MSTID_MAP_ALL_DIR, point)}_av.txt'
        lstid_time_file = f'{self.gnss_parser.get_time_dtec_file_stem(LSTID_MAP_ALL_DIR, point)}_av.txt'
        if os.path.isfile(lstid_time_file):
            lstid_time_rows = []
            with open(lstid_time_file, mode='r') as lstid_time_in_file:
                for line in lstid_time_in_file:
                    lstid_time_rows.append(line.split('\t'))
        else:
            print(f"File {lstid_time_file} does not exist.")
            exit(10)
        map_node_dir = f'{NODE_MAP_ALL_DIR}'
        time_stamp = time_coverage['min_time']
        time_max = time_coverage['max_time']
        data = dict()
        while lat <= lat_max:
            lat_float = lat.get_float_degs()
            self.gnss_parser.coord_values['lat'] = lat
            lon = dTEC_parser.gnss_parser.coord_coverage['min_lon']
            while lon <= lon_max:
                lon_float = lon.get_float_degs()
                self.gnss_parser.coord_values['lon'] = lon
                mstid_map_file = f'{self.gnss_parser.get_time_dtec_file_stem(map_node_dir)}_av.txt'
                dist, _ = get_distance_azimuth(spec_lat, spec_lon, lat_float, lon_float)
                if dist <= radius:
                    file_data = []
                    with open(mstid_map_file, mode='r') as in_file:
                        for row in in_file:
                            file_data.append(row.split('\t'))
                    data[(lat_float, lon_float)] = file_data
                lon += GeoCoord(1, 0)
            lat += GeoCoord(1, 0)
        with open(mstid_time_file, mode='w') as out_file:
            while time_stamp <= time_max:
                time_str = time_stamp.strftime(TIME_FORMAT)
                mstid_time_dtec = []
                for key in data:
                    for row in data[key]:
                        if row[0] == time_str:
                            mstid_time_dtec.append(float(row[1]))
                            break
                if mstid_time_dtec:
                    mstid_time_dtec_value = median(mstid_time_dtec)
                    for row in lstid_time_rows:
                        if row[0] == time_str:
                            lstid_time_dtec_value = float(row[1])
                            mstid_time_dtec_value -= lstid_time_dtec_value
                    out_file.write(f"{time_str}\t{mstid_time_dtec_value}\n")
                time_stamp += dt.timedelta(seconds=30)

    def get_lstid_lat_time(self, lon):
        dist_0 = 1000
        lstid_lat_time_file = f'{self.gnss_parser.get_lat_time_dtec_file_stem(LSTID_LON_ALL_DIR, lon)}_av.txt'
        spec_lon_float = lon.get_float_degs()
        coord_coverage = self.gnss_parser.coord_coverage
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        lat_span = self.gnss_parser.coord_values['lat_span'].get_float_degs()
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        point = dict()
        with open(lstid_lat_time_file, mode='w') as out_file:
            for lat in plot_lat:
                c_dist = dist_0
                node_lat = coord_coverage['min_lat']
                while node_lat <= coord_coverage['max_lat']:
                    node_lat_float = node_lat.get_float_degs()
                    node_lon = coord_coverage['min_lon']
                    while node_lon <= coord_coverage['max_lon']:
                        node_lon_float = node_lon.get_float_degs()
                        dist, _ = get_distance_azimuth(lat, spec_lon_float, node_lat_float, node_lon_float)
                        if dist < c_dist:
                            c_dist = dist
                            point['lat'] = node_lat
                            point['lon'] = node_lon
                        node_lon += GeoCoord(1, 0)
                    node_lat += GeoCoord(1, 0)
                node_dir = f"{LSTID_MAP_DIR}/30-120min"
                node_file = f'{self.gnss_parser.get_time_dtec_file_stem(node_dir, point)}_av.txt'
                with open(node_file, mode='r') as in_file:
                    for line in in_file:
                        data = line.split('\t')
                        time_value = data[0]
                        dtec_value = data[1].strip('\n')
                        out_file.write(f"{time_value}\t{lat}\t{dtec_value}\n")

    def get_mstid_lat_time(self, lon):
        dist_0 = 1000
        mstid_lat_time_file = f'{self.gnss_parser.get_lat_time_dtec_file_stem(MSTID_LON_ALL_DIR, lon)}_av.txt'
        spec_lon_float = lon.get_float_degs()
        coord_coverage = self.gnss_parser.coord_coverage
        min_lat = coord_coverage['min_lat'].get_float_degs()
        max_lat = coord_coverage['max_lat'].get_float_degs()
        lat_span = self.gnss_parser.coord_values['lat_span'].get_float_degs()
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        point = dict()
        with open(mstid_lat_time_file, mode='w') as out_file:
            for lat in plot_lat:
                c_dist = dist_0
                node_lat = coord_coverage['min_lat']
                while node_lat <= coord_coverage['max_lat']:
                    node_lat_float = node_lat.get_float_degs()
                    node_lon = coord_coverage['min_lon']
                    while node_lon <= coord_coverage['max_lon']:
                        node_lon_float = node_lon.get_float_degs()
                        dist, _ = get_distance_azimuth(lat, spec_lon_float, node_lat_float, node_lon_float)
                        if dist < c_dist:
                            c_dist = dist
                            point['lat'] = node_lat
                            point['lon'] = node_lon
                        node_lon += GeoCoord(1, 0)
                    node_lat += GeoCoord(1, 0)
                node_dir = f"{MSTID_MAP_DIR}/10-60min"
                node_file = f'{self.gnss_parser.get_time_dtec_file_stem(node_dir, point)}_av.txt'
                with open(node_file, mode='r') as in_file:
                    for line in in_file:
                        data = line.split('\t')
                        time_value = data[0]
                        dtec_value = data[1].strip('\n')
                        out_file.write(f"{time_value}\t{lat}\t{dtec_value}\n")

    def get_lstid_lon_time(self, lat):
        dist_0 = 1000
        self.gnss_parser.coord_values['lat'] = lat
        lstid_lon_time_file = f'{self.gnss_parser.get_lon_time_dtec_file_stem(LSTID_LAT_ALL_DIR, lat)}_av.txt'
        spec_lat_float = lat.get_float_degs()
        coord_coverage = self.gnss_parser.coord_coverage
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        lon_span = self.get_corr_lon_span()
        n_lon = math.ceil((max_lon - min_lon) / lon_span)
        plot_lon = [min_lon + lon_span / 2 + j * lon_span for j in range(n_lon)]
        point = dict()
        with open(lstid_lon_time_file, mode='w') as out_file:
            for lon in plot_lon:
                c_dist = dist_0
                node_lat = coord_coverage['min_lat']
                while node_lat <= coord_coverage['max_lat']:
                    node_lat_float = node_lat.get_float_degs()
                    node_lon = coord_coverage['min_lon']
                    while node_lon <= coord_coverage['max_lon']:
                        node_lon_float = node_lon.get_float_degs()
                        dist, _ = get_distance_azimuth(spec_lat_float, lon, node_lat_float, node_lon_float)
                        if dist < c_dist:
                            c_dist = dist
                            point['lat'] = node_lat
                            point['lon'] = node_lon
                        node_lon += GeoCoord(1, 0)
                    node_lat += GeoCoord(1, 0)
                node_dir = f"{LSTID_MAP_DIR}/30-120min"
                node_file = f'{self.gnss_parser.get_time_dtec_file_stem(node_dir, point)}_av.txt'
                with open(node_file, mode='r') as in_file:
                    for line in in_file:
                        data = line.split('\t')
                        time_value = data[0]
                        dtec_value = data[1].strip('\n')
                        out_file.write(f"{time_value}\t{lon}\t{dtec_value}\n")

    def get_mstid_lon_time(self, lat):
        dist_0 = 1000
        self.gnss_parser.coord_values['lat'] = lat
        mstid_lon_time_file = f'{self.gnss_parser.get_lon_time_dtec_file_stem(MSTID_LAT_ALL_DIR, lat)}_av.txt'
        spec_lat_float = lat.get_float_degs()
        coord_coverage = self.gnss_parser.coord_coverage
        min_lon = coord_coverage['min_lon'].get_float_degs()
        max_lon = coord_coverage['max_lon'].get_float_degs()
        lon_span = self.get_corr_lon_span()
        n_lon = math.ceil((max_lon - min_lon) / lon_span)
        plot_lon = [min_lon + lon_span / 2 + j * lon_span for j in range(n_lon)]
        point = dict()
        with open(mstid_lon_time_file, mode='w') as out_file:
            for lon in plot_lon:
                c_dist = dist_0
                node_lat = coord_coverage['min_lat']
                while node_lat <= coord_coverage['max_lat']:
                    node_lat_float = node_lat.get_float_degs()
                    node_lon = coord_coverage['min_lon']
                    while node_lon <= coord_coverage['max_lon']:
                        node_lon_float = node_lon.get_float_degs()
                        dist, _ = get_distance_azimuth(spec_lat_float, lon, node_lat_float, node_lon_float)
                        if dist < c_dist:
                            c_dist = dist
                            point['lat'] = node_lat
                            point['lon'] = node_lon
                        node_lon += GeoCoord(1, 0)
                    node_lat += GeoCoord(1, 0)
                node_dir = f"{MSTID_MAP_DIR}/10-60min"
                node_file = f'{self.gnss_parser.get_time_dtec_file_stem(node_dir, point)}_av.txt'
                with open(node_file, mode='r') as in_file:
                    for line in in_file:
                        data = line.split('\t')
                        time_value = data[0]
                        dtec_value = data[1].strip('\n')
                        out_file.write(f"{time_value}\t{lon}\t{dtec_value}\n")

    def get_filtered_time(self, point, periods=None):
        time_coverage = self.gnss_parser.time_coverage
        # input_file = f'{self.gnss_parser.get_time_dtec_file_stem(LSTID_MAP_ALL_DIR, point)}_av.txt'
        input_file = f'{self.gnss_parser.get_time_dtec_file_stem(MSTID_MAP_ALL_DIR, point)}_av.txt'
        if periods is None:
            # store_dir = f'{LSTID_MAP_DIR}/Interp'
            store_dir = f'{MSTID_MAP_DIR}/Interp'
        else:
            # store_dir = f'{LSTID_MAP_DIR}/{periods[0]}-{periods[1]}min'
            store_dir = f'{MSTID_MAP_DIR}/{periods[0]}-{periods[1]}min'
        filtered_file = f'{self.gnss_parser.get_time_dtec_file_stem(store_dir, point)}_av.txt'
        time = time_coverage['min_time']
        time_max = time_coverage['max_time']
        time_orig = []
        while time <= time_max:
            time_orig.append(time)
            time += dt.timedelta(seconds=30)
        raw_data = []
        file_time = []
        file_dtec = []
        with open(input_file, mode='r') as in_file:
            for line in in_file:
                raw_data.append(line.split('\t'))
            for row in raw_data:
                file_time.append(dt.datetime.strptime(row[0], TIME_FORMAT))
                file_dtec.append(float(row[1]))
        if file_time:
            if file_time[0] != time_orig[0]:
                file_time.insert(0, time_orig[0])
                file_dtec.insert(0, 0)
            if file_time[-1] != time_orig[-1]:
                file_time.append(time_orig[-1])
                file_dtec.append(0)
            try:
                file_dtec_corr = use_sigma_criteria(file_dtec, window=240)
                file_dtec_interp = interp_data(file_time, file_dtec_corr, time_orig, k=1)
                if periods is None:
                    output_dtec = file_dtec_interp
                else:
                    min_period = 2 * periods[0]
                    max_period = 2 * periods[1]
                    output_dtec = bandpass_filter(file_dtec_interp, min_period, max_period)
                with open(filtered_file, mode='w') as out_file:
                    for i in range(len(time_orig)):
                        time_str = time_orig[i].strftime(TIME_FORMAT)
                        out_file.write(f'{time_str}\t{output_dtec[i]}\n')
            except Exception:
                print(f"Failed to process {input_file}.")

    def get_lstid_velocity(self, node):
        def plot_lstid_params():
            min_time = dt.datetime(2023, 4, 1, 0, 0)
            max_time = dt.datetime(2023, 4, 2, 0, 0)
            fig, ax = plt.subplots(5, 1)
            fig.set_size_inches(9, 15)
            ax[0].set_title('MSTID characteristics on 2023-04-01')
            ax[0].plot(time_orig, prev_lat_dtec,
                       label=f"{prev_lat_node['lat'].degs} N, {prev_lat_node['lon'].degs} E")
            ax[0].plot(time_orig, next_lat_dtec,
                       label=f"{next_lat_node['lat'].degs} N, {next_lat_node['lon'].degs} E")
            ax[0].set_ylabel('dTEC (TECU)')
            ax[0].legend()
            ax[0].set_xlim([min_time, max_time])
            ax[1].plot(time_orig, prev_lon_dtec,
                       label=f"{prev_lon_node['lat'].degs} N, {prev_lon_node['lon'].degs} E")
            ax[1].plot(time_orig, next_lon_dtec,
                       label=f"{next_lon_node['lat'].degs} N, {next_lon_node['lon'].degs} E")
            ax[1].set_ylabel('dTEC (TECU)')
            ax[1].legend()
            ax[1].set_xlim([min_time, max_time])
            ax[2].scatter(time_vel, lat_period_vel, label='Latitude', s=2)
            ax[2].scatter(time_vel, lon_period_vel, label='Longitude', s=2)
            ax[2].set_ylabel('Main period (min)')
            ax[2].grid(axis='y')
            ax[2].legend()
            ax[2].set_ylim([10, 60])
            ax[2].set_xlim([min_time, max_time])
            ax[3].scatter(time_vel, abs_velocity, label=f"{node['lat'].degs} N, {node['lon'].degs} E", s=2)
            ax[3].grid(axis='y')
            ax[3].set_ylabel('Velocity (m/s)')
            ax[3].legend()
            ax[3].set_ylim([0, 1000])
            ax[3].set_xlim([min_time, max_time])
            ax[4].scatter(time_vel, azimuth, label=f"{node['lat'].degs} N, {node['lon'].degs} E", s=2)
            ax[4].set_ylabel('Azimuth (deg)')
            ax[4].grid(axis='y')
            ax[4].legend()
            ax[4].set_xlabel('Time (UT)')
            ax[4].set_ylim([0, 360])
            ax[4].set_xlim([min_time, max_time])
            plt.tight_layout()
            plt.show()

        def parse_time_dtec_file(node_file):
            dtec_values = []
            with open(node_file, mode='r') as in_file:
                for line in in_file:
                    row = line.split('\t')
                    dtec_values.append(float(row[1]))
            return np.array(dtec_values)

        lat_delta = GeoCoord(1, 0)
        lon_delta = GeoCoord(1, 0)

        prev_lat_node = {
            'lat': node['lat'] - lat_delta,
            'lon': node['lon']
        }
        next_lat_node = {
            'lat': node['lat'] + lat_delta,
            'lon': node['lon']
        }
        prev_lon_node = {
            'lat': node['lat'],
            'lon': node['lon'] - lon_delta
        }
        next_lon_node = {
            'lat': node['lat'],
            'lon': node['lon'] + lon_delta
        }
        node_dir = f"{MSTID_MAP_DIR}/10-60min"
        # node_dir = f"{LSTID_MAP_DIR}/30-120min"
        prev_lat_node_file = f"{self.gnss_parser.get_time_dtec_file_stem(node_dir, prev_lat_node)}_av.txt"
        next_lat_node_file = f"{self.gnss_parser.get_time_dtec_file_stem(node_dir, next_lat_node)}_av.txt"
        prev_lon_node_file = f"{self.gnss_parser.get_time_dtec_file_stem(node_dir, prev_lon_node)}_av.txt"
        next_lon_node_file = f"{self.gnss_parser.get_time_dtec_file_stem(node_dir, next_lon_node)}_av.txt"
        c_time = self.gnss_parser.time_coverage['min_time']
        time_max = self.gnss_parser.time_coverage['max_time']
        time_orig = []
        while c_time <= time_max:
            time_orig.append(c_time)
            c_time += dt.timedelta(seconds=30)

        prev_lat_dtec = parse_time_dtec_file(prev_lat_node_file)
        next_lat_dtec = parse_time_dtec_file(next_lat_node_file)
        prev_lon_dtec = parse_time_dtec_file(prev_lon_node_file)
        next_lon_dtec = parse_time_dtec_file(next_lon_node_file)
        window = 300
        lat_period_list, lat_lag_list, lat_corr_list = estimate_periods_lags_values(next_lat_dtec, prev_lat_dtec,
                                                                                    window=window, delta_t=0.5)
        lon_period_list, lon_lag_list, lon_corr_list = estimate_periods_lags_values(next_lon_dtec, prev_lon_dtec,
                                                                                    window=window, delta_t=0.5)
        dist_lat, azm_lat = get_distance_azimuth(prev_lat_node['lat'].get_float_degs(),
                                                 prev_lat_node['lon'].get_float_degs(),
                                                 next_lat_node['lat'].get_float_degs(),
                                                 next_lat_node['lon'].get_float_degs())
        dist_lon, azm_lon = get_distance_azimuth(prev_lon_node['lat'].get_float_degs(),
                                                 prev_lon_node['lon'].get_float_degs(),
                                                 next_lon_node['lat'].get_float_degs(),
                                                 next_lon_node['lon'].get_float_degs())
        vel_dir = f"{MSTID_MAP_DIR}/10-60min/Vel1"
        # vel_dir = f"{LSTID_MAP_DIR}/30-120min/Vel1"
        lstid_vel_file = f'{self.gnss_parser.get_time_dtec_file_stem(vel_dir, node)}_av_test.txt'
        abs_velocity = []
        azimuth = []
        time_vel = []
        lat_period_vel = []
        lon_period_vel = []
        lat_corr_vel = []
        lon_corr_vel = []
        with open(lstid_vel_file, mode='w') as out_file:
            for i in range(len(time_orig)):
                set_1 = (dist_lat, azm_lat, lat_lag_list[i])
                set_2 = (dist_lon, azm_lon, lon_lag_list[i])
                vel, azm = estimate_phase_velocity(set_1, set_2)
                vel *= (1000 / 60)
                period = (lat_period_list[i] + lon_period_list[i]) / 2
                time_str = time_orig[i].strftime(TIME_FORMAT)
                lat_corr = lat_corr_list[i]
                lon_corr = lon_corr_list[i]
                if (vel < 1000) and (lat_corr > CORR_LIM) and (lon_corr > CORR_LIM):
                    out_file.write(f'{time_str}\t{vel}\t{azm}\t{period}\t{lat_corr_list[i]}\t{lon_corr_list[i]}\n')
                    time_vel.append(time_orig[i])
                    abs_velocity.append(vel)
                    azimuth.append(azm)
                    lat_period_vel.append(lat_period_list[i])
                    lon_period_vel.append(lon_period_list[i])
                    lat_corr_vel.append(lat_corr_list[i])
                    lon_corr_vel.append((lon_corr_list[i]))
        plot_lstid_params()

    def find_max_values(self, point, time_ref, time_limits):
        low_time, up_time = time_limits
        raw_data = []
        file_time = []
        file_dtec = []
        input_file = f'{self.gnss_parser.get_time_dtec_file_stem(f"{LSTID_MAP_DIR}/30-120min", point)}_av.txt'
        with open(input_file, mode='r') as in_file:
            for line in in_file:
                raw_data.append(line.split('\t'))
            for row in raw_data:
                cur_time = dt.datetime.strptime(row[0], TIME_FORMAT)
                if low_time <= cur_time <= up_time:
                    file_time.append(cur_time)
                    file_dtec.append(float(row[1]))
        max_indices = arg_loc_max(file_dtec)
        max_dtec_times = []
        for index in max_indices:
            max_dtec_times.append(file_time[index])
        delta_t = 24
        max_time = dTEC_parser.gnss_parser.time_coverage['min_time']
        for c_time in max_dtec_times:
            c_delta_t = abs(convert_to_hours(c_time) - convert_to_hours(time_ref))
            if c_delta_t < delta_t:
                delta_t = c_delta_t
                max_time = c_time
        max_index = file_time.index(max_time)
        max_dtec = file_dtec[max_index]
        global_max_dtec = max(file_dtec)
        global_max_index = file_dtec.index(global_max_dtec)
        global_max_time = file_time[global_max_index]
        return max_time, max_dtec, global_max_time, global_max_dtec

    def get_params(self):
        input_file = 'maximums.txt'
        output_file = 'MSTID_Azimuth_new.txt'
        raw_data = []
        file_time = []
        file_lat = []
        file_lon = []
        with open(input_file, mode='r') as in_file:
            for line in in_file:
                raw_data.append(line.split('\t'))
        for row in raw_data:
            file_lat.append(float(row[0]))
            file_lon.append(float(row[1]))
            # time_str = row[2].strip('\n')
            time_str = "2023-04-01 19:30:00"
            file_time.append(time_str)
        lat_list = list(map(int, file_lat))
        lon_list = list(map(int, file_lon))
        data_list = list(zip(lat_list, lon_list, file_time))
        with open(output_file, mode='w') as out_file:
            for data in data_list:
                lat, lon, max_time = data
                if (lat < 60) and (lon < 21):
                    point = {
                        'lat': GeoCoord(lat, 0),
                        'lon': GeoCoord(lon, 0)
                    }
                    vel_dir = f"{MSTID_MAP_DIR}/10-60min/Vel1"
                    lstid_vel_file = f"{self.gnss_parser.get_time_dtec_file_stem(vel_dir, point)}_av_test.txt"
                    if os.path.isfile(lstid_vel_file):
                        with open(lstid_vel_file, mode='r') as vel_file:
                            for line in vel_file:
                                row = line.split('\t')
                                if dt.datetime.strptime(row[0], TIME_FORMAT) == dt.datetime.strptime(max_time,
                                                                                                     '%Y-%m-%d %H:%M:%S'):
                                    period = row[3].strip('\n')
                                    velocity = row[1]
                                    azimuth = row[2]
                                    if float(velocity) < 1000:
                                        out_file.write(f"{lat}\t{lon}\t{azimuth}\n")


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
    parser.add_argument("-d", "--directory", help="Path to the current directory in format path/to/the/directory.",
                        type=str,
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
    parser.add_argument("-L", "--lstid_radius", help="Radius value for retrieval LSTIDs (km).",
                        default=500, type=int)
    parser.add_argument("-M", "--mstid_radius", help="Radius value for retrieval MSTIDs (km).",
                        default=150, type=int)
    parser.add_argument("-f", "--filter", help="Filtered time variations.",
                        default=(10, 60), type=tuple)

    parser.add_argument("-a", "--all_times", help="Analysis for all times.", action='store_true')
    parser.add_argument("-s", "--assemble", help="Assemble map from nodes.", action='store_true')
    parser.add_argument("-l", "--lstid_map", help="Retrieve LSTID signatures in space domain.", action='store_true')
    parser.add_argument("-m", "--mstid_map", help="Retrieve MSTID signatures in space domain.", action='store_true')
    parser.add_argument("-Q", "--lstid_time", help="Retrieve LSTID signatures in time domain.", action='store_true')
    parser.add_argument("-q", "--mstid_time", help="Retrieve MSTID signatures in time domain.", action='store_true')
    parser.add_argument("-p", "--specific", help="Analysis for specific parameters.", action='store_true')
    parser.add_argument("-V", "--lstid_velocity", help="Evaluation of LSTID phase velocity.", action='store_true')
    parser.add_argument("-v", "--mstid_velocity", help="Evaluation of MSTID phase velocity.", action='store_true')
    parser.add_argument("-F", "--lstid_filter", help="Evaluation of filtered LSTID variations.", action='store_true')
    parser.add_argument("-b", "--local", help="Local max.", action='store_true')
    parser.add_argument("-B", "--param", help="", action='store_true')
    parser.add_argument("-I", "--lstid_lon", help="", action='store_true')
    parser.add_argument("-J", "--lstid_lat", help="", action='store_true')

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
    dTEC_parser.gnss_parser.coord_values = {
        'lat': lat, 'lat_span': LAT_SPAN,
        'lon': lon, 'lon_span': LON_SPAN,
    }

    if args.specific or args.all_times:
        dTEC_parser.read_data()

    if args.specific:
        with ProcessPoolExecutor() as executor:
            executor.submit(dTEC_parser.create_time_stamp_data)
            executor.submit(dTEC_parser.create_coords_stamp_data)
            executor.submit(dTEC_parser.create_lat_time_data)
            executor.submit(dTEC_parser.create_lon_time_data)

    lat_min = dTEC_parser.gnss_parser.coord_coverage['min_lat']
    lat_max = dTEC_parser.gnss_parser.coord_coverage['max_lat']
    lon_min = dTEC_parser.gnss_parser.coord_coverage['min_lon']
    lon_max = dTEC_parser.gnss_parser.coord_coverage['max_lon']

    if args.all_times:
        latitudes = []
        lat_min = GeoCoord(41, 30)
        lat_max = GeoCoord(50, 0)
        current_lat = lat_min
        while current_lat <= lat_max:
            latitudes.append(current_lat)
            current_lat += GeoCoord(0, 30)
        with ProcessPoolExecutor() as executor:
            executor.map(dTEC_parser.analyze_all_coords, latitudes)

    c_time = dt.datetime(year=year, month=month, day=day, hour=0, minute=0)
    time_max = dt.datetime(year=year, month=month, day=day, hour=23, minute=59)

    if args.assemble:
        while c_time <= time_max:
            dTEC_parser.assemble_map(c_time)
            c_time += dt.timedelta(minutes=1)

    c_time = dt.datetime(year=year, month=month, day=day, hour=0, minute=0)

    if args.lstid_map:
        while c_time <= time_max:
            dTEC_parser.get_lstid_map(c_time, radius=args.lstid_radius)
            c_time += dt.timedelta(minutes=1)
    if args.mstid_map:
        while c_time <= time_max:
            dTEC_parser.get_mstid_map(c_time, radius=args.mstid_radius)
            c_time += dt.timedelta(minutes=1)

    if args.lstid_time:
        lat = lat_min
        while lat <= lat_max:
            lon = lon_min
            while lon <= lon_max:
                point = {
                    'lat': lat,
                    'lon': lon
                }
                dTEC_parser.get_lstid_time(point)
                lon += GeoCoord(1, 0)
            lat += GeoCoord(1, 0)
    if args.mstid_time:
        lat = lat_min
        while lat <= lat_max:
            lon = lon_min
            while lon <= lon_max:
                point = {
                    'lat': lat,
                    'lon': lon
                }
                dTEC_parser.get_mstid_time(point)
                lon += GeoCoord(1, 0)
            lat += GeoCoord(1, 0)

    if args.lstid_filter:
        lat = lat_min
        while lat <= lat_max:
            lon = lon_min
            while lon <= lon_max:
                point = {
                    'lat': lat,
                    'lon': lon
                }
                dTEC_parser.get_filtered_time(point, args.filter)
                lon += GeoCoord(1, 0)
            lat += GeoCoord(1, 0)

    if args.lstid_velocity:
        lat = lat_min + GeoCoord(2, 0)
        while lat <= lat_max - GeoCoord(2, 0):
            lon = lon_min + GeoCoord(2, 0)
            while lon <= lon_max - GeoCoord(2, 0):
                node = {
                    'lat': lat,
                    'lon': lon
                }
                try:
                    dTEC_parser.get_lstid_velocity(node)
                except Exception:
                    print(f"lat: {node['lat'].degs}, lon: {node['lon'].degs} is failed.")
                lon += GeoCoord(1, 0)
            lat += GeoCoord(1, 0)
    if args.lstid_velocity:
        node = {
            'lat': GeoCoord(40,0),
            'lon': GeoCoord(0, 0)
        }
        dTEC_parser.get_lstid_velocity(node)

    if args.local:
        time_ref = dt.datetime(2023, 4, 1, 19, 30, 0)
        low_time = dt.datetime(2023, 4, 1, 18, 0, 0)
        up_time = dt.datetime(2023, 4, 1, 21, 0, 0)
        lat = lat_min
        lat_max = GeoCoord(65, 0)
        times_ref = []
        lon = lon_min
        output_file = 'maximums1.txt'
        while lon <= lon_max:
            times_ref.append(time_ref)
            lon += GeoCoord(1, 0)
        with open(output_file, mode='w') as out_file:
            while lat <= lat_max:
                lon = lon_min
                i_lon = 0
                while lon <= lon_max:
                    point = {
                        'lat': lat,
                        'lon': lon
                    }
                    max_time, max_dtec, global_max_time, global_max_dtec = (
                        dTEC_parser.find_max_values(point, times_ref[i_lon], (low_time, up_time)))
                    times_ref[i_lon] = max_time
                    out_file.write(f"{point['lat'].get_float_degs()}\t"
                                   f"{point['lon'].get_float_degs()}\t"
                                   f"{max_time}\n")
                    lon += GeoCoord(1, 0)
                    i_lon += 1
                lat += GeoCoord(1, 0)

    if args.param:
        dTEC_parser.get_params()

    if args.lstid_lon:
        dTEC_parser.get_mstid_lat_time(GeoCoord(3, 0))

    if args.lstid_lat:
        dTEC_parser.get_mstid_lon_time(GeoCoord(40, 0))
