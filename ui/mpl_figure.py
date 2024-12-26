import matplotlib.pyplot as plt

DEFAULT_TICK_PARAMS = {'font_size': 18, 'font_weight': 'normal',
                       'family': 'Times New Roman', 'direction': 'in'}

DEFAULT_FIGURE_PARAMS = {'pad': 3}


class AxesMap:
    def __init__(self, tick_params=None, figure_params=None):
        self.tick_params = DEFAULT_TICK_PARAMS.copy() if tick_params is None \
            else tick_params.copy()
        self.figure_params = DEFAULT_FIGURE_PARAMS.copy() if figure_params is None \
            else figure_params.copy()
        self.graphs = []
        self.figure = None

    def create_figure(self):
        self.figure = plt.figure()
        ax = plt.axes()
        self.figure.add_axes(ax)
        ax.tick_params(labelsize=self.tick_params['font_size'],
                       labelfontfamily=self.tick_params['family'],
                       direction=self.tick_params['direction'], pad=3)
        ax.set_ylabel(ylabel='dTEC (TECU)', fontsize=self.tick_params['font_size'],
                      family=self.tick_params['family'])
        ax.set_xlabel(xlabel='UT', fontsize=self.tick_params['font_size'],
                      family=self.tick_params['family'])
        ax.xaxis.set_label_coords(0.97, -0.036)
        plt.tight_layout(pad=self.figure_params['pad'])


if __name__ == '__main__':
    g = AxesMap()
    g.create_figure()
    plt.show()
