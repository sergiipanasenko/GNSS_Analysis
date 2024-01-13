import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader
import cartopy.feature as c_feature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

from matplotlib.pyplot import axes, figure, show, tight_layout, colorbar, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib import colormaps

UA_COORDS = {'min_lat': 44, 'max_lat': 52.5,
             'min_lon': 22, 'max_lon': 40.5,
             'central_long': 31.5, 'central_lat': 48.5}
EU_COORDS = {'min_lat': 36, 'max_lat': 71,
             'min_lon': -10, 'max_lon': 30,
             'central_long': 10, 'central_lat': 53.5}

DEFAULT_SHP_PARAMS = {'face_color': 'none', 'edge_color': 'gray',
                      'border_width': 0.3, 'coast_width': 0.3}
DEFAULT_GRID_PARAMS = {'grid_width': 0.2, 'draw_labels': True}
DEFAULT_LABEL_PARAMS = {'size': 14, 'color': 'black',
                        'family': 'Times New Roman',
                        'frame_on': True}


class MapLAEA:
    def __init__(self, shp_file_name=None, coords=None,
                 shp_params=None, grid_params=None,
                 label_params=None, is_cbar=False):
        self.coords = EU_COORDS.copy() if coords is None else coords.copy()
        self.shp_params = DEFAULT_SHP_PARAMS.copy() if shp_params is None \
            else shp_params.copy()
        self.grid_params = DEFAULT_GRID_PARAMS.copy() if grid_params is None \
            else grid_params.copy()
        self.label_params = DEFAULT_LABEL_PARAMS.copy() if label_params is None \
            else label_params.copy()
        self.shp_file_name = shp_file_name
        self.is_cbar = is_cbar
        self.color_bar = None

    def create_figure(self):
        current_crs = ccrs.LambertAzimuthalEqualArea(
            central_longitude=self.coords['central_long'],
            central_latitude=self.coords['central_lat']
        )
        output_figure = figure()
        ax = axes(projection=current_crs, frame_on=self.label_params['frame_on'])
        if self.shp_file_name is not None:
            shape_feature = c_feature.ShapelyFeature(
                Reader(self.shp_file_name).geometries(),
                ccrs.LambertAzimuthalEqualArea(), facecolor=self.shp_params['face_color'],
                edgecolor=self.shp_params['edge_color'])
            ax.add_feature(shape_feature,
                           linewidth=self.shp_params['border_width'])
        else:
            ax.add_feature(c_feature.COASTLINE, linewidth=self.shp_params['coast_width'])
            ax.add_feature(c_feature.BORDERS, linewidth=self.shp_params['border_width'])
        gl = ax.gridlines(draw_labels=self.grid_params['draw_labels'],
                          linewidth=self.grid_params['grid_width'],
                          xformatter=LONGITUDE_FORMATTER,
                          yformatter=LATITUDE_FORMATTER,
                          auto_update=True)
        gl.xlabel_style = {'size': self.label_params['size'],
                           'color': self.label_params['color'],
                           'family': self.label_params['family']}
        gl.ylabel_style = {'size': self.label_params['size'],
                           'color': self.label_params['color'],
                           'family': self.label_params['family']}
        ax.set_extent([self.coords['min_lon'], self.coords['max_lon'],
                       self.coords['min_lat'], self.coords['max_lat']],
                      crs=ccrs.PlateCarree())
        if self.is_cbar:
            norm = Normalize(-1, 1)
            cmap = colormaps['rainbow']
            self.color_bar = colorbar(mappable=ScalarMappable(norm=norm, cmap=cmap), pad=0.15,
                                      orientation='vertical')
        tight_layout(pad=2)
        return output_figure


if __name__ == '__main__':
    fig = MapLAEA(shp_file_name='geo/cntry02.shp').create_figure()
    show()
