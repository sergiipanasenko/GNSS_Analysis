from PyQt5.QtWidgets import QMainWindow, QFileDialog, QSizePolicy

from ui.cartopy_figure import MapLAEA, DEFAULT_LABEL_PARAMS, DEFAULT_GRID_PARAMS
from ui.main_window import Ui_MainWindow
import cartopy.crs as ccrs

from zipfile import Path
from matplotlib.patches import Rectangle
from matplotlib import colormaps
from matplotlib.colors import Normalize

from ui.qt_utils import MplWidget, MplCanvas


class DTECViewerForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        # parent initialisation
        super().__init__()

        # ui loading
        self.setupUi(self)
        self.time_axes = self.time_widget.canvas.figure.gca()
        self.space_axes = self.space_widget.canvas.figure.axes[0]
        self.space_cbar = self.space_widget.canvas.figure.axes[1]
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

        # connections
        self.pushButton.clicked.connect(self.update_coords)
        self.pushButton_2.clicked.connect(self.update_time_value)
        self.actionOpen_receiver_list.triggered.connect(self.show_receivers)
        self.actionOpen.triggered.connect(self.analyze_data)

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
        self.space_widget.geo_map = MapLAEA(coords=coords, cbar=True)
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
        self.space_cbar = self.space_widget.canvas.figure.axes[1]
        self.receiver_axes = self.receiver_widget.canvas.figure.axes[0]

    def update_time_value(self):
        min_time = float(self.lineEdit_6.text())
        max_time = float(self.lineEdit_5.text())
        min_value = float(self.lineEdit_8.text())
        max_value = float(self.lineEdit_7.text())
        self.time_axes.set_xlim(min_time, max_time)
        self.time_axes.set_ylim(min_value, max_value)
        self.time_widget.canvas.draw()

    def show_receivers(self):
        rec_names = []
        rec_lat = []
        rec_lon = []
        file_name = QFileDialog.getOpenFileName(
            caption="Open receiver list file",
            filter="All files (*);;Text files (*.dat *.txt)",
            initialFilter="Text files (*.dat *.txt)",
            directory='d:/Surnames/Skipa/')
        if file_name[0]:
            with open(file_name[0]) as receiver_file:
                _ = receiver_file.readline()
                for line in receiver_file:
                    data = line.split()
                    rec_names.append(data[0])
                    rec_lat.append(float(data[1]))
                    rec_lon.append(float(data[2]))
            self.receiver_axes.scatter(rec_lon, rec_lat, c='blue', s=10, marker='o',
                                       transform=ccrs.PlateCarree())
            self.receiver_widget.canvas.draw()

    def analyze_data(self):
        current_lat = float(self.lineEdit_12.text())
        current_lon = float(self.lineEdit_13.text())
        lat_span = float(self.lineEdit_11.text())
        lon_span = float(self.lineEdit_14.text())
        current_time = float(self.lineEdit_10.text())
        time_span = float(self.lineEdit_9.text())
        time_data = []
        time_dtec_data = []
        lat_data = []
        lon_data = []
        space_dtec_data = []

        file_name = QFileDialog.getOpenFileName(
            caption="Open GNSS data archive",
            filter="Archive files (*.zip)",
            initialFilter="Archive files (*.zip)",
            directory='d:/Surnames/Skipa/')
        if file_name[0]:
            root_dir = file_name[0].split('/')[-1].split('.')[0]
            filter_dir = 'Window_3600_Seconds'
            rec_paths = Path(file_name[0], f'{root_dir}/')
            rec_dirs = (rec_dir.name for rec_dir in rec_paths.iterdir())
            for rec_dir in rec_dirs:
                for i in range(1, 33):
                    at_file = f"{root_dir}/{rec_dir}/{filter_dir}/G{str(i).zfill(2)}.txt"
                    g_file = Path(file_name[0], at_file)
                    if g_file.exists():
                        with g_file.open(mode='r') as txt:
                            title = txt.readline().split()
                            lines_raw = txt.readlines()
                        lines = filter(lambda x:
                                       float(x.split()[title.index('elm')]) > 30,
                                       lines_raw)
                        for line in lines:
                            g_data = dict(zip(title, line.split()))
                            time = (float(g_data['hour']) + float(g_data['min']) / 60 +
                                    float(g_data['sec']) / 3600)
                            time_cond = (time > current_time - time_span / 2) and (time < current_time + time_span / 2)
                            if time_cond:
                                lat_data.append(float(g_data['gdlat']))
                                lon_data.append(float(g_data['gdlon']))
                                space_dtec_data.append(float(g_data['dTEC']))
                            if all((float(g_data['gdlat']) >= current_lat - lat_span / 2,
                                    float(g_data['gdlat']) <= current_lat + lat_span / 2,
                                    float(g_data['gdlon']) >= current_lon - lon_span / 2,
                                    float(g_data['gdlon']) <= current_lon + lon_span / 2)):
                                time_data.append(time)
                                time_dtec_data.append(float(g_data['dTEC']))
            self.time_axes.scatter(time_data, time_dtec_data, s=0.8, color='blue')
            self.time_widget.canvas.draw()
            cmap = colormaps['viridis']
            norm = Normalize(vmin=-0.2, vmax=0.2)
            c = cmap(norm(space_dtec_data))
            for i in range(len(lat_data)):
                lon_coord = lon_data[i] - lon_span / 2
                lat_coord = lat_data[i] - lat_span / 2
                self.space_axes.add_patch(Rectangle(xy=(lon_coord, lat_coord),
                                                    width=lon_span, height=lat_span,
                                                    edgecolor='none',
                                                    facecolor=c[i],
                                                    transform=ccrs.PlateCarree()))
            self.space_widget.canvas.draw()
            save_time = self.lineEdit_10.text()
            self.space_widget.canvas.figure.savefig(
                dpi=200,
                fname=f'd:/Surnames/Skipa/June5-8_2023/157/{save_time}.png')
