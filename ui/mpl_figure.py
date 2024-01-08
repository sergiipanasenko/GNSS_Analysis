import matplotlib.pyplot as plt

DEFAULT_TICK_PARAMS = {'font_size': 24, 'font_weight': 'normal',
                       'family': 'Times New Roman', 'direction': 'in'}

DEFAULT_FIGURE_PARAMS = {'pad': 2}


class MapAxes:
    def __init__(self, tick_params=None, figure_params=None):
        self.tick_params = DEFAULT_TICK_PARAMS.copy() if tick_params is None \
            else tick_params.copy()
        self.figure_params = DEFAULT_FIGURE_PARAMS.copy() if figure_params is None \
            else figure_params.copy()

    def create_figure(self):
        output_figure = plt.figure()
        plt.axes()
        plt.xticks(fontsize=self.tick_params['font_size'],
                   fontweight=self.tick_params['font_weight'],
                   family=self.tick_params['family'])
        plt.yticks(fontsize=self.tick_params['font_size'],
                   fontweight=self.tick_params['font_weight'],
                   family=self.tick_params['family'])
        plt.tick_params(direction=self.tick_params['direction'])
        plt.tight_layout(pad=self.figure_params['pad'])
        return output_figure


if __name__ == '__main__':
    fig = MapAxes().create_figure()
    plt.show()
