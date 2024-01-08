from PyQt5.QtWidgets import QSizePolicy, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from matplotlib.pyplot import figure as mpl_figure


class MplCanvas(FigureCanvas):
    def __init__(self, figure):
        self.figure = figure
        FigureCanvas.__init__(self, self.figure)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Ignored, QSizePolicy.Ignored)
        FigureCanvas.updateGeometry(self)


class MplWidget(QWidget):
    def __init__(self, parent=None, geo_map=None):
        # parent initialisation
        super().__init__()
        self.geo_map = geo_map
        figure = mpl_figure() if geo_map is None else geo_map.create_figure()
        # Create canvas object
        self.canvas = MplCanvas(figure)
        self.vbl = QVBoxLayout()  # Set box for plotting
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)


if __name__ == '__main__':
    fig = mpl_figure()
    canvas = MplCanvas(fig)
