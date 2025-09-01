from PyQt5.QtWidgets import QFileDialog

from ui.dTEC_window import DTEC_Window
from utils.time import convert_to_hours, timedelta_to_time, time_to_timedelta
from ui.cartopy_figure import GeoAxesMap, DEFAULT_MAP_PARAMS, DEFAULT_GRID_PARAMS, PROJECTIONS
from utils.geo.geo_coords import GeoCoord
from dTEC import DTEC_handling
from gnss import TIME_FORMAT

import cartopy.crs as ccrs
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib import colormaps

import math
import os
import array
import datetime as dt

OUTPUT_DIR = 'results/out'
INPUT_DIR = 'results/in'
RECEIVER_FILE = 'Sites.txt'
STAGES = ('Original', 'Without outliers', 'Interpolated', 'Bandpass filtered')
DEFAULT_CMAP = 'rainbow'
TIME_SAMPLE = dt.timedelta(seconds=30)


class DTECViewerForm(DTEC_Window):
    def __init__(self):
        # parent initialisation
        super().__init__()

        # settings
        self.combo_region.setCurrentIndex(2)
        self.combo_projection.addItems(PROJECTIONS)
        self.combo_cmap.addItems(list(colormaps))
        self.combo_cmap.setCurrentIndex(self.combo_cmap.findText(DEFAULT_CMAP))
        self.combo_stage.addItems(STAGES)
        min_date_time = dt.datetime.combine(dt.date.today(), dt.time(0, 0, 0))
        max_date_time = min_date_time + dt.timedelta(hours=23, minutes=59, seconds=59)
        current_date_time = dt.datetime.now()
        self.time_dtec = {'min_time': min_date_time, 'max_time': max_date_time,
                          'min_dtec': -1.0, 'max_dtec': 1.0}
        self.data_coords = {"start_lon": GeoCoord(33, 22, 18),
                            'end_lon': GeoCoord(33, 22, 18),
                            'lon_span': GeoCoord(0, 45),
                            'lon_step': GeoCoord(0, 45),
                            'start_lat': GeoCoord(46, 46, 34),
                            'end_lat': GeoCoord(46, 46, 34),
                            'lat_span': GeoCoord(0, 45),
                            'lat_step': GeoCoord(0, 45)}
        self.data_time = {'start_time': current_date_time,
                          'end_time': current_date_time,
                          'time_span': TIME_SAMPLE,
                          'time_step': TIME_SAMPLE}
        self.data_dtec = {'min_lat_lon': -0.5,
                          'max_lat_lon': 0.5,
                          'min_lat_time': -0.5,
                          'max_lat_time': 0.5,
                          'min_lon_time': -0.5,
                          'max_lon_time': 0.5}

        float_min_time = convert_to_hours(min_date_time)
        float_max_time = convert_to_hours(max_date_time)
        self.time_axes.set_xlim((float_min_time, float_max_time))
        self.time_axes.set_ylim((self.time_dtec['min_dtec'], self.time_dtec['max_dtec']))
        self.keo_lat_axes.set_xlim((float_min_time, float_max_time))
        self.keo_lon_axes.set_xlim((float_min_time, float_max_time))

        self.dt_xaxis_min.setDateTime(self.time_dtec['min_time'])
        self.dt_xaxis_max.setDateTime(self.time_dtec['max_time'])
        self.dspin_yaxis_min.setValue(self.time_dtec['min_dtec'])
        self.dspin_yaxis_max.setValue(self.time_dtec['max_dtec'])

        self.dt_data_time_start.setDateTime(self.data_time['start_time'])
        self.dt_data_time_end.setDateTime(self.data_time['end_time'])
        self.t_data_time_span.setTime(timedelta_to_time(self.data_time['time_span']))
        self.t_data_time_step.setTime(timedelta_to_time(self.data_time['time_step']))

        self.spin_lat_start_degs.setValue(self.data_coords['start_lat'].degs)
        self.spin_lat_start_mins.setValue(self.data_coords['start_lat'].mins)
        self.spin_lat_end_degs.setValue(self.data_coords['end_lat'].degs)
        self.spin_lat_end_mins.setValue(self.data_coords['end_lat'].mins)
        self.spin_lon_start_degs.setValue(self.data_coords['start_lon'].degs)
        self.spin_lon_start_mins.setValue(self.data_coords['start_lon'].mins)
        self.spin_lon_end_degs.setValue(self.data_coords['end_lon'].degs)
        self.spin_lon_end_mins.setValue(self.data_coords['end_lon'].mins)
        self.spin_lat_span_degs.setValue(self.data_coords['lat_span'].degs)
        self.spin_lat_span_mins.setValue(self.data_coords['lat_span'].mins)
        self.spin_lat_step_degs.setValue(self.data_coords['lat_step'].degs)
        self.spin_lat_step_mins.setValue(self.data_coords['lat_step'].mins)
        self.spin_lon_span_degs.setValue(self.data_coords['lon_span'].degs)
        self.spin_lon_span_mins.setValue(self.data_coords['lon_span'].mins)
        self.spin_lon_step_degs.setValue(self.data_coords['lon_step'].degs)
        self.spin_lon_step_mins.setValue(self.data_coords['lon_step'].mins)

        self.dspin_lat_lon_min.setValue(self.data_dtec['min_lat_lon'])
        self.dspin_lat_lon_max.setValue(self.data_dtec['max_lat_lon'])
        self.dspin_lat_time_min.setValue(self.data_dtec['min_lat_time'])
        self.dspin_lat_time_max.setValue(self.data_dtec['max_lat_time'])
        self.dspin_lon_time_min.setValue(self.data_dtec['min_lon_time'])
        self.dspin_lon_time_max.setValue(self.data_dtec['max_lon_time'])

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

        self.dTEC_parser = DTEC_handling(INPUT_DIR, OUTPUT_DIR)
        self.input_data_file = None
        self.receiver_file = None

        self.filter_sec = 7200
        self.min_elm = 30

        # connections
        self.push_update.clicked.connect(self.update_data)
        self.actionOpen.triggered.connect(self.choose_input_data_dir)

    def update_data(self):
        if self.tabWidget_set.currentIndex() == 0:
            self.update_coords()
        elif self.tabWidget_set.currentIndex() == 1:
            self.update_time_values()
        elif self.tabWidget_set.currentIndex() == 2:
            self.update_coords()
            self.update_time_values()
            self.update_data_values()
            self.plot_time_stamp_data()
            self.plot_coords_stamp_data()
            self.plot_lat_time_data()
            self.plot_lon_time_data()

    def update_coords(self):
        self.combo_region.setCurrentIndex(0)
        min_lat = GeoCoord(self.spin_minlat_degs.value(), self.spin_minlat_mins.value())
        max_lat = GeoCoord(self.spin_maxlat_degs.value(), self.spin_maxlat_mins.value())
        min_lon = GeoCoord(self.spin_minlon_degs.value(), self.spin_minlon_mins.value())
        max_lon = GeoCoord(self.spin_maxlon_degs.value(), self.spin_maxlon_mins.value())
        central_lat = GeoCoord(self.spin_centrlat_degs.value(), self.spin_centrlat_mins.value())
        central_lon = GeoCoord(self.spin_centrlon_degs.value(), self.spin_centrlon_mins.value())
        coords = {'min_lat': min_lat, 'max_lat': max_lat,
                  'min_lon': min_lon, 'max_lon': max_lon,
                  'central_long': central_lon,
                  'central_lat': central_lat}
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

    def update_time_values(self):
        self.time_dtec['min_time'] = self.dt_xaxis_min.dateTime().toPyDateTime()
        self.time_dtec['max_time'] = self.dt_xaxis_max.dateTime().toPyDateTime()
        self.time_dtec['min_dtec'] = self.dspin_yaxis_min.value()
        self.time_dtec['max_dtec'] = self.dspin_yaxis_max.value()
        min_time = convert_to_hours(self.time_dtec['min_time'])
        max_time = convert_to_hours(self.time_dtec['max_time'])
        self.time_axes.set_xlim(min_time, max_time)
        self.time_axes.set_ylim(self.time_dtec['min_dtec'], self.time_dtec['max_dtec'])
        self.time_widget.canvas.draw()

    def update_data_values(self):
        self.data_coords['start_lon'] = GeoCoord(self.spin_minlon_degs.value(),
                                                 self.spin_minlon_mins.value())
        self.data_coords['end_lon'] = GeoCoord(self.spin_maxlon_degs.value(),
                                               self.spin_maxlon_mins.value())
        self.data_coords['start_lat'] = GeoCoord(self.spin_minlat_degs.value(),
                                                 self.spin_minlat_mins.value())
        self.data_coords['end_lat'] = GeoCoord(self.spin_maxlat_degs.value(),
                                               self.spin_maxlat_mins.value())
        self.data_coords['lat_span'] = GeoCoord(self.spin_lat_span_degs.value(),
                                                self.spin_lat_span_mins.value())
        self.data_coords['lon_span'] = GeoCoord(self.spin_lon_span_degs.value(),
                                                self.spin_lon_span_mins.value())
        self.data_coords['lat_step'] = GeoCoord(self.spin_lat_step_degs.value(),
                                                self.spin_lat_step_mins.value())
        self.data_coords['lon_step'] = GeoCoord(self.spin_lon_step_degs.value(),
                                                self.spin_lon_step_mins.value())
        self.data_time['start_time'] = self.dt_data_time_start.dateTime().toPyDateTime()
        self.data_time['start_time'] = self.dt_data_time_end.dateTime().toPyDateTime()
        self.data_time['time_span'] = time_to_timedelta(self.t_data_time_span.time().toPyTime())
        self.data_time['time_step'] = time_to_timedelta(self.t_data_time_step.time().toPyTime())
        self.data_dtec['min_lat_lon'] = self.dspin_lat_lon_min.value()
        self.data_dtec['max_lat_lon'] = self.dspin_lat_lon_max.value()
        self.data_dtec['min_lat_time'] = self.dspin_lat_time_min.value()
        self.data_dtec['max_lat_time'] = self.dspin_lat_time_max.value()
        self.data_dtec['min_lon_time'] = self.dspin_lon_time_min.value()
        self.data_dtec['max_lon_time'] = self.dspin_lon_time_max.value()

    def plot_receivers(self):
        if self.receiver_file:
            rec_lon = array.array('f')
            rec_lat = array.array('f')
            if os.path.isfile(self.receiver_file):
                with open(self.receiver_file, mode='r') as rec_file:
                    _ = rec_file.readline()
                    for line in rec_file:
                        data = line.split()
                        rec_lat.append(float(data[1]))
                        rec_lon.append(float(data[2]))
            self.receiver_axes.scatter(rec_lon, rec_lat, c='blue', s=10, marker='o',
                                       transform=ccrs.PlateCarree())
            self.receiver_widget.canvas.draw()

    def choose_input_data_dir(self):
        input_data_directory = QFileDialog.getExistingDirectory(self, 'Select Input Data Folder',
                                                                directory=INPUT_DIR)
        if input_data_directory:
            self.receiver_file = f"{input_data_directory}/{RECEIVER_FILE}"
            self.plot_receivers()
            input_params = input_data_directory.split('/')
            self.dTEC_parser.gnss_parser.add_dir = '/'.join(input_params[-4:])
            current_date = input_params[-2]
            current_year = int(input_params[-3])
            current_month = int(input_params[-2][5:7])
            current_day = int(input_params[-2][8:])
            self.filter_sec = int(input_params[-1])
            self.dTEC_parser.input_data_file = f"{input_data_directory}/{current_date}_{self.filter_sec}.txt"
            start_time = dt.datetime(current_year, current_month, current_day, 0, 0, 0)
            end_time = dt.datetime(current_year, current_month, current_day, 23, 59, 59)
            self.time_dtec['min_time'] = start_time
            self.time_dtec['max_time'] = end_time
            self.data_time['start_time'] = start_time
            self.data_time['end_time'] = end_time
            self.dt_xaxis_min.setDateTime(start_time)
            self.dt_xaxis_max.setDateTime(end_time)
            self.dt_data_time_start.setDateTime(start_time)
            self.dt_data_time_end.setDateTime(end_time)

    def plot_time_stamp_data(self):
        self.map_color_bar.cmap = colormaps[self.combo_cmap.currentText()]
        cmap = self.map_color_bar.cmap
        v_min = self.data_dtec['min_lat_lon']
        v_max = self.data_dtec['max_lat_lon']
        norm = Normalize(vmin=v_min, vmax=v_max)
        self.map_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
        lat_span = self.data_coords['lat_span'].get_float_degs()
        lon_span = self.data_coords['lon_span'].get_float_degs()
        self.dTEC_parser.gnss_parser.coord_values['lon_span'] = lon_span
        self.dTEC_parser.gnss_parser.coord_values['lat_span'] = lat_span
        time_file_name = f"{self.dTEC_parser.gnss_parser.get_lon_lat_dtec_file_stem(OUTPUT_DIR)}_av.txt"
        if not os.path.isfile(time_file_name):
            self.dTEC_parser.gnss_parser.time_values = {
                'time': self.data_time['start_time'],
                'time_span': self.data_time['time_span']
            }
            coords = self.map_widget.axes_map.coords
            self.dTEC_parser.create_time_stamp_data(coords)
        with open(time_file_name, mode='r') as res_file:
            raw_data = [line.split('\t') for line in res_file]
            for data in raw_data:
                lon_value = float(data[1])
                lat_value = float(data[0])
                dtec_value = float(data[2])
                corr_lon_span = lon_span / math.cos(math.radians(lat_value))
                c = self.map_color_bar.cmap(norm(dtec_value))
                self.map_axes.add_patch(Rectangle(xy=(lon_value - corr_lon_span / 2, lat_value - lat_span / 2),
                                                  width=corr_lon_span, height=lat_span,
                                                  edgecolor='none',
                                                  facecolor=c,
                                                  transform=ccrs.PlateCarree()))
        current_time = self.dTEC_parser.gnss_parser.time_values['time'].strftime("%Y-%m-%d   %H:%M:%S")
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
        fig_file_name = f"{self.gnss_data.get_lon_lat_dtec_file_stem(OUTPUT_DIR)}.png"
        # if not os.path.isfile(fig_file_name):
        self.map_widget.canvas.figure.savefig(dpi=300, fname=fig_file_name)

    def plot_coords_stamp_data(self):
        coord_file_name = f"{self.dTEC_parser.gnss_parser.get_time_dtec_file_stem(OUTPUT_DIR)}_av.txt"
        if not os.path.isfile(coord_file_name):
            coord_values = {
                'lon': self.data_coords['min_lon'],
                'lon_span': self.data_coords['lon_span'],
                'lat': self.data_coords['min_lat'],
                'lat_span': self.data_coords['lat_span']
            }
            self.dTEC_parser.gnss_parser.coord_values = coord_values
            time_values = {
                'min_time': self.time_dtec['min_time'],
                'max_time': self.time_dtec['min_time'],
                'time_span': TIME_SAMPLE
            }
            self.dTEC_parser.create_coords_stamp_data(time_values)
        with open(coord_file_name, mode='r') as res_file:
            raw_data = [line.split('\t') for line in res_file]
            data = list(zip(*raw_data))
            time_value = [dt.datetime.strptime(x, TIME_FORMAT) for x in data[0]]
            dtec_value = list(map(float, data[1]))
        for graph in self.time_widget.axes_map.graphs:
            graph.remove()
            self.time_widget.axes_map.graphs.remove(graph)
        x_time_value = list(map(convert_to_hours, time_value))
        graph = self.time_axes.scatter(x_time_value, dtec_value, s=0.8, color='blue')
        self.time_widget.axes_map.graphs.append(graph)
        self.time_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_time_dtec_file_stem(OUTPUT_DIR)}.png"

        # if not os.path.isfile(fig_file_name):
        self.time_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def plot_lat_time_data(self):
        self.update_time_values()
        coord_values = dict()
        coord_values['lon'] = GeoCoord(self.spin_lon_start_degs.value(),
                                       self.spin_lon_start_mins.value())
        coord_values['lon_span'] = GeoCoord(self.spin_lon_span_degs.value(),
                                            self.spin_lon_span_mins.value())
        self.gnss_data.coord_values = coord_values
        lat_file_name = f"{self.gnss_data.get_lat_time_dtec_file_stem(OUTPUT_DIR)}_av.txt"
        self.keo_lat_color_bar.cmap = colormaps[self.combo_cmap.currentText()]
        cmap = self.keo_lat_color_bar.cmap
        v_min = self.dspin_lat_time_min.value()
        v_max = self.dspin_lat_time_max.value()
        norm = Normalize(vmin=v_min, vmax=v_max)
        self.keo_lat_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
        time_span = dt.timedelta(seconds=30)
        x_time_span = 1 / 120
        self.data_coords['lat_span'] = GeoCoord(self.spin_lat_span_degs.value(),
                                                self.spin_lat_span_mins.value())
        lat_span = self.data_coords['lat_span'].get_float_degs()
        if not os.path.isfile(lat_file_name):
            current_date = self.dt_data_time_start.dateTime().toPyDateTime().date()
            self.read_data()
            self.gnss_data.get_lat_time_dtec(OUTPUT_DIR, coord_values, current_date)
            min_time = self.time_dtec['min_time']
            max_time = self.time_dtec['max_time']
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
                                # lat_time_dtec = list(map(dtec_corr, lat_time_dtec_raw))
                                lat_time_dtec = lat_time_dtec_raw
                                dtec_value = sum(lat_time_dtec) / len(lat_time_dtec)
                                res_file.write(f"{c_time.strftime('%Y.%m.%d %H:%M:%S')}\t{lat}\t{dtec_value}\n")
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
        self.keo_lat_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_lat_time_dtec_file_stem(OUTPUT_DIR)}.png"
        # if not os.path.isfile(fig_file_name):
        self.keo_lat_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def plot_lon_time_data(self):
        self.update_time_values()
        coord_values = dict()
        coord_values['lat'] = GeoCoord(self.spin_lat_start_degs.value(),
                                       self.spin_lat_start_mins.value())
        coord_values['lat_span'] = GeoCoord(self.spin_lat_span_degs.value(),
                                            self.spin_lat_span_mins.value())
        self.gnss_data.coord_values = coord_values
        lon_file_name = f"{self.gnss_data.get_lon_time_dtec_file_stem(OUTPUT_DIR)}_av.txt"
        self.keo_lon_color_bar.cmap = colormaps[self.combo_cmap.currentText()]
        cmap = self.keo_lon_color_bar.cmap
        v_min = self.dspin_lon_time_min.value()
        v_max = self.dspin_lon_time_max.value()
        norm = Normalize(vmin=v_min, vmax=v_max)
        self.keo_lon_color_bar.update_normal(ScalarMappable(norm=norm, cmap=cmap))
        time_span = dt.timedelta(seconds=30)
        x_time_span = 1 / 120
        self.data_coords['lon_span'] = GeoCoord(self.spin_lon_span_degs.value(),
                                                self.spin_lon_span_mins.value())
        lon_span = self.data_coords['lon_span'].get_float_degs()
        current_lat = coord_values['lat'].get_float_degs()
        corr_lon_span = lon_span / math.cos(math.radians(current_lat))
        if not os.path.isfile(lon_file_name):
            current_date = self.dt_data_time_start.dateTime().toPyDateTime().date()
            self.read_data()
            self.gnss_data.get_lon_time_dtec(OUTPUT_DIR, coord_values, current_date)
            min_time = self.time_dtec['min_time']
            max_time = self.time_dtec['max_time']
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
                                # lon_time_dtec = list(map(dtec_corr, lon_time_dtec_raw))
                                lon_time_dtec = lon_time_dtec_raw
                                dtec_value = sum(lon_time_dtec) / len(lon_time_dtec)
                                res_file.write(f"{c_time.strftime('%Y.%m.%d %H:%M:%S')}\t{lon}\t{dtec_value}\n")
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
        self.keo_lon_widget.canvas.draw()
        fig_file_name = f"{self.gnss_data.get_lon_time_dtec_file_stem(OUTPUT_DIR)}.png"
        # if not os.path.isfile(fig_file_name):
        self.keo_lon_widget.canvas.figure.savefig(dpi=200, fname=fig_file_name)

    def update_figures(self):
        if self.gnss_archive:
            self.set_coords_time()
            self.plot_time_stamp_data()
            self.plot_coords_stamp_data()
            print("Figure updating is completed.")
