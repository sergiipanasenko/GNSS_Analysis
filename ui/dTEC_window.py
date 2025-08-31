from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QMainWindow
from ui.main_window1 import Ui_MainWindow


class DTEC_Window(QMainWindow, Ui_MainWindow):
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


