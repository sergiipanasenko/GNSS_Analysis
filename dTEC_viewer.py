from PyQt5.QtCore import QDateTime, QDate, QTime
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from gnss import GnssArchive, GnssData
from ui.cartopy_figure import GeoAxesMap, GeoCoord, DEFAULT_MAP_PARAMS, DEFAULT_GRID_PARAMS, PROJECTIONS
from ui.main_window1 import Ui_MainWindow
import cartopy.crs as ccrs

from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

import math
import time
import os
from datetime import datetime


STAGES = ('Original', 'Without outliers', 'Interpolated', 'Bandpass filtered')


class DTECViewerForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        # parent initialisation
        super().__init__()

        # ui loading
        self.setupUi(self)
        self.time_axes = self.time_widget.canvas.figure.gca()
        self.map_axes = self.map_widget.canvas.figure.axes[0]
        self.map_cbar_axes = self.map_widget.canvas.figure.axes[1]
        self.map_color_bar = self.map_widget.axes_map.color_bar
        self.receiver_axes = self.receiver_widget.canvas.figure.axes[0]

        # centering
        qt_rect = self.frameGeometry()
        center_point = (QGuiApplication.primaryScreen().
                        availableGeometry().center())
        y_coord = center_point.y()
        center_point.setY(y_coord - 40)
        qt_rect.moveCenter(center_point)
        self.move(qt_rect.topLeft())

        # settings
        self.combo_region.setCurrentIndex(2)
        self.combo_projection.addItems(PROJECTIONS)
        self.combo_stage.addItems(STAGES)

        min_date_time = QDateTime()
        min_date_time.setDate(QDate.currentDate())
        min_date_time.setTime(QTime(0, 0, 0))
        max_date_time = min_date_time.addSecs(23 * 3600 + 59 * 60 + 59)
        current_date_time = QDateTime.currentDateTime()
        self.limit_map_dtec = {'min_dtec': -0.5, 'max_dtec': 0.5}
        self.limit_time = {'min_time': min_date_time, 'max_time': max_date_time,
                           'min_dtec': -1.0, 'max_dtec': 1.0}
        self.analyzed_coords = {"start_lon": GeoCoord(46, 46, 34),
                               'end_lon': GeoCoord(46, 46, 34),
                               'lon_span': GeoCoord(0, 45),
                               'start_lat': GeoCoord(33, 22, 18),
                               'end_lat': GeoCoord(33, 22, 18),
                               'lat_span': GeoCoord(0, 45)}
        self.analyzed_time = {'start_time': current_date_time,
                              'end_time': current_date_time,
                              'time_span': QTime(0, 0, 30)}
        float_min_timw = (min_date_time.time().hour() + min_date_time.time().minute() / 60. +
                          min_date_time.time().second() / 3600.)
        float_max_timw = (max_date_time.time().hour() + max_date_time.time().minute() / 60. +
                          max_date_time.time().second() / 3600.)
        self.time_axes.set_xlim((float_min_timw, float_max_timw))
        self.time_axes.set_ylim((self.limit_time['min_dtec'], self.limit_time['max_dtec']))
        self.dspin_yaxis_min.setValue(self.limit_time['min_dtec'])
        self.dspin_yaxis_max.setValue(self.limit_time['max_dtec'])
        self.dspin_lat_lon_min.setValue(self.limit_map_dtec['min_dtec'])
        self.dspin_lat_lon_max.setValue(self.limit_map_dtec['max_dtec'])
        self.dspin_lat_time_min.setValue(self.limit_map_dtec['min_dtec'])
        self.dspin_lat_time_max.setValue(self.limit_map_dtec['max_dtec'])
        self.dspin_lon_time_min.setValue(self.limit_map_dtec['min_dtec'])
        self.dspin_lon_time_max.setValue(self.limit_map_dtec['max_dtec'])

        self.dt_xaxis_min.setDateTime(self.limit_time['min_time'])
        self.dt_xaxis_max.setDateTime(self.limit_time['max_time'])

        map_lim = self.map_widget.axes_map.coords
        self.spin_minlon_degs.setValue(map_lim['min_lon'].degs)
        self.spin_maxlon_degs.setValue(map_lim['max_lon'].degs)
        self.spin_minlat_degs.setValue(map_lim['min_lat'].degs)
        self.spin_maxlat_degs.setValue(map_lim['max_lat'].degs)
        self.spin_centrlat_degs.setValue(map_lim['central_lat'].degs)
        self.spin_centrlon_degs.setValue(map_lim['central_long'].degs)
        self.spin_minlon_mins.setValue(map_lim['min_lon'].mins)
        self.spin_maxlon_mins.setValue(map_lim['max_lon'].mins)
        self.spin_minlat_mins.setValue(map_lim['min_lat'].mins)
        self.spin_maxlat_mins.setValue(map_lim['max_lat'].mins)
        self.spin_centrlat_mins.setValue(map_lim['central_lat'].mins)
        self.spin_centrlon_mins.setValue(map_lim['central_long'].mins)
        #
        self.spin_lat_start_degs.setValue(self.analyzed_coords['start_lat'].degs)
        self.spin_lat_start_mins.setValue(self.analyzed_coords['start_lat'].mins)
        self.spin_lat_end_degs.setValue(self.analyzed_coords['end_lat'].degs)
        self.spin_lat_end_mins.setValue(self.analyzed_coords['end_lat'].mins)
        self.spin_lon_start_degs.setValue(self.analyzed_coords['start_lon'].degs)
        self.spin_lon_start_mins.setValue(self.analyzed_coords['start_lon'].mins)
        self.spin_lon_end_degs.setValue(self.analyzed_coords['end_lon'].degs)
        self.spin_lon_end_mins.setValue(self.analyzed_coords['end_lon'].mins)
        self.dt_data_time_start.setDateTime(self.analyzed_time['start_time'])
        self.dt_data_time_end.setDateTime(self.analyzed_time['end_time'])
        self.t_data_time_span.setTime(self.analyzed_time['time_span'])
        self.spin_lat_span_degs.setValue(self.analyzed_coords['lat_span'].degs)
        self.spin_lat_span_mins.setValue(self.analyzed_coords['lat_span'].mins)
        self.spin_lon_span_degs.setValue(self.analyzed_coords['lon_span'].degs)
        self.spin_lon_span_mins.setValue(self.analyzed_coords['lon_span'].mins)

        self.gnss_archive = None
        self.gnss_data = GnssData()
        self.gnss_data.coord_values = self.analyzed_coords
        self.gnss_data.time_values = self.analyzed_time

        self.filter_sec = 7200
        self.in_dir = 'results/in/EU'
        self.out_dir = 'results/out/EU'
        self.min_elm = 30

        # connections
        self.push_update.clicked.connect(self.update_coords)
        self.actionOpen.triggered.connect(self.choose_gnss_data_archive)

    def update_data(self):
        pass

    def update_coords(self):
        self.combo_region.setCurrentIndex(0)
        min_lat = GeoCoord(self.spin_minlat_degs.value(), self.spin_minlat_mins.value())
        max_lat = GeoCoord(self.spin_maxlat_degs.value(), self.spin_maxlat_mins.value())
        min_lon = GeoCoord(self.spin_minlon_degs.value(), self.spin_minlon_mins.value())
        max_lon = GeoCoord(self.spin_maxlon_degs.value(), self.spin_maxlon_mins.value())
        centr_lat = GeoCoord(self.spin_centrlat_degs.value(), self.spin_centrlat_mins.value())
        centr_lon = GeoCoord(self.spin_centrlon_degs.value(), self.spin_centrlon_mins.value())
        coords = {'min_lat': min_lat, 'max_lat': max_lat,
                  'min_lon': min_lon, 'max_lon': max_lon,
                  'central_long': centr_lon,
                  'central_lat': centr_lat}
        self.map_widget.axes_map.coords = coords
        s_width, s_height = self.map_widget.canvas.figure.get_size_inches()
        self.map_widget.axes_map = GeoAxesMap(coords=coords, is_cbar=True)
        self.map_widget.axes_map.create_figure()
        self.map_widget.canvas.figure = self.map_widget.axes_map.figure
        self.map_color_bar = self.map_widget.axes_map.color_bar
        self.map_widget.canvas.figure.set_size_inches(s_width, s_height)
        self.map_widget.canvas.draw()
        r_label_params = DEFAULT_MAP_PARAMS | {'frame_on': False}
        r_grid_params = DEFAULT_GRID_PARAMS | {'draw_labels': False}
        self.receiver_widget.axes_map = GeoAxesMap(coords=coords,
                                                   label_params=r_label_params,
                                                   grid_params=r_grid_params)
        self.receiver_widget.axes_map.create_figure()
        r_width, r_height = self.receiver_widget.canvas.figure.get_size_inches()
        self.receiver_widget.canvas.figure = self.receiver_widget.axes_map.figure
        self.receiver_widget.canvas.figure.set_size_inches(r_width, r_height)
        self.receiver_widget.canvas.draw()
        self.map_axes = self.map_widget.canvas.figure.axes[0]
        self.map_cbar_axes = self.map_widget.canvas.figure.axes[1]
        self.receiver_axes = self.receiver_widget.canvas.figure.axes[0]
        self.plot_receivers()

    def update_time_value(self):
        self.limit_time['min_time'] = float(self.lineEdit_6.text())
        self.limit_time['max_time'] = float(self.lineEdit_5.text())
        self.limit_time['min_dtec'] = float(self.lineEdit_8.text())
        self.limit_time['max_dtec'] = float(self.lineEdit_7.text())
        self.time_axes.set_xlim(self.limit_time['min_time'], self.limit_time['max_time'])
        self.time_axes.set_ylim(self.limit_time['min_dtec'], self.limit_time['max_dtec'])
        x_labs = self.time_axes.get_xticklabels()
        x_labs[-1] = ''
        self.time_axes.set_xticklabels(x_labs)
        self.time_widget.canvas.draw()

    def plot_receivers(self):
        if self.gnss_archive:
            _, rec_lon, rec_lat = self.gnss_archive.get_receiver_coords()
            self.receiver_axes.scatter(rec_lon, rec_lat, c='blue', s=10, marker='o',
                                       transform=ccrs.PlateCarree())
            self.receiver_widget.canvas.draw()

    def choose_gnss_data_archive(self):
        file_name = QFileDialog.getOpenFileName(
            caption="Open GNSS data archive",
            filter="Archive files (*.zip)",
            initialFilter="Archive files (*.zip)",
            directory='C:/Users/Sergii/Dell_D/GNSS')
        if file_name[0]:
            self.gnss_archive = GnssArchive(file_name[0])
            self.plot_receivers()

    def read_data(self):
        if self.gnss_archive is None:
            raise FileNotFoundError("GNSS archive is not opened.")
        if not self.gnss_data.data:
            file_name = f"{self.gnss_archive.get_parsed_file_stem(self.in_dir, self.filter_sec)}.txt"
            if not os.path.isfile(file_name):
                raise FileNotFoundError(f"Parsed file f'{file_name}' is not exist.")
            self.gnss_data.read_gnss_data(file_name)

    def plot_timestamp_data(self):
        self.read_data()
        self.gnss_data.get_lon_lat_dtec(self.out_dir)
        self.update_coords()
        min_lat = float(self.lineEdit.text())
        max_lat = float(self.lineEdit_2.text())
        min_lon = float(self.lineEdit_4.text())
        max_lon = float(self.lineEdit_3.text())
        lat_span = float(self.lineEdit_11.text())
        lon_span = float(self.lineEdit_14.text())
        n_lat = math.ceil((max_lat - min_lat) / lat_span)
        plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
        cmap = self.space_color_bar.cmap
        v_min = self.limit_space_dtec['min_dtec']
        v_max = self.limit_space_dtec['max_dtec']
        norm = Normalize(vmin=v_min, vmax=v_max)
        self.space_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
        res_file_name = f"{self.gnss_data.get_lon_lat_dtec_file_stem(self.out_dir)}_av.txt"
        with open(res_file_name, mode='w') as res_file:
            for lat in plot_lat:
                lat_data = list(filter(lambda x: abs(x[1] - lat) <= lat_span / 2,
                                       self.gnss_data.lon_lat_dtec))
                if lat_data:
                    corr_lon_span = lon_span / math.cos(math.radians(lat))
                    n_lon = math.ceil((max_lon - min_lon) / corr_lon_span)
                    plot_lon = [min_lon + corr_lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
                    for lon in plot_lon:
                        lat_lon_data = list(filter(lambda x: abs(x[0] - lon) <= corr_lon_span / 2, lat_data))
                        if lat_lon_data:
                            lat_lon_dtec = list(zip(*lat_lon_data))[2]
                            dtec_value = sum(lat_lon_dtec) / len(lat_lon_dtec)
                            res_file.write(f"{lat}\t{lon}\t{dtec_value}\n")
                            c = self.space_color_bar.cmap(norm(dtec_value))
                            self.space_axes.add_patch(Rectangle(xy=(lon - corr_lon_span / 2, lat - lat_span / 2),
                                                                width=corr_lon_span, height=lat_span,
                                                                edgecolor='none',
                                                                facecolor=c,
                                                                transform=ccrs.PlateCarree()))
        current_date = self.gnss_archive.date
        current_time = time.strftime("%H:%M:%S",
                                     time.gmtime(self.gnss_data.time_values['time'] * 3600))
        title = f"{current_date}    {current_time} UT"
        # current_lat = float(self.lineEdit_12.text())
        # current_lon = float(self.lineEdit_13.text())
        # self.space_axes.scatter(current_lon, current_lat, marker='o', s=30, color='black',
        #                         transform=ccrs.PlateCarree())
        # self.space_axes.annotate(text='Kakhovka Dam', xy=[current_lon + 0.1, current_lat + 0.1],
        #                          transform=ccrs.PlateCarree())
        self.space_widget.canvas.figure.text(x=0.6, y=0.02, s=title,
                                             family='Times New Roman', size=16)
        self.space_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_lon_lat_dtec_file_stem(self.out_dir)}.png"
        if not os.path.isfile(fig_file_name):
            self.space_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def plot_coords_stamp_data(self):
        self.read_data()
        self.gnss_data.get_time_dtec(self.out_dir)
        self.update_time_value()
        time_value = []
        dtec_value = []
        min_time = self.limit_time['min_time']
        max_time = self.limit_time['max_time']
        time_span = 1 / 120
        n_time = math.ceil((max_time - min_time) / time_span)
        plot_time = [min_time + j * time_span for j in range(n_time)]
        res_file_name = f"{self.gnss_data.get_time_dtec_file_stem(self.out_dir)}_av.txt"
        for c_time in plot_time:
            time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2,
                                    self.gnss_data.time_dtec))
            if time_data:
                time_dtec = list(zip(*time_data))[1]
                c_dtec = sum(time_dtec) / len(time_dtec)
                dtec_value.append(c_dtec)
                time_value.append(c_time)
        with open(res_file_name, mode='w') as res_file:
            for line in list(zip(time_value, dtec_value)):
                res_file.write(f"{line[0]}\t{line[1]}\n")

        for graph in self.time_widget.axes_map.graphs:
            graph.remove()
            self.time_widget.axes_map.graphs.remove(graph)
        # self.time_axes.clear()
        graph = self.time_axes.scatter(time_value, dtec_value, s=0.8, color='blue')
        self.time_widget.axes_map.graphs.append(graph)
        # self.update_time_value()
        self.time_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_time_dtec_file_stem(self.out_dir)}.png"

        if not os.path.isfile(fig_file_name):
            self.time_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def update_figures(self):
        if self.gnss_archive:
            self.set_coords_time()
            self.plot_timestamp_data()
            self.plot_coords_stamp_data()
            print("Figure updating is completed.")
