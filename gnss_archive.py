from zipfile import Path
from sys import argv
import os


filter_dirs = {3600: 'Window_3600_Seconds', 7200: 'Window_3600_Seconds'}


class GnssArchive:
    def __init__(self, archive_name: str, in_dir: str, out_dir: str, filter_sec: int):
        self.filter_dir = filter_dirs.get(filter_sec)
        if not self.filter_dir:
            raise ValueError("Wrong value of filter window. Must be 3600 or 7200")
        self.archive_name = archive_name
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.filter_sec = str(filter_sec)
        self.root_dir = self.__get_root_dir()
        self.day_number = self.__get_day_number()
        self.year = self.__get_year()
        self.date = self.__get_date()
        self.file_stem = self.__get_parsed_file_stem()
        self.gnss_data = []

    def __get_root_dir(self):
        return self.archive_name.split('/')[-1].split('.')[0]

    def __get_day_number(self):
        return self.root_dir[:3]

    def __get_year(self):
        return self.root_dir[4:8]

    def __get_date(self):
        return self.root_dir[4:]

    def __get_parsed_file_stem(self):
        prefix = self.date
        suffix = self.filter_sec
        dirs = f"{self.in_dir}/{self.year}/{prefix}/{suffix}"
        os.makedirs(dirs, exist_ok=True)
        return f"{dirs}/{prefix}_{suffix}"

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

    def parse_gnss_archive(self, min_elm=30):
        out_file_name = f"{self.file_stem}.txt"
        rec_num_file = f"{self.file_stem}.num"
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
                    at_file = f"{self.root_dir}/{rec_dir}/{self.filter_dir}/G{str(j).zfill(2)}.txt"
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

    def read_gnss_data(self):
        if not self.gnss_data:
            in_file_name = f"{self.file_stem}.txt"
            with open(in_file_name, mode='r') as in_file:
                self.gnss_data = in_file.readlines()


if __name__ == '__main__':
    _, cmd_archive_name, cmd_in_dir, cmd_out_dir, cmd_filter_sec = argv
    archive = GnssArchive(cmd_archive_name, cmd_in_dir,
                          cmd_out_dir, int(cmd_filter_sec))
    archive.parse_gnss_archive()
