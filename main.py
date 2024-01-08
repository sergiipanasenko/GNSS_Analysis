import pandas as pd

LAT = 43
LON = -72

if __name__ == '__main__':
    data = pd.read_csv('gps191228g.002.hdf5.txt', sep = '\s+')
    data = data.query('GDLAT  == @LAT & GLON == @LON')
    data['UT'] = data['HOUR'] + data['MIN']/60 + data['SEC']/3600
    data1 = data.loc[:, ['UT', 'TEC', 'DTEC']]
    writePath = 'gps191228.dat'
    with open(writePath, 'w') as f:
        f.write(
            data1.to_string(header=False, index=False, float_format="%.8f")
        )
    print(data1.to_string(header=False, index=False))

