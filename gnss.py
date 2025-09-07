from zipfile import Path
from sys import argv
import os
import datetime as dt

TIME_FORMAT = '%Y.%m.%d %H:%M:%S'


class GnssArchive:
    def __init__(self, archive_name: str):
        self.filter_dirs = {3600: 'Window_3600_Seconds',
                            7200: 'Window_7200_Seconds'}
        self.archive_name = archive_name
        self.root_dir = self.__get_root_dir()
        self.day_number = self.__get_day_number()
        self.year = self.get_year()
        self.date = self.__get_date()

    def __get_root_dir(self):
        return self.archive_name.split('/')[-1].split('.')[0]

    def __get_day_number(self):
        return self.root_dir[:3]

    def get_year(self):
        return self.root_dir[4:8]

    def get_month(self):
        return self.root_dir[9:11]

    def get_day(self):
        return self.root_dir[12:]

    def __get_date(self):
        return self.root_dir[4:]

    def get_parsed_file_stem(self, parsed_dir, filter_sec):
        prefix = self.date
        suffix = filter_sec
        dirs = f"{parsed_dir}/{self.year}/{prefix}/{suffix}"
        os.makedirs(dirs, exist_ok=True)
        return f"{dirs}/{prefix}_{suffix}"

    def get_filter_dir(self, filter_sec):
        filter_dir = self.filter_dirs.get(filter_sec)
        if not filter_dir:
            raise ValueError("Wrong value of filter window. Must be 3600 or 7200")
        return filter_dir

    def get_receiver_list(self):
        rec_paths = Path(self.archive_name, f'{self.root_dir}/')
        rec_dirs = [rec_dir.name for rec_dir in rec_paths.iterdir() if rec_dir.is_dir()]
        rec_dirs.sort()
        return rec_dirs

    def get_receiver_coords(self):
        rec_names = []
        rec_lat = []
        rec_lon = []
        at_file = f"{self.root_dir}/Sites.txt"
        rec_file_name = Path(self.archive_name, at_file)
        if rec_file_name.exists():
            with rec_file_name.open(mode='r') as rec_file:
                _ = rec_file.readline()
                for line in rec_file:
                    data = line.split()
                    rec_names.append(data[0])
                    rec_lat.append(float(data[1]))
                    rec_lon.append(float(data[2]))
        return rec_names, rec_lon, rec_lat

    def parse_gnss_archive(self, parsed_dir, filter_sec, min_elm=30):
        out_file_name = f"{self.get_parsed_file_stem(parsed_dir, filter_sec)}.txt"
        rec_num_file = f"{self.get_parsed_file_stem(parsed_dir, filter_sec)}.num"
        filter_dir = self.get_filter_dir(filter_sec)
        if not os.path.isfile(rec_num_file):
            with open(rec_num_file, mode='w') as num_file:
                num_file.write('0')
        rec_dirs = self.get_receiver_list()
        print(rec_dirs)
        rec_count = len(rec_dirs)
        with open(rec_num_file, mode='r') as num_file:
            rec_index = int(num_file.read())
        with open(out_file_name, "a") as out_file:
            for i in range(rec_index, rec_count):
                gnss_data = []
                rec_dir = rec_dirs[rec_index]
                rec_num = rec_index + 1
                print(f"{rec_num} of {rec_count}.")
                for j in range(1, 33):
                    at_file = f"{self.root_dir}/{rec_dir}/{filter_dir}/G{str(j).zfill(2)}.txt"
                    g_file = Path(self.archive_name, at_file)
                    if g_file.exists():
                        with g_file.open(mode='r') as txt:
                            gnss_data_title = txt.readline().split()
                            lines_raw = txt.readlines()
                        lines = list(filter(lambda x:
                                            float(x.split()[gnss_data_title.index('elm')]) > min_elm,
                                            lines_raw))
                        gnss_data.extend(lines)
                out_file.writelines(gnss_data)
                out_file.flush()
                rec_index += 1
                with open(rec_num_file, mode='w') as num_file:
                    num_file.write(str(rec_index))
        print("Reading is completed.")


class GnssDataParser:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.add_dir: str | None = None
        self.coord_values: dict | None = {'lon': None, 'lon_span': None,
                                          'lat': None, 'lat_span': None}
        self.coord_coverage: dict | None = {'min_lon': None, 'max_lon': None,
                                            'min_lat': None, 'max_lat': None}
        self.time_values: dict | None = {'time': None, 'time_span': None}
        self.time_coverage: dict | None = {'min_time': None, 'max_time': None}
        self.data_title: list = ['hour', 'min', 'sec', 'dTEC', 'azm', 'elm', 'gdlat', 'gdlon']
        self.data: list = []
        self.time_dtec: list = []
        self.lon_lat_dtec: list = []
        self.lon_time_dtec: list = []
        self.lat_time_dtec: list = []

    def get_time_dtec_file_stem(self, store_dir, point=None):
        if point is None:
            point = {
                'lat': self.coord_values['lat'],
                'lon': self.coord_values['lon']
            }
        if all((point['lon'], self.coord_values['lon_span'],
                point['lat'], self.coord_values['lat_span'])):
            dir_name = f"{self.out_dir}/{self.add_dir}/{store_dir}"
            os.makedirs(dir_name, exist_ok=True)
            file_name = (f"{point['lon'].degs}d"
                         f"{point['lon'].mins}m_"
                         f"{self.coord_values['lon_span'].degs}d"
                         f"{self.coord_values['lon_span'].mins}m_lon_"
                         f"{point['lat'].degs}d"
                         f"{point['lat'].mins}m_"
                         f"{self.coord_values['lat_span'].degs}d"
                         f"{self.coord_values['lat_span'].mins}m_lat")
            return f"{dir_name}/{file_name}"
        else:
            raise TypeError("Coordinates are not defined")

    def get_lon_time_dtec_file_stem(self, store_dir, latitude=None):
        if latitude is None:
            latitude = self.coord_values['lat']
        if all((latitude, self.coord_values['lat_span'])):
            dir_name = f"{self.out_dir}/{self.add_dir}/{store_dir}"
            os.makedirs(dir_name, exist_ok=True)
            file_name = (f"{latitude.degs}d"
                         f"{latitude.mins}m_"
                         f"{self.coord_values['lat_span'].degs}d"
                         f"{self.coord_values['lat_span'].mins}m_lat")
            return f"{dir_name}/{file_name}"
        else:
            raise TypeError("Latitudes are not defined")

    def get_lat_time_dtec_file_stem(self, store_dir, longitude=None):
        if longitude is None:
            longitude = self.coord_values['lon']
        if all((longitude, self.coord_values['lon_span'])):
            dir_name = f"{self.out_dir}/{self.add_dir}/{store_dir}"
            os.makedirs(dir_name, exist_ok=True)
            file_name = (f"{longitude.degs}d"
                         f"{longitude.mins}m_"
                         f"{self.coord_values['lon_span'].degs}d"
                         f"{self.coord_values['lon_span'].mins}m_lon")
            return f"{dir_name}/{file_name}"
        else:
            raise TypeError("Longitudes are not defined")

    def get_lon_lat_dtec_file_stem(self, store_dir, time_stamp=None):
        if time_stamp is None:
            time_stamp = self.time_values['time']
        if all((time_stamp, self.time_values['time_span'])):
            dir_name = f"{self.out_dir}/{self.add_dir}/{store_dir}"
            os.makedirs(dir_name, exist_ok=True)
            td = self.time_values['time_span']
            hours, minutes, seconds = td.seconds // 3600, td.seconds // 60 % 60, td.seconds
            file_name = (f"{time_stamp.strftime('%H%M%S')}_"
                         f"{hours}{minutes}{seconds}")
            return f"{dir_name}/{file_name}"
        else:
            raise TypeError("Times are not defined")

    def read_gnss_data(self, file_name):
        if not self.data:
            with open(file_name, mode='r') as in_file:
                self.data = in_file.readlines()

    def get_time_dtec(self, store_dir, point=None):
        if point is None:
            point = {
                'lat': self.coord_values['lat'],
                'lon': self.coord_values['lon']
            }
        current_date = self.time_coverage['min_time'].date()
        time_file_name = f"{self.get_time_dtec_file_stem(store_dir, point)}.txt"
        if os.path.isfile(time_file_name):
            with open(time_file_name, mode='r') as time_file:
                raw_data = [line.split('\t') for line in time_file]
                time_dtec = list(zip(*raw_data))
                time_data = [dt.datetime.strptime(x, TIME_FORMAT) for x in time_dtec[0]]
                dtec_data = list(map(float, time_dtec[1]))
                self.time_dtec = list(zip(time_data, dtec_data))
        else:
            self.time_dtec = []
            current_lon = point['lon'].get_float_degs()
            lon_span = self.coord_values['lon_span'].get_float_degs()
            current_lat = point['lat'].get_float_degs()
            lat_span = self.coord_values['lat_span'].get_float_degs()
            with open(time_file_name, mode='w') as time_file:
                for line in self.data:
                    data = list(map(float, line.split()))
                    g_data = dict(zip(self.data_title, data))
                    if all((g_data['gdlat'] >= current_lat - lat_span / 2,
                            g_data['gdlat'] <= current_lat + lat_span / 2,
                            g_data['gdlon'] >= current_lon - lon_span / 2,
                            g_data['gdlon'] <= current_lon + lon_span / 2)):
                        c_time = dt.datetime.combine(current_date, dt.time(int(g_data['hour']),
                                                                           int(g_data['min']),
                                                                           int(g_data['sec'])))
                        current_time = c_time.strftime(TIME_FORMAT)
                        time_dtec_data = (c_time, g_data['dTEC'])
                        self.time_dtec.append(time_dtec_data)
                        time_file.write(f"{current_time}\t{g_data['dTEC']}\n")

    def get_lon_lat_dtec(self, store_dir, time_stamp=None):
        if time_stamp is None:
            time_stamp = self.time_values['time']
        coord_file_name = f"{self.get_lon_lat_dtec_file_stem(store_dir, time_stamp)}.txt"
        if os.path.isfile(coord_file_name):
            with open(coord_file_name, mode='r') as coord_file:
                self.lon_lat_dtec = [list(map(float, line.split())) for line in coord_file]
        else:
            self.lon_lat_dtec = []
            with open(coord_file_name, mode='w') as coord_file:
                for line in self.data:
                    data = list(map(float, line.split()))
                    g_data = dict(zip(self.data_title, data))
                    current_time = time_stamp
                    time_span = self.time_values['time_span']
                    c_time = dt.datetime.combine(current_time.date(),
                                                 dt.time(int(g_data['hour']), int(g_data['min']), int(g_data['sec'])))
                    time_cond = ((c_time >= current_time - time_span / 2) and
                                 (c_time <= current_time + time_span / 2))
                    if time_cond:
                        lon_lat_dtec_data = [g_data['gdlon'], g_data['gdlat'], g_data['dTEC']]
                        self.lon_lat_dtec.append(lon_lat_dtec_data)
                        coord_file.write(f"{g_data['gdlon']}\t{g_data['gdlat']}\t{g_data['dTEC']}\n")

    def get_lon_time_dtec(self, store_dir, latitude=None):
        if latitude is None:
            latitude = self.coord_values['lat']
        current_date = self.time_coverage['min_time'].date()
        lon_time_file_name = f"{self.get_lon_time_dtec_file_stem(store_dir, latitude)}.txt"
        if os.path.isfile(lon_time_file_name):
            with open(lon_time_file_name, mode='r') as lon_time_file:
                raw_data = [line.split('\t') for line in lon_time_file]
                lon_time_dtec = list(zip(*raw_data))
                time_data = [dt.datetime.strptime(x, TIME_FORMAT) for x in lon_time_dtec[0]]
                lon_data = list(map(float, lon_time_dtec[1]))
                dtec_data = list(map(float, lon_time_dtec[2]))
                self.lon_time_dtec = list(zip(time_data, lon_data, dtec_data))
        else:
            self.lon_time_dtec = []
            current_lat = latitude.get_float_degs()
            lat_span = self.coord_values['lat_span'].get_float_degs()
            with open(lon_time_file_name, mode='w') as lon_time_file:
                for line in self.data:
                    data = list(map(float, line.split()))
                    g_data = dict(zip(self.data_title, data))
                    if all((g_data['gdlat'] >= current_lat - lat_span / 2,
                            g_data['gdlat'] <= current_lat + lat_span / 2)):
                        c_time = dt.datetime.combine(current_date, dt.time(int(g_data['hour']),
                                                                           int(g_data['min']),
                                                                           int(g_data['sec'])))
                        current_time = c_time.strftime(TIME_FORMAT)
                        lon_time_dtec_data = (c_time, g_data['gdlon'], g_data['dTEC'])
                        self.lon_time_dtec.append(lon_time_dtec_data)
                        lon_time_file.write(f"{current_time}\t{g_data['gdlon']}\t{g_data['dTEC']}\n")

    def get_lat_time_dtec(self, store_dir, longitude=None):
        if longitude is None:
            longitude = self.coord_values['lon']
        current_date = self.time_coverage['min_time'].date()
        lat_time_file_name = f"{self.get_lat_time_dtec_file_stem(store_dir, longitude)}.txt"
        if os.path.isfile(lat_time_file_name):
            with open(lat_time_file_name, mode='r') as lat_time_file:
                raw_data = [line.split('\t') for line in lat_time_file]
                lat_time_dtec = list(zip(*raw_data))
                time_data = [dt.datetime.strptime(x, TIME_FORMAT) for x in lat_time_dtec[0]]
                lat_data = list(map(float, lat_time_dtec[1]))
                dtec_data = list(map(float, lat_time_dtec[2]))
                self.lat_time_dtec = list(zip(time_data, lat_data, dtec_data))
        else:
            self.lat_time_dtec = []
            current_lon = longitude.get_float_degs()
            lon_span = self.coord_values['lon_span'].get_float_degs()
            with open(lat_time_file_name, mode='w') as lat_time_file:
                for line in self.data:
                    data = list(map(float, line.split()))
                    g_data = dict(zip(self.data_title, data))
                    if all((g_data['gdlon'] >= current_lon - lon_span / 2,
                            g_data['gdlon'] <= current_lon + lon_span / 2)):
                        c_time = dt.datetime.combine(current_date, dt.time(int(g_data['hour']),
                                                                           int(g_data['min']),
                                                                           int(g_data['sec'])))
                        current_time = c_time.strftime(TIME_FORMAT)
                        lat_time_dtec_data = (c_time, g_data['gdlat'], g_data['dTEC'])
                        self.lat_time_dtec.append(lat_time_dtec_data)
                        lat_time_file.write(f"{current_time}\t{g_data['gdlat']}\t{g_data['dTEC']}\n")


if __name__ == '__main__':
    _, cmd_archive_name, cmd_parsed_dir, cmd_filter_sec = argv
    archive = GnssArchive(cmd_archive_name)
    archive.parse_gnss_archive(cmd_parsed_dir, int(cmd_filter_sec))
