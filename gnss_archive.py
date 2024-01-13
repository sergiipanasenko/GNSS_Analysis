from zipfile import Path
from sys import argv


def get_root_dir(in_archive):
    return in_archive.split('/')[-1].split('.')[0]


def get_in_file_name(in_archive, filter_dir):
    root_dir = get_root_dir(in_archive)
    prefix = root_dir[4:]
    suffix = ''
    if filter_dir == 'Window_3600_Seconds':
        suffix = '3600'
    if filter_dir == 'Window_7200_Seconds':
        suffix = '7200'
    return f"{prefix}_{suffix}.txt"


def read_gnss_data(in_archive, out_dir, filter_dir, min_elm=30):
    root_dir = get_root_dir(in_archive)
    out_file_name = f"{out_dir}/{get_in_file_name(in_archive, filter_dir)}"
    out_file = open(out_file_name, "w")
    rec_paths = Path(in_archive, f'{root_dir}/')
    rec_dirs = [rec_dir.name for rec_dir in rec_paths.iterdir()]
    rec_dirs.sort()
    rec_count = len(rec_dirs)
    for rec_dir in rec_dirs:
        rec_num = rec_dirs.index(rec_dir) + 1
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
                out_file.writelines(lines)
                out_file.flush()
    out_file.close()
    print("Reading is completed.")


if __name__ == '__main__':
    _, in_archive, out_dir, filter_dir = argv
    read_gnss_data(in_archive, out_dir, filter_dir)
