from zipfile import Path
from sys import argv
from os.path import isfile


def get_root_dir(in_archive):
    return in_archive.split('/')[-1].split('.')[0]


def get_receiver_list(in_archive):
    rec_names = []
    rec_lat = []
    rec_lon = []
    root_dir = get_root_dir(in_archive)
    at_file = f"{root_dir}/Sites.txt"
    rec_file_name = Path(in_archive, at_file)
    if rec_file_name.exists():
        with rec_file_name.open(mode='r') as rec_file:
            _ = rec_file.readline()
            for line in rec_file:
                data = line.split()
                rec_names.append(data[0])
                rec_lat.append(float(data[1]))
                rec_lon.append(float(data[2]))
    return rec_names, rec_lon, rec_lat


def get_in_file_name(in_archive, filter_dir):
    root_dir = get_root_dir(in_archive)
    prefix = root_dir[4:]
    suffix = ''
    if filter_dir == 'Window_3600_Seconds':
        suffix = '3600'
    if filter_dir == 'Window_7200_Seconds':
        suffix = '7200'
    return f"{prefix}_{suffix}"


def read_gnss_data(in_archive, out_dir, filter_dir, min_elm=30):
    root_dir = get_root_dir(in_archive)
    out_file_name = f"{out_dir}/{get_in_file_name(in_archive, filter_dir)}.txt"
    rec_num_file = f"{out_dir}/{get_in_file_name(in_archive, filter_dir)}.num"
    if not isfile(rec_num_file):
        with open(rec_num_file, mode='w') as num_file:
            num_file.write('0')
    rec_paths = Path(in_archive, f'{root_dir}/')
    rec_dirs = [rec_dir.name for rec_dir in rec_paths.iterdir() if rec_dir.is_dir()]
    rec_dirs.sort()
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
            for i in range(1, 33):
                at_file = f"{root_dir}/{rec_dir}/{filter_dir}/G{str(i).zfill(2)}.txt"
                g_file = Path(in_archive, at_file)
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


if __name__ == '__main__':
    _, in_archive, out_dir, filter_dir = argv
    read_gnss_data(in_archive, out_dir, filter_dir)
