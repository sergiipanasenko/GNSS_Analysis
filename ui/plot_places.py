import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import numpy as np
import pandas as pd


def plot_towns(ax, lats, lons, resolution='10m', transform=ccrs.PlateCarree(), zorder=3):
    """
    This function will download the 'populated_places' shapefile from
    NaturalEarth, trim the shapefile based on the limits of the provided
    lat & long coords, and then plot the locations and names of the towns
    on a given GeoAxes.
    
    ax = a pyplot axes object
    lats = latitudes, as an xarray object
    lons = longitudes, as an xarray object
    resolution= str. either high res:'10m' or low res: '50m'
    transform = a cartopy crs object
    """
    # get town locations
    shp_fn = shpreader.natural_earth(resolution=resolution,
                                     category='cultural',
                                     name='populated_places')
    shp = shpreader.Reader(shp_fn)

    # get town names
    towns = shp.records()
    names_en = []
    town_lons = []
    town_lats = []
    for town in towns:
        if town.attributes['POP_MAX'] > 500000 and town.attributes['SOV0NAME'] != 'Russia':
            names_en.append(town.attributes['NAME_EN'])
            town_lons.append(town.attributes['LONGITUDE'])
            town_lats.append(town.attributes['LATITUDE'])

    # create data frame and index by the region of the plot
    all_towns = pd.DataFrame({'names_en': names_en, 'x': town_lons, 'y': town_lats})
    region_towns = all_towns[(all_towns.y < np.max(lats)) & (all_towns.y > np.min(lats))
                             & (all_towns.x > np.min(lons)) & (all_towns.x < np.max(lons))]

    # plot the locations and labels of the towns in the region
    ax.scatter(region_towns.x.values, region_towns.y.values,
               c='blue', marker='.', transform=transform, zorder=zorder)
    # this is a work-around to transform xy coords in ax.annotate
    transform_mpl = ccrs.PlateCarree()._as_mpl_transform(ax)
    for i, txt in enumerate(region_towns.names_en):
        ax.annotate(txt, (region_towns.x.values[i] + 0.1, region_towns.y.values[i] + 0.1),
                    xycoords=transform_mpl, size=14, family='Times New Roman')
