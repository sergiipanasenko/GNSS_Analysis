from PyQt5.QtWidgets import QMainWindow, QFileDialog

from gnss import GnssArchive
from ui.cartopy_figure import GeoAxesMap, DEFAULT_LABEL_PARAMS, DEFAULT_GRID_PARAMS
from ui.main_window import Ui_MainWindow
import cartopy.crs as ccrs

from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

from math import ceil, cos, radians
import time


class DTECViewerForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        # parent initialisation
        super().__init__()

        # ui loading
        self.setupUi(self)
        self.time_axes = self.time_widget.canvas.figure.gca()
        self.space_axes = self.space_widget.canvas.figure.axes[0]
        self.space_cbar_axes = self.space_widget.canvas.figure.axes[1]
        self.space_color_bar = self.space_widget.axes_map.color_bar
        self.receiver_axes = self.receiver_widget.canvas.figure.axes[0]

        # settings
        time_x_lim = (0, 24)
        time_y_lim = (-1, 1)
        self.time_axes.set_xlim(time_x_lim)
        self.time_axes.set_ylim(time_y_lim)
        self.lineEdit_6.setText(str(time_x_lim[0]))
        self.lineEdit_5.setText(str(time_x_lim[1]))
        self.lineEdit_8.setText(str(time_y_lim[0]))
        self.lineEdit_7.setText(str(time_y_lim[1]))

        space_lim = self.space_widget.axes_map.coords
        self.lineEdit_4.setText(str(round(space_lim['min_lon'], 3)))
        self.lineEdit_3.setText(str(round(space_lim['max_lon'], 3)))
        self.lineEdit.setText(str(round(space_lim['min_lat'], 3)))
        self.lineEdit_2.setText(str(round(space_lim['max_lat'], 3)))

        self.lineEdit_9.setText(str(0.01))
        self.lineEdit_10.setText(str(12))
        self.lineEdit_11.setText(str(0.75))
        self.lineEdit_12.setText(str(46.777778))
        self.lineEdit_14.setText(str(0.75))
        self.lineEdit_13.setText(str(33.370278))

        self.gnss_archive = None
        self.filter_sec = 7200
        self.in_dir = 'results/in'
        self.out_dir = 'results/out'
        self.min_elm = 30
        self.dtec_limits = [-0.5, 0.5]
        self.gnss_data_title = ['hour', 'min', 'sec', 'dTEC', 'azm', 'elm', 'gdlat', 'gdlon']

        # connections
        self.pushButton.clicked.connect(self.update_coords)
        self.pushButton_2.clicked.connect(self.update_time_value)
        self.pushButton_3.clicked.connect(self.parse_data)
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
        self.space_widget.axes_map.coords = coords
        s_width, s_height = self.space_widget.canvas.figure.get_size_inches()
        self.space_widget.axes_map = GeoAxesMap(coords=coords, is_cbar=True)
        self.space_widget.canvas.figure = self.space_widget.axes_map.create_figure()
        self.space_color_bar = self.space_widget.axes_map.color_bar
        self.space_widget.canvas.figure.set_size_inches(s_width, s_height)
        self.space_widget.canvas.draw()
        r_label_params = DEFAULT_LABEL_PARAMS | {'frame_on': False}
        r_grid_params = DEFAULT_GRID_PARAMS | {'draw_labels': False}
        self.receiver_widget.axes_map = GeoAxesMap(coords=coords,
                                                   label_params=r_label_params,
                                                   grid_params=r_grid_params)
        r_width, r_height = self.receiver_widget.canvas.figure.get_size_inches()
        self.receiver_widget.canvas.figure = self.receiver_widget.axes_map.create_figure()
        self.receiver_widget.canvas.figure.set_size_inches(r_width, r_height)
        self.receiver_widget.canvas.draw()
        self.space_axes = self.space_widget.canvas.figure.axes[0]
        self.space_cbar_axes = self.space_widget.canvas.figure.axes[1]
        self.receiver_axes = self.receiver_widget.canvas.figure.axes[0]
        self.plot_receivers()

    def update_time_value(self):
        min_time = float(self.lineEdit_6.text())
        max_time = float(self.lineEdit_5.text())
        min_value = float(self.lineEdit_8.text())
        max_value = float(self.lineEdit_7.text())
        self.time_axes.set_xlim(min_time, max_time)
        self.time_axes.set_ylim(min_value, max_value)
        self.time_widget.canvas.draw()

    def plot_receivers(self):
        _, rec_lon, rec_lat = self.gnss_archive.get_receiver_coords()
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
            self.gnss_archive = GnssArchive(file_name[0])
            self.plot_receivers()

    def save_timestamp_data(self, timestamp, timespan):
        # self.gnss_archive.parse_gnss_archive(self.in_dir, self.filter_sec)
        # self.gnss_archive.read_gnss_data()
        cmap = self.space_color_bar.cmap
        root_dir = self.gnss_archive.root_dir
        day_num = self.gnss_archive.day_number
        year = self.gnss_archive.year
        save_time = str(timestamp).replace('.', 'p')
        save_span = str(timespan).replace('.', 'p')
        out_data_dir = f'{self.out_dir}/{year}/{day_num}/1/Time'
        out_data_file = f'{out_data_dir}/{save_time}_{save_span}.txt'
        out_fig_file = f'{out_data_dir}/Figures/{save_time}_{save_span}.png'
        with (open(out_data_file, mode='w') as data_file):
            for line in self.gnss_archive.gnss_data:
                data = list(map(float, line.split()))
                g_data = dict(zip(self.gnss_data_title, data))
                c_time = g_data['hour'] + g_data['min'] / 60 + g_data['sec'] / 3600
                time_cond = (c_time >= timestamp - timespan / 2) and (c_time <= timestamp + timespan / 2)
                if time_cond:
                    out_str = f"{g_data['gdlon']}\t{g_data['gdlat']}\t{g_data['elm']}\t{g_data['dTEC']}\n"
                    data_file.write(out_str)
        self.update_coords()
        with (open(out_data_file, mode='r') as data_file):
            data = [list(map(float, line.split())) for line in data_file]
            min_lat = float(self.lineEdit.text())
            max_lat = float(self.lineEdit_2.text())
            min_lon = float(self.lineEdit_4.text())
            max_lon = float(self.lineEdit_3.text())
            lat_span = float(self.lineEdit_11.text())
            lon_span = float(self.lineEdit_14.text())
            n_lat = ceil((max_lat - min_lat) / lat_span)
            plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
            vmin, vmax = self.dtec_limits
            norm = Normalize(vmin=vmin, vmax=vmax)
            self.space_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
            for lat in plot_lat:
                lat_data = list(filter(lambda x: abs(x[1] - lat) <= lat_span / 2, data))
                if lat_data:
                    corr_lon_span = lon_span / cos(radians(lat))
                    n_lon = ceil((max_lon - min_lon) / corr_lon_span)
                    plot_lon = [min_lon + corr_lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
                    for lon in plot_lon:
                        lat_lon_data = list(filter(lambda x: abs(x[0] - lon) <= corr_lon_span / 2, lat_data))
                        if lat_lon_data:
                            lat_lon_dtec = list(zip(*lat_lon_data))[3]
                            dtec_value = sum(lat_lon_dtec) / len(lat_lon_dtec)
                            c = self.space_color_bar.cmap(norm(dtec_value))
                            self.space_axes.add_patch(Rectangle(xy=(lon - corr_lon_span / 2, lat - lat_span / 2),
                                                                width=corr_lon_span, height=lat_span,
                                                                edgecolor='none',
                                                                facecolor=c,
                                                                transform=ccrs.PlateCarree()))

        current_date = self.gnss_archive.date
        current_time = time.strftime("%H:%M:%S", time.gmtime(timestamp * 3600))
        title = f"{current_date}    {current_time}"
        current_lat = float(self.lineEdit_12.text())
        current_lon = float(self.lineEdit_13.text())
        self.space_axes.scatter(current_lon, current_lat, marker='d', s=40, color='black',
                                transform=ccrs.PlateCarree())
        self.space_axes.annotate(text='Kakhovka Dam', xy=[current_lon + 0.1, current_lat + 0.1],
                                 transform=ccrs.PlateCarree())
        self.space_widget.canvas.figure.suptitle(title)
        self.space_widget.canvas.draw()
        self.space_widget.canvas.figure.savefig(dpi=200, fname=out_fig_file)

    def save_coords_stamp_data(self, coords_stamp, coords_span):
        self.read_in_data()
        root_dir = self.gnss_archive.split('/')[-1].split('.')[0]
        day_num = root_dir[:3]
        year = root_dir[4:8]
        current_lon = coords_stamp['lon']
        current_lat = coords_stamp['lat']
        lon_span = coords_span['lon']
        lat_span = coords_span['lat']
        lon_str = str(current_lon).replace('.', 'p')
        lat_str = str(current_lat).replace('.', 'p')
        lon_span_str = str(lon_span).replace('.', 'p')
        lat_span_str = str(lat_span).replace('.', 'p')
        save_coords = f"{lon_str}_{lon_span_str}lon_{lat_str}_{lat_span_str}lat"
        out_data_dir = f'{self.out_dir}/{year}/{day_num}/1/Coords'
        out_data_file = f'{out_data_dir}/{save_coords}.txt'
        with (open(out_data_file, mode='w') as data_file):
            for line in self.gnss_data:
                data = list(map(float, line.split()))
                g_data = dict(zip(self.gnss_data_title, data))
                if all((g_data['gdlat'] >= current_lat - lat_span / 2,
                        g_data['gdlat'] <= current_lat + lat_span / 2,
                        g_data['gdlon'] >= current_lon - lon_span / 2,
                        g_data['gdlon'] <= current_lon + lon_span / 2)):
                    c_time = g_data['hour'] + g_data['min'] / 60 + g_data['sec'] / 3600
                    out_str = f"{c_time}\t{g_data['dTEC']}\n"
                    data_file.write(out_str)
        with (open(out_data_file, mode='r') as data_file):
            data = [list(map(float, line.split())) for line in data_file]
            time_value = []
            dtec_value = []
            min_time = float(self.lineEdit_6.text())
            max_time = float(self.lineEdit_5.text())
            time_span = 1 / 120
            n_time = ceil((max_time - min_time) / time_span)
            plot_time = [min_time + j * time_span for j in range(n_time)]
            for c_time in plot_time:
                time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2, data))
                if time_data:
                    time_dtec = list(zip(*time_data))[1]
                    dtec_value.append(sum(time_dtec) / len(time_dtec))
                    time_value.append(c_time)
        self.update_time_value()
        self.time_axes.scatter(time_value, dtec_value, s=0.8, color='blue')
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
