from PyQt5.QtWidgets import QMainWindow, QFileDialog, QSizePolicy

from ui.cartopy_figure import MapLAEA, DEFAULT_LABEL_PARAMS, DEFAULT_GRID_PARAMS
from ui.main_window import Ui_MainWindow
import cartopy.crs as ccrs

from zipfile import Path
from matplotlib.patches import Rectangle
from matplotlib import colormaps
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

from ui.qt_utils import MplWidget, MplCanvas


class DTECViewerForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        # parent initialisation
        super().__init__()

        # ui loading
        self.setupUi(self)
        self.time_axes = self.time_widget.canvas.figure.gca()
        self.space_axes = self.space_widget.canvas.figure.axes[0]
        self.space_cbar_axes = self.space_widget.canvas.figure.axes[1]
        self.space_color_bar = self.space_widget.geo_map.color_bar
        self.receiver_axes = self.receiver_widget.canvas.figure.axes[0]
        self.receiver_widget.addAction(self.actionOpen_receiver_list)

        # settings
        time_x_lim = (0, 24)
        time_y_lim = (-1, 1)
        self.time_axes.set_xlim(time_x_lim)
        self.time_axes.set_ylim(time_y_lim)
        self.lineEdit_6.setText(str(time_x_lim[0]))
        self.lineEdit_5.setText(str(time_x_lim[1]))
        self.lineEdit_8.setText(str(time_y_lim[0]))
        self.lineEdit_7.setText(str(time_y_lim[1]))

        space_lim = self.space_widget.geo_map.coords
        self.lineEdit_4.setText(str(round(space_lim['min_lon'], 3)))
        self.lineEdit_3.setText(str(round(space_lim['max_lon'], 3)))
        self.lineEdit.setText(str(round(space_lim['min_lat'], 3)))
        self.lineEdit_2.setText(str(round(space_lim['max_lat'], 3)))

        self.lineEdit_9.setText(str(0.01))
        self.lineEdit_10.setText(str(12))
        self.lineEdit_11.setText(str(0.8))
        self.lineEdit_12.setText(str(46.777778))
        self.lineEdit_14.setText(str(0.8))
        self.lineEdit_13.setText(str(33.370278))

        self.rec_file = None
        self.gnss_archive = None
        self.filter_dir = 'Window_3600_Seconds'
        self.min_elm = 30
        self.gnss_data = None
        self.gnss_data_title = None

        # connections
        self.pushButton.clicked.connect(self.update_coords)
        self.pushButton_2.clicked.connect(self.update_time_value)
        self.pushButton_3.clicked.connect(self.parse_data)
        self.actionOpen_receiver_list.triggered.connect(self.choose_receiver_file)
        self.actionOpen.triggered.connect(self.choose_gnss_data_archive)

    def update_coords(self):
        min_lat = float(self.lineEdit.text())
        max_lat = float(self.lineEdit_2.text())
        min_lon = float(self.lineEdit_4.text())
        max_lon = float(self.lineEdit_3.text())
        coords = {'min_lat': min_lat, 'max_lat': max_lat,
                  'min_lon': min_lon, 'max_lon': max_lon,
                  'central_long': (min_lon + max_lon) / 2,
                  'central_lat': (min_lat + max_lat) / 2}
        self.space_widget.geo_map.coords = coords
        s_width, s_height = self.space_widget.canvas.figure.get_size_inches()
        self.space_widget.geo_map = MapLAEA(coords=coords, is_cbar=True)
        self.space_widget.canvas.figure = (self.space_widget.geo_map.create_figure())
        self.space_widget.canvas.figure.set_size_inches(s_width, s_height)
        self.space_widget.canvas.draw()
        r_label_params = DEFAULT_LABEL_PARAMS | {'frame_on': False}
        r_grid_params = DEFAULT_GRID_PARAMS | {'draw_labels': False}
        self.receiver_widget.geo_map = MapLAEA(coords=coords,
                                               label_params=r_label_params,
                                               grid_params=r_grid_params)
        r_width, r_height = self.receiver_widget.canvas.figure.get_size_inches()
        self.receiver_widget.canvas.figure = self.receiver_widget.geo_map.create_figure()
        self.receiver_widget.canvas.figure.set_size_inches(r_width, r_height)
        self.receiver_widget.canvas.draw()
        self.space_axes = self.space_widget.canvas.figure.axes[0]
        self.space_cbar_axes = self.space_widget.canvas.figure.axes[1]
        self.receiver_axes = self.receiver_widget.canvas.figure.axes[0]
        self.__plot_receivers()

    def update_time_value(self):
        min_time = float(self.lineEdit_6.text())
        max_time = float(self.lineEdit_5.text())
        min_value = float(self.lineEdit_8.text())
        max_value = float(self.lineEdit_7.text())
        self.time_axes.set_xlim(min_time, max_time)
        self.time_axes.set_ylim(min_value, max_value)
        self.time_widget.canvas.draw()

    def choose_receiver_file(self):
        file_name = QFileDialog.getOpenFileName(
            caption="Open receiver list file",
            filter="All files (*);;Text files (*.dat *.txt)",
            initialFilter="Text files (*.dat *.txt)",
            directory='d:/Surnames/Skipa/')
        if file_name[0]:
            self.rec_file = file_name[0]
            self.__plot_receivers()

    def __plot_receivers(self):
        if self.rec_file:
            rec_names = []
            rec_lat = []
            rec_lon = []
            with open(self.rec_file) as receiver_file:
                _ = receiver_file.readline()
                for line in receiver_file:
                    data = line.split()
                    rec_names.append(data[0])
                    rec_lat.append(float(data[1]))
                    rec_lon.append(float(data[2]))
            self.receiver_axes.scatter(rec_lon, rec_lat, c='blue', s=10, marker='o',
                                       transform=ccrs.PlateCarree())
            self.receiver_widget.canvas.draw()

    def choose_gnss_data_archive(self):
        file_name = QFileDialog.getOpenFileName(
            caption="Open GNSS data archive",
            filter="Archive files (*.zip)",
            initialFilter="Archive files (*.zip)",
            directory='d:/Surnames/Skipa/')
        if file_name[0]:
            self.gnss_archive = file_name[0]

    def read_gnss_data(self):
        self.gnss_data = []
        root_dir = self.gnss_archive.split('/')[-1].split('.')[0]
        rec_paths = Path(self.gnss_archive, f'{root_dir}/')
        rec_dirs = (rec_dir.name for rec_dir in rec_paths.iterdir())
        for rec_dir in rec_dirs:
            for i in range(1, 33):
                at_file = f"{root_dir}/{rec_dir}/{self.filter_dir}/G{str(i).zfill(2)}.txt"
                g_file = Path(self.gnss_archive, at_file)
                if g_file.exists():
                    with g_file.open(mode='r') as txt:
                        self.gnss_data_title = txt.readline().split()
                        lines_raw = txt.readlines()
                    lines = list(filter(lambda x:
                                        float(x.split()[self.gnss_data_title.index('elm')]) > self.min_elm,
                                        lines_raw))
                    self.gnss_data.extend(lines)
        print("Reading is completed.")

    def save_timestamp_data(self, timestamp, timespan):
        if self.gnss_data is None:
            self.read_gnss_data()
        root_dir = self.gnss_archive.split('/')[-1].split('.')[0]
        day_num = root_dir[:3]
        save_time = str(timestamp).replace('.', 'p')
        out_data_file = \
            f'd:/Surnames/Skipa/June5-8_2023/{day_num}/1/Time/{save_time}.txt'
        out_fig_file = \
            f'd:/Surnames/Skipa/June5-8_2023/{day_num}/1/Time/Figures/{save_time}.png'
        with (open(out_data_file, mode='w') as data_file):
            for line in self.gnss_data:
                data = list(map(float, line.split()))
                g_data = dict(zip(self.gnss_data_title, data))
                time = g_data['hour'] + g_data['min'] / 60 + g_data['sec'] / 3600
                time_cond = (time >= timestamp - timespan / 2) and (time <= timestamp + timespan / 2)
                if time_cond:
                    out_str = f"{g_data['gdlon']}\t{g_data['gdlat']}\t{g_data['elm']}\t{g_data['dTEC']}\n"
                    data_file.write(out_str)
        self.update_coords()
        with (open(out_data_file, mode='r') as data_file):
            data = list(zip(*[line.split() for line in data_file]))
            lon_data = list(map(float, data[0]))
            lat_data = list(map(float, data[1]))
            dtec = list(map(float, data[3]))
            lat_span = float(self.lineEdit_11.text())
            lon_span = float(self.lineEdit_14.text())
            norm = Normalize(vmin=-0.2, vmax=0.2)
            c = self.space_color_bar.cmap(norm(dtec))
            for i in range(len(lat_data)):
                lon_coord = lon_data[i] - lon_span / 2
                lat_coord = lat_data[i] - lat_span / 2
                self.space_axes.add_patch(Rectangle(xy=(lon_coord, lat_coord),
                                                    width=lon_span, height=lat_span,
                                                    edgecolor='none',
                                                    facecolor=c[i],
                                                    transform=ccrs.PlateCarree()))
        self.space_widget.canvas.draw()
        self.space_widget.canvas.figure.savefig(dpi=200, fname=out_fig_file)

    def save_coords_stamp_data(self, coords_stamp, coords_span):
        if self.gnss_data is None:
            self.read_gnss_data()
        root_dir = self.gnss_archive.split('/')[-1].split('.')[0]
        day_num = root_dir[:3]
        current_lon = coords_stamp['lon']
        current_lat = coords_stamp['lat']
        lon_span = coords_span['lon']
        lat_span = coords_span['lat']
        lon_str = str(current_lon).replace('.', 'p')
        lat_str = str(current_lat).replace('.', 'p')
        save_coords = f"{lon_str}lon_{lat_str}lat"
        out_data_file = \
            f'd:/Surnames/Skipa/June5-8_2023/{day_num}/1/Coords/{save_coords}.txt'
        with (open(out_data_file, mode='w') as data_file):
            for line in self.gnss_data:
                data = list(map(float, line.split()))
                g_data = dict(zip(self.gnss_data_title, data))
                if all((g_data['gdlat'] >= current_lat - lat_span / 2,
                        g_data['gdlat'] <= current_lat + lat_span / 2,
                        g_data['gdlon'] >= current_lon - lon_span / 2,
                        g_data['gdlon'] <= current_lon + lon_span / 2)):
                    time = g_data['hour'] + g_data['min'] / 60 + g_data['sec'] / 3600
                    out_str = f"{time}\t{g_data['dTEC']}\n"
                    data_file.write(out_str)

        with (open(out_data_file, mode='r') as data_file):
            data = list(zip(*[line.split() for line in data_file]))
            time = list(map(float, data[0]))
            dtec = list(map(float, data[1]))
        self.time_axes.clear()
        self.time_axes.scatter(time, dtec, s=0.8, color='blue')
        self.time_widget.canvas.draw()

    def parse_data(self):
        if self.gnss_archive:
            current_lat = float(self.lineEdit_12.text())
            current_lon = float(self.lineEdit_13.text())
            lat_span = float(self.lineEdit_11.text())
            lon_span = float(self.lineEdit_14.text())
            current_time = float(self.lineEdit_10.text())
            time_span = float(self.lineEdit_9.text())
            self.save_timestamp_data(current_time, time_span)
            coords_stamp = {'lon': current_lon, 'lat': current_lat}
            coords_span = {'lon': lon_span, 'lat': lat_span}
            self.save_coords_stamp_data(coords_stamp, coords_span)
            print("Parsing is completed.")