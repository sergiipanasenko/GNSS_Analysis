from zipfile import Path
from sys import argv
import os


class GnssArchive:
    def __init__(self, archive_name: str):
        self.filter_dirs = {3600: 'Window_3600_Seconds',
                            7200: 'Window_7200_Seconds'}
        self.archive_name = archive_name
        self.root_dir = self.__get_root_dir()
        self.day_number = self.__get_day_number()
        self.year = self.__get_year()
        self.date = self.__get_date()

    def __get_root_dir(self):
        return self.archive_name.split('/')[-1].split('.')[0]

    def __get_day_number(self):
        return self.root_dir[:3]

    def __get_year(self):
        return self.root_dir[4:8]

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


class GnssData:
    def __init__(self):
        self.add_dir = None
        self.coord_values = {"lon": 0, "lon_span": 0, "lat": 0, "lat_span": 0}
        self.time_values = {'time': 0, "time_span": 0}
        self.data_title = ['hour', 'min', 'sec', 'dTEC', 'azm', 'elm', 'gdlat', 'gdlon']
        self.data = []
        self.time_dtec = []
        self.lon_lat_dtec = []

    @staticmethod
    def get_str_value(value):
        return str(value).replace('.', 'p')

    def get_time_dtec_file_stem(self, out_dir):
        dir_name = f"{out_dir}/{self.add_dir}/Coords/1"
        os.makedirs(dir_name, exist_ok=True)
        file_name = (f"{self.get_str_value(self.coord_values['lon'])}_"
                     f"{self.get_str_value(self.coord_values['lon_span'])}lon_"
                     f"{self.get_str_value(self.coord_values['lat'])}_"
                     f"{self.get_str_value(self.coord_values['lat_span'])}lat")
        return f"{dir_name}/{file_name}"

    def get_lon_lat_dtec_file_stem(self, out_dir):
        dir_name = f"{out_dir}/{self.add_dir}/Time/1"
        os.makedirs(dir_name, exist_ok=True)
        file_name = (f"{self.get_str_value(self.time_values['time'])}_"
                     f"{self.get_str_value(self.time_values['time_span'])}")
        return f"{dir_name}/{file_name}"

    def read_gnss_data(self, file_name):
        self.add_dir = '/'.join(file_name.split('/')[-4:-1])
        if not self.data:
            with open(file_name, mode='r') as in_file:
                self.data = in_file.readlines()

    def get_time_dtec(self, out_dir):
        time_file_name = f"{self.get_time_dtec_file_stem(out_dir)}.txt"
        if os.path.isfile(time_file_name):
            with open(time_file_name, mode='r') as time_file:
                self.time_dtec = [list(map(float, line.split())) for line in time_file]
        else:
            self.time_dtec = []
            with open(time_file_name, mode='w') as time_file:
                for line in self.data:
                    data = list(map(float, line.split()))
                    g_data = dict(zip(self.data_title, data))
                    if all((g_data['gdlat'] >= self.coord_values['lat'] - self.coord_values['lat_span'] / 2,
                            g_data['gdlat'] <= self.coord_values['lat'] + self.coord_values['lat_span'] / 2,
                            g_data['gdlon'] >= self.coord_values['lon'] - self.coord_values['lon_span'] / 2,
                            g_data['gdlon'] <= self.coord_values['lon'] + self.coord_values['lon_span'] / 2)):
                        c_time = g_data['hour'] + g_data['min'] / 60 + g_data['sec'] / 3600
                        time_dtec_data = [c_time, g_data['dTEC']]
                        self.time_dtec.append(time_dtec_data)
                        time_file.write(f"{c_time}\t{g_data['dTEC']}\n")

    def get_lon_lat_dtec(self, out_dir):
        coord_file_name = f"{self.get_lon_lat_dtec_file_stem(out_dir)}.txt"
        if os.path.isfile(coord_file_name):
            with open(coord_file_name, mode='r') as coord_file:
                self.lon_lat_dtec = [list(map(float, line.split())) for line in coord_file]
        else:
            self.lon_lat_dtec = []
            with open(coord_file_name, mode='w') as coord_file:
                for line in self.data:
                    data = list(map(float, line.split()))
                    g_data = dict(zip(self.data_title, data))
                    c_time = g_data['hour'] + g_data['min'] / 60 + g_data['sec'] / 3600
                    time_cond = ((c_time >= self.time_values['time'] - self.time_values['time_span'] / 2) and
                                 (c_time <= self.time_values['time'] + self.time_values['time_span'] / 2))
                    if time_cond:
                        lon_lat_dtec_data = [g_data['gdlon'], g_data['gdlat'], g_data['dTEC']]
                        self.lon_lat_dtec.append(lon_lat_dtec_data)
                        coord_file.write(f"{g_data['gdlon']}\t{g_data['gdlat']}\t{g_data['dTEC']}\n")


if __name__ == '__main__':
    _, cmd_archive_name, cmd_parsed_dir, cmd_filter_sec = argv
    archive = GnssArchive(cmd_archive_name)
    archive.parse_gnss_archive(cmd_parsed_dir, int(cmd_filter_sec))
