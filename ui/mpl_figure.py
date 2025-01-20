import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable

from ui.cartopy_figure import DEFAULT_CBAR_PARAMS

DEFAULT_TICK_PARAMS = {'font_size': 18, 'font_weight': 'normal',
                       'family': 'Times New Roman', 'direction': 'in'}

DEFAULT_FIGURE_PARAMS = {'pad': 3}

DEFAULT_LABEL_PARAMS = {'x_label': 'UT', 'y_label': 'dTEC (TECU)', 'x_label_coords': (0.97, -0.036)}


class AxesMap:
    def __init__(self, tick_params=None, figure_params=None, is_cbar=False,
                 cbar_params=None, label_params=None, axes_ratio=None, cbar_orient='vertical',
                 cbar_title_loc=1.0):
        self.axes_ratio = axes_ratio
        self.tick_params = DEFAULT_TICK_PARAMS.copy() if tick_params is None \
            else tick_params.copy()
        self.figure_params = DEFAULT_FIGURE_PARAMS.copy() if figure_params is None \
            else figure_params.copy()
        self.label_params = DEFAULT_LABEL_PARAMS.copy() if label_params is None \
            else label_params.copy()
        self.graphs = []
        self.figure = None
        self.cbar_params = DEFAULT_CBAR_PARAMS.copy() if cbar_params is None \
            else cbar_params.copy()
        self.is_cbar = is_cbar
        self.color_bar = None
        self.cbar_orient = cbar_orient
        self.cbar_title_loc = cbar_title_loc

    def create_figure(self):
        self.figure = plt.figure()
        ax = plt.axes(box_aspect=self.axes_ratio)
        self.figure.add_axes(ax)
        ax.tick_params(labelsize=self.tick_params['font_size'],
                       labelfontfamily=self.tick_params['family'],
                       direction=self.tick_params['direction'], pad=3)
        ax.set_ylabel(ylabel=self.label_params['y_label'], fontsize=self.tick_params['font_size'],
                      family=self.tick_params['family'])
        ax.set_xlabel(xlabel=self.label_params['x_label'], fontsize=self.tick_params['font_size'],
                      family=self.tick_params['family'])
        ax.xaxis.set_label_coords(*self.label_params['x_label_coords'])
        if self.is_cbar:
            norm = plt.Normalize(-1, 1)
            # cmap = colormaps['viridis']
            cmap = plt.colormaps['rainbow']
            self.color_bar = plt.colorbar(mappable=ScalarMappable(norm=norm, cmap=cmap), pad=0.15,
                                          orientation=self.cbar_orient, alpha=0, ax=ax, shrink=0.95,
                                          fraction=0.05, aspect=30, ticks=[-1, -0.5, 0, 0.5, 1])
            self.color_bar.ax.tick_params(labelsize=self.cbar_params['size'],
                                          labelfontfamily=self.cbar_params['family'],
                                          labelcolor=self.cbar_params['color'])
            self.color_bar.ax.set_title(label=self.cbar_params['title'],
                                        pad=self.cbar_params['title_pad'],
                                        family=self.cbar_params['family'],
                                        fontsize=self.cbar_params['size'],
                                        color=self.cbar_params['color'],
                                        y=self.cbar_title_loc)
        plt.tight_layout(pad=self.figure_params['pad'])


if __name__ == '__main__':
    g = AxesMap()
    g.create_figure()
    plt.show()
