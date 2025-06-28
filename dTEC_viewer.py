from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from gnss import GnssArchive, GnssData, convert_to_hours, TIME_FORMAT
from ui.cartopy_figure import GeoAxesMap, DEFAULT_MAP_PARAMS, DEFAULT_GRID_PARAMS, PROJECTIONS
from utils.geo.geo_coords import GeoCoord
from ui.main_window1 import Ui_MainWindow
import cartopy.crs as ccrs

from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib import colormaps

import math
import os
import datetime as dt

STAGES = ('Original', 'Without outliers', 'Interpolated', 'Bandpass filtered')

DEFAULT_CMAP = 'rainbow'
LIMIT_DTEC = 1


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
        self.keo_lat_axes = self.keo_lat_widget.canvas.figure.axes[0]
        self.keo_lat_cbar_axes = self.keo_lat_widget.canvas.figure.axes[1]
        self.keo_lat_color_bar = self.keo_lat_widget.axes_map.color_bar
        self.keo_lon_axes = self.keo_lon_widget.canvas.figure.axes[0]
        self.keo_lon_cbar_axes = self.keo_lon_widget.canvas.figure.axes[1]
        self.keo_lon_color_bar = self.keo_lon_widget.axes_map.color_bar
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
        self.combo_cmap.addItems(list(colormaps))
        self.combo_cmap.setCurrentIndex(self.combo_cmap.findText(DEFAULT_CMAP))
        self.combo_stage.addItems(STAGES)

        min_date_time = dt.datetime.combine(dt.date.today(), dt.time(0, 0, 0))
        max_date_time = min_date_time + dt.timedelta(hours=23, minutes=59, seconds=59)
        current_date_time = dt.datetime.now()
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
                              'time_span': dt.timedelta(seconds=60)}
        float_min_timw = convert_to_hours(min_date_time)
        float_max_timw = convert_to_hours(max_date_time)
        self.time_axes.set_xlim((float_min_timw, float_max_timw))
        self.time_axes.set_ylim((self.limit_time['min_dtec'], self.limit_time['max_dtec']))
        self.keo_lat_axes.set_xlim((float_min_timw, float_max_timw))
        self.keo_lon_axes.set_xlim((float_min_timw, float_max_timw))
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

        self.keo_lat_axes.set_ylim((map_lim['min_lat'].degs, map_lim['max_lat'].degs))
        self.keo_lon_axes.set_ylim((map_lim['min_lon'].degs, map_lim['max_lon'].degs))

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
        time_span = dt.time(0, 0, 30)
        self.t_data_time_span.setTime(time_span)
        self.spin_lat_span_degs.setValue(self.analyzed_coords['lat_span'].degs)
        self.spin_lat_span_mins.setValue(self.analyzed_coords['lat_span'].mins)
        self.spin_lon_span_degs.setValue(self.analyzed_coords['lon_span'].degs)
        self.spin_lon_span_mins.setValue(self.analyzed_coords['lon_span'].mins)

        self.gnss_archive = None
        self.gnss_data = GnssData()

        self.filter_sec = 7200
        self.in_dir = 'results/in/EU'
        self.out_dir = 'results/out/EU'
        self.min_elm = 30

        # connections
        self.push_update.clicked.connect(self.update_data)
        self.actionOpen.triggered.connect(self.choose_gnss_data_archive)

    def dtec_corr(self, val):
        if abs(val) < LIMIT_DTEC:
            return val
        else:
            return 0.0

    def update_data(self):
        if self.tabWidget_set.currentIndex() == 0:
            self.update_coords()
        elif self.tabWidget_set.currentIndex() == 1:
            self.update_time_value()
        elif self.tabWidget_set.currentIndex() == 2:
            self.plot_time_stamp_data()
            self.plot_coords_stamp_data()
            self.plot_lat_time_data()
            self.plot_lon_time_data()

    def update_coords(self):
        self.combo_region.setCurrentIndex(0)
        min_lat = GeoCoord(self.spin_minlat_degs.value(), self.spin_minlat_mins.value())
        max_lat = GeoCoord(self.spin_maxlat_degs.value(), self.spin_maxlat_mins.value())
        min_lon = GeoCoord(self.spin_minlon_degs.value(), self.spin_minlon_mins.value())
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
        self.limit_time['min_time'] = self.dt_xaxis_min.dateTime().toPyDateTime()
        self.limit_time['max_time'] = self.dt_xaxis_max.dateTime().toPyDateTime()
        self.limit_time['min_dtec'] = self.dspin_yaxis_min.value()
        self.limit_time['max_dtec'] = self.dspin_yaxis_max.value()
        min_time = convert_to_hours(self.limit_time['min_time'])
        max_time = convert_to_hours(self.limit_time['max_time'])
        self.time_axes.set_xlim(min_time, max_time)
        self.time_axes.set_ylim(self.limit_time['min_dtec'], self.limit_time['max_dtec'])
        # x_labs = self.time_axes.get_xticklabels()
        # x_labs[-1] = ''
        # self.time_axes.set_xticklabels(x_labs)
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
            current_year = int(self.gnss_archive.get_year())
            current_month = int(self.gnss_archive.get_month())
            current_day = int(self.gnss_archive.get_day())
            start_time = dt.datetime(current_year, current_month, current_day, 0, 0, 0)
            end_time = dt.datetime(current_year, current_month, current_day, 23, 59, 59)
            self.limit_time['min_time'] = start_time
            self.limit_time['max_time'] = end_time
            self.analyzed_time['start_time'] = start_time
            self.analyzed_time['end_time'] = end_time
            self.dt_xaxis_min.setDateTime(start_time)
            self.dt_xaxis_max.setDateTime(end_time)
            self.dt_data_time_start.setDateTime(start_time)
            self.dt_data_time_end.setDateTime(end_time)

    def read_data(self):
        if self.gnss_archive is None:
            raise FileNotFoundError("GNSS archive is not opened.")
        if not self.gnss_data.data:
            file_name = f"{self.gnss_archive.get_parsed_file_stem(self.in_dir, self.filter_sec)}.txt"
            if not os.path.isfile(file_name):
                raise FileNotFoundError(f"Parsed file f'{file_name}' is not exist.")
            self.gnss_data.read_gnss_data(file_name)

    def plot_time_stamp_data(self):
        time_values = dict()
        time_values['time'] = self.dt_data_time_start.dateTime().toPyDateTime()
        time_values['time_span'] = dt.timedelta(hours=self.t_data_time_span.time().hour(),
                                                minutes=self.t_data_time_span.time().minute(),
                                                seconds=self.t_data_time_span.time().second())
        self.gnss_data.time_values = time_values
        file_name = f"{self.gnss_archive.get_parsed_file_stem(self.in_dir, self.filter_sec)}.txt"
        self.gnss_data.add_dir = '/'.join(file_name.split('/')[-4:-1])
        self.update_coords()
        time_file_name = f"{self.gnss_data.get_lon_lat_dtec_file_stem(self.out_dir)}_av.txt"
        self.map_color_bar.cmap = colormaps[self.combo_cmap.currentText()]
        cmap = self.map_color_bar.cmap
        v_min = self.dspin_lat_lon_min.value()
        v_max = self.dspin_lat_lon_max.value()
        norm = Normalize(vmin=v_min, vmax=v_max)
        self.map_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
        self.analyzed_coords['lat_span'] = GeoCoord(self.spin_lat_span_degs.value(),
                                                    self.spin_lat_span_mins.value())
        lat_span = self.analyzed_coords['lat_span'].get_float_degs()
        self.analyzed_coords['lon_span'] = GeoCoord(self.spin_lon_span_degs.value(),
                                                    self.spin_lon_span_mins.value())
        lon_span = self.analyzed_coords['lon_span'].get_float_degs()
        if os.path.isfile(time_file_name):
            with open(time_file_name, mode='r') as res_file:
                raw_data = [line.split('\t') for line in res_file]
                for data in raw_data:
                    lon_value = float(data[0])
                    lat_value = float(data[1])
                    dtec_value = float(data[2])
                    corr_lon_span = lon_span / math.cos(math.radians(lat_value))
                    c = self.map_color_bar.cmap(norm(dtec_value))
                    self.map_axes.add_patch(Rectangle(xy=(lon_value - corr_lon_span / 2, lat_value - lat_span / 2),
                                                      width=corr_lon_span, height=lat_span,
                                                      edgecolor='none',
                                                      facecolor=c,
                                                      transform=ccrs.PlateCarree()))
        else:
            self.read_data()
            self.gnss_data.get_lon_lat_dtec(self.out_dir, time_values)
            coords = self.map_widget.axes_map.coords
            min_lat = coords['min_lat'].get_float_degs()
            max_lat = coords['max_lat'].get_float_degs()
            min_lon = coords['min_lon'].get_float_degs()
            max_lon = coords['max_lon'].get_float_degs()
            n_lat = math.ceil((max_lat - min_lat) / lat_span)
            plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
            with open(time_file_name, mode='w') as res_file:
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
                                lat_lon_dtec_raw = list(zip(*lat_lon_data))[2]
                                lat_lon_dtec = list(map(self.dtec_corr, lat_lon_dtec_raw))
                                dtec_value = sum(lat_lon_dtec) / len(lat_lon_dtec)
                                res_file.write(f"{lat}\t{lon}\t{dtec_value}\n")
                                c = self.map_color_bar.cmap(norm(dtec_value))
                                self.map_axes.add_patch(Rectangle(xy=(lon - corr_lon_span / 2, lat - lat_span / 2),
                                                                  width=corr_lon_span, height=lat_span,
                                                                  edgecolor='none',
                                                                  facecolor=c,
                                                                  transform=ccrs.PlateCarree()))
        current_time = self.gnss_data.time_values['time'].strftime("%Y-%m-%d   %H:%M:%S")
        title = f"{current_time} UT"
        # current_lat = float(self.lineEdit_12.text())
        # current_lon = float(self.lineEdit_13.text())
        # self.space_axes.scatter(current_lon, current_lat, marker='o', s=30, color='black',
        #                         transform=ccrs.PlateCarree())
        # self.space_axes.annotate(text='Kakhovka Dam', xy=[current_lon + 0.1, current_lat + 0.1],
        #                          transform=ccrs.PlateCarree())
        self.map_widget.canvas.figure.text(x=0.7, y=0.02, s=title,
                                           family='Times New Roman', size=16)
        self.map_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_lon_lat_dtec_file_stem(self.out_dir)}.png"
        # if not os.path.isfile(fig_file_name):
        self.map_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def plot_coords_stamp_data(self):
        coord_values = dict()
        coord_values['lon'] = GeoCoord(self.spin_lon_start_degs.value(),
                                       self.spin_lon_start_mins.value())
        coord_values['lon_span'] = GeoCoord(self.spin_lon_span_degs.value(),
                                            self.spin_lon_span_mins.value())
        coord_values['lat'] = GeoCoord(self.spin_lat_start_degs.value(),
                                       self.spin_lat_start_mins.value())
        coord_values['lat_span'] = GeoCoord(self.spin_lat_span_degs.value(),
                                            self.spin_lat_span_mins.value())
        self.gnss_data.coord_values = coord_values
        file_name = f"{self.gnss_archive.get_parsed_file_stem(self.in_dir, self.filter_sec)}.txt"
        self.gnss_data.add_dir = '/'.join(file_name.split('/')[-4:-1])
        coord_file_name = f"{self.gnss_data.get_time_dtec_file_stem(self.out_dir)}_av.txt"
        time_value = []
        dtec_value = []
        if os.path.isfile(coord_file_name):
            with open(coord_file_name, mode='r') as res_file:
                raw_data = [line.split('\t') for line in res_file]
                data = list(zip(*raw_data))
                time_value = [dt.datetime.strptime(x, TIME_FORMAT) for x in data[0]]
                dtec_value = list(map(float, data[1]))
        else:
            current_date = self.dt_data_time_start.dateTime().toPyDateTime().date()
            self.read_data()
            self.gnss_data.get_time_dtec(self.out_dir, coord_values, current_date)
            self.update_time_value()
            min_time = self.limit_time['min_time']
            max_time = self.limit_time['max_time']
            time_span = dt.timedelta(seconds=30)
            n_time = math.ceil((max_time - min_time) / time_span)
            plot_time = [min_time + j * time_span for j in range(n_time)]
            for c_time in plot_time:
                time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2,
                                        self.gnss_data.time_dtec))
                if time_data:
                    time_dtec_raw = list(zip(*time_data))[1]
                    time_dtec = list(map(self.dtec_corr, time_dtec_raw))
                    c_dtec = sum(time_dtec) / len(time_dtec)
                    dtec_value.append(c_dtec)
                    time_value.append(c_time)
            with open(coord_file_name, mode='w') as res_file:
                for line in list(zip(time_value, dtec_value)):
                    current_time_value = line[0].strftime('%Y.%m.%d %H:%M:%S')
                    current_dtec_value = line[1]
                    res_file.write(f"{current_time_value}\t{current_dtec_value}\n")
        for graph in self.time_widget.axes_map.graphs:
            graph.remove()
            self.time_widget.axes_map.graphs.remove(graph)
        # self.time_axes.clear()
        x_time_value = list(map(convert_to_hours, time_value))
        graph = self.time_axes.scatter(x_time_value, dtec_value, s=0.8, color='blue')
        self.time_widget.axes_map.graphs.append(graph)
        # self.update_time_value()
        self.time_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_time_dtec_file_stem(self.out_dir)}.png"

        # if not os.path.isfile(fig_file_name):
        self.time_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def plot_lat_time_data(self):
        self.update_time_value()
        coord_values = dict()
        coord_values['lon'] = GeoCoord(self.spin_lon_start_degs.value(),
                                       self.spin_lon_start_mins.value())
        coord_values['lon_span'] = GeoCoord(self.spin_lon_span_degs.value(),
                                            self.spin_lon_span_mins.value())
        self.gnss_data.coord_values = coord_values
        lat_file_name = f"{self.gnss_data.get_lat_time_dtec_file_stem(self.out_dir)}_av.txt"
        self.keo_lat_color_bar.cmap = colormaps[self.combo_cmap.currentText()]
        cmap = self.keo_lat_color_bar.cmap
        v_min = self.dspin_lat_time_min.value()
        v_max = self.dspin_lat_time_max.value()
        norm = Normalize(vmin=v_min, vmax=v_max)
        self.keo_lat_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
        time_span = dt.timedelta(seconds=30)
        x_time_span = 1 / 120
        self.analyzed_coords['lat_span'] = GeoCoord(self.spin_lat_span_degs.value(),
                                                    self.spin_lat_span_mins.value())
        lat_span = self.analyzed_coords['lat_span'].get_float_degs()
        if os.path.isfile(lat_file_name):
            with open(lat_file_name, mode='r') as res_file:
                raw_data = [line.split('\t') for line in res_file]
                for data in raw_data:
                    time_value = convert_to_hours(dt.datetime.strptime(data[0], TIME_FORMAT))
                    lat_value = float(data[1])
                    dtec_value = float(data[2])
                    c = self.keo_lat_color_bar.cmap(norm(dtec_value))
                    self.keo_lat_axes.add_patch(Rectangle(xy=(time_value - x_time_span / 2,
                                                              lat_value - lat_span / 2),
                                                          width=x_time_span, height=lat_span,
                                                          edgecolor='none',
                                                          facecolor=c))
        else:
            current_date = self.dt_data_time_start.dateTime().toPyDateTime().date()
            self.read_data()
            self.gnss_data.get_lat_time_dtec(self.out_dir, coord_values, current_date)
            min_time = self.limit_time['min_time']
            max_time = self.limit_time['max_time']
            n_time = math.ceil((max_time - min_time) / time_span)
            plot_time = [min_time + j * time_span for j in range(n_time)]
            coords = self.map_widget.axes_map.coords
            min_lat = coords['min_lat'].get_float_degs()
            max_lat = coords['max_lat'].get_float_degs()
            n_lat = math.ceil((max_lat - min_lat) / lat_span)
            plot_lat = [min_lat + lat_span / 2 + j * lat_span for j in range(n_lat)]
            with open(lat_file_name, mode='w') as res_file:
                for c_time in plot_time:
                    current_time = convert_to_hours(c_time)
                    time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2,
                                            self.gnss_data.lat_time_dtec))
                    if time_data:
                        for lat in plot_lat:
                            lat_time_data = list(filter(lambda x: abs(x[1] - lat) <= lat_span / 2, time_data))
                            if lat_time_data:
                                lat_time_dtec_raw = list(zip(*lat_time_data))[2]
                                lat_time_dtec = list(map(self.dtec_corr, lat_time_dtec_raw))
                                dtec_value = sum(lat_time_dtec) / len(lat_time_dtec)
                                res_file.write(f"{c_time.strftime('%Y.%m.%d %H:%M:%S')}\t{lat}\t{dtec_value}\n")
                                c = self.keo_lat_color_bar.cmap(norm(dtec_value))
                                self.keo_lat_axes.add_patch(Rectangle(xy=(current_time - x_time_span / 2,
                                                                          lat - lat_span / 2),
                                                                      width=x_time_span, height=lat_span,
                                                                      edgecolor='none',
                                                                      facecolor=c))
        self.keo_lat_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_lat_time_dtec_file_stem(self.out_dir)}.png"
        # if not os.path.isfile(fig_file_name):
        self.keo_lat_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def plot_lon_time_data(self):
        self.update_time_value()
        coord_values = dict()
        coord_values['lat'] = GeoCoord(self.spin_lat_start_degs.value(),
                                       self.spin_lat_start_mins.value())
        coord_values['lat_span'] = GeoCoord(self.spin_lat_span_degs.value(),
                                            self.spin_lat_span_mins.value())
        self.gnss_data.coord_values = coord_values
        lon_file_name = f"{self.gnss_data.get_lon_time_dtec_file_stem(self.out_dir)}_av.txt"
        self.keo_lon_color_bar.cmap = colormaps[self.combo_cmap.currentText()]
        cmap = self.keo_lon_color_bar.cmap
        v_min = self.dspin_lon_time_min.value()
        v_max = self.dspin_lon_time_max.value()
        norm = Normalize(vmin=v_min, vmax=v_max)
        self.keo_lon_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
        time_span = dt.timedelta(seconds=30)
        x_time_span = 1 / 120
        self.analyzed_coords['lon_span'] = GeoCoord(self.spin_lon_span_degs.value(),
                                                    self.spin_lon_span_mins.value())
        lon_span = self.analyzed_coords['lon_span'].get_float_degs()
        current_lat = coord_values['lat'].get_float_degs()
        corr_lon_span = lon_span / math.cos(math.radians(current_lat))
        if os.path.isfile(lon_file_name):
            with open(lon_file_name, mode='r') as res_file:
                raw_data = [line.split('\t') for line in res_file]
                for data in raw_data:
                    time_value = convert_to_hours(dt.datetime.strptime(data[0], TIME_FORMAT))
                    lon_value = float(data[1])
                    dtec_value = float(data[2])
                    c = self.keo_lon_color_bar.cmap(norm(dtec_value))
                    self.keo_lon_axes.add_patch(Rectangle(xy=(time_value - x_time_span / 2,
                                                              lon_value - corr_lon_span / 2),
                                                          width=x_time_span, height=corr_lon_span,
                                                          edgecolor='none',
                                                          facecolor=c))
        else:
            current_date = self.dt_data_time_start.dateTime().toPyDateTime().date()
            self.read_data()
            self.gnss_data.get_lon_time_dtec(self.out_dir, coord_values, current_date)
            min_time = self.limit_time['min_time']
            max_time = self.limit_time['max_time']
            n_time = math.ceil((max_time - min_time) / time_span)
            plot_time = [min_time + j * time_span for j in range(n_time)]
            coords = self.map_widget.axes_map.coords
            min_lon = coords['min_lon'].get_float_degs()
            max_lon = coords['max_lon'].get_float_degs()
            corr_lon_span = lon_span / math.cos(math.radians(current_lat))
            n_lon = math.ceil((max_lon - min_lon) / corr_lon_span)
            plot_lon = [min_lon + lon_span / 2 + j * corr_lon_span for j in range(n_lon)]
            with open(lon_file_name, mode='w') as res_file:
                for c_time in plot_time:
                    current_time = convert_to_hours(c_time)
                    time_data = list(filter(lambda x: abs(x[0] - c_time) <= time_span / 2,
                                            self.gnss_data.lon_time_dtec))
                    if time_data:
                        for lon in plot_lon:
                            lon_time_data = list(filter(lambda x: abs(x[1] - lon) <= corr_lon_span / 2, time_data))
                            if lon_time_data:
                                lon_time_dtec_raw = list(zip(*lon_time_data))[2]
                                lon_time_dtec = list(map(self.dtec_corr, lon_time_dtec_raw))
                                dtec_value = sum(lon_time_dtec) / len(lon_time_dtec)
                                res_file.write(f"{c_time.strftime('%Y.%m.%d %H:%M:%S')}\t{lon}\t{dtec_value}\n")
                                c = self.keo_lon_color_bar.cmap(norm(dtec_value))
                                self.keo_lon_axes.add_patch(Rectangle(xy=(current_time - x_time_span / 2,
                                                                          lon - corr_lon_span / 2),
                                                                      width=x_time_span, height=corr_lon_span,
                                                                      edgecolor='none',
                                                                      facecolor=c))
        self.keo_lon_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_lon_time_dtec_file_stem(self.out_dir)}.png"
        # if not os.path.isfile(fig_file_name):
        self.keo_lon_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def update_figures(self):
        if self.gnss_archive:
            self.set_coords_time()
            self.plot_time_stamp_data()
            self.plot_coords_stamp_data()
            print("Figure updating is completed.")
