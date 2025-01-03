import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader
import cartopy.feature as c_feature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib import colormaps


class GeoCoord:
    def __init__(self, degs: int, mins: int, secs=0):
        self.degs = degs
        self.mins = mins
        self.secs = secs

    def get_float_degs(self) -> float:
        return self.degs + self.mins / 60. + self.secs / 3600.


UA_COORDS = {'min_lat': GeoCoord(44, 0), 'max_lat': GeoCoord(52, 30),
             'min_lon': GeoCoord(22, 0), 'max_lon': GeoCoord(40, 30),
             'central_long': GeoCoord(31, 30), 'central_lat': GeoCoord(48, 30)}
EU_COORDS = {'min_lat': GeoCoord(36, 0), 'max_lat': GeoCoord(71, 0),
             'min_lon': GeoCoord(-10, 0), 'max_lon': GeoCoord(30, 0),
             'central_long': GeoCoord(10, 0), 'central_lat': GeoCoord(53, 30)}
US_COORDS = {'min_lat': GeoCoord(23, 0), 'max_lat': GeoCoord(55, 0),
             'min_lon': GeoCoord(-126, 0), 'max_lon': GeoCoord(-66, 0),
             'central_long': GeoCoord(-96, 0), 'central_lat': GeoCoord(39, 0)}

SA_COORDS = {'min_lat': GeoCoord(-35, 0), 'max_lat': GeoCoord(-20, 0),
             'min_lon': GeoCoord(15, 0), 'max_lon': GeoCoord(35, 0),
             'central_long': GeoCoord(25, 0), 'central_lat': GeoCoord(-27, 30)}

DEFAULT_SHP_PARAMS = {'face_color': 'none', 'edge_color': 'gray',
                      'border_width': 0.3, 'coast_width': 0.3}
DEFAULT_GRID_PARAMS = {'grid_width': 0.2, 'draw_labels': True}
DEFAULT_MAP_PARAMS = {'size': 18, 'color': 'black',
                      'family': 'Times New Roman',
                      'frame_on': True}
DEFAULT_CBAR_PARAMS = {'size': 16, 'color': 'black',
                       'family': 'Times New Roman',
                       'title_pad': 18.0, 'title': 'dTEC (TECU)'}


PROJECTIONS = (
    'LambertAzimuthalEqualArea',
    'PlateCarree',
    'AlbersEqualArea',
    'AzimuthalEquidistant',
    'EquidistantConic',
    'LambertConformal',
    'LambertCylindrical',
    'Mercator',
    'Miller',
    'Mollweide',
    'ObliqueMercator',
    'Orthographic',
    'Robinson',
    'Sinusoidal',
    'Stereographic',
    'TransverseMercator',
    'InterruptedGoodeHomolosine',
    'RotatedPole',
    'Geostationary',
    'NearsidePerspective',
    'EckertI',
    'EckertII',
    'EckertIII',
    'EckertIV',
    'EckertV',
    'EckertVI',
    'Aitoff',
    'EqualEarth',
    'Gnomonic',
    'Hammer',
    'NorthPolarStereo',
    'SouthPolarStereo',
)


class GeoAxesMap:
    def __init__(self, shp_file_name=None, coords=None,
                 shp_params=None, grid_params=None,
                 label_params=None, is_cbar=False,
                 cbar_params=None):
        self.coords = EU_COORDS.copy() if coords is None else coords.copy()
        self.shp_params = DEFAULT_SHP_PARAMS.copy() if shp_params is None \
            else shp_params.copy()
        self.grid_params = DEFAULT_GRID_PARAMS.copy() if grid_params is None \
            else grid_params.copy()
        self.label_params = DEFAULT_MAP_PARAMS.copy() if label_params is None \
            else label_params.copy()
        self.cbar_params = DEFAULT_CBAR_PARAMS.copy() if cbar_params is None \
            else cbar_params.copy()
        self.shp_file_name = shp_file_name
        self.is_cbar = is_cbar
        self.color_bar = None
        self.figure = None
        self.polygons = []

    def create_figure(self):
        current_crs = ccrs.LambertAzimuthalEqualArea(
            central_longitude=self.coords['central_long'].get_float_degs(),
            central_latitude=self.coords['central_lat'].get_float_degs()
        )
        self.figure = plt.figure()
        ax = plt.axes(projection=current_crs, frame_on=self.label_params['frame_on'])
        self.figure.add_axes(ax)
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
        ax.set_extent([self.coords['min_lon'].get_float_degs(), self.coords['max_lon'].get_float_degs(),
                       self.coords['min_lat'].get_float_degs(), self.coords['max_lat'].get_float_degs()],
                      crs=ccrs.PlateCarree())
        if self.is_cbar:
            norm = plt.Normalize(-1, 1)
            # cmap = colormaps['viridis']
            cmap = colormaps['rainbow']
            self.color_bar = plt.colorbar(mappable=ScalarMappable(norm=norm, cmap=cmap), pad=0.2,
                                          orientation='vertical', alpha=0, ax=ax, shrink=0.95,
                                          fraction=0.05, aspect=30, ticks=[-1, -0.5, 0, 0.5, 1])
            self.color_bar.ax.tick_params(labelsize=self.cbar_params['size'],
                                          labelfontfamily=self.cbar_params['family'],
                                          labelcolor=self.cbar_params['color'])
            self.color_bar.ax.set_title(label=self.cbar_params['title'],
                                        pad=self.cbar_params['title_pad'],
                                        family=self.cbar_params['family'],
                                        fontsize=self.cbar_params['size'],
                                        color=self.cbar_params['color'])
        plt.tight_layout(pad=2)


if __name__ == '__main__':
    g = GeoAxesMap(shp_file_name='geo/cntry02.shp')
    g.create_figure()
    plt.show()

