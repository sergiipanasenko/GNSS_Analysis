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
    def __init__(self, parent=None, axes_map=None):
        # parent initialisation
        super().__init__()
        self.axes_map = axes_map
        if self.axes_map is None:
            figure = mpl_figure()
        else:
            self.axes_map.create_figure()
            figure = self.axes_map.figure
        # Create canvas object
        self.canvas = MplCanvas(figure)
        self.vbl = QVBoxLayout()  # Set box for plotting
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)


if __name__ == '__main__':
    fig = mpl_figure()
    canvas = MplCanvas(fig)
