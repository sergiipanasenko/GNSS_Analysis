import matplotlib.pyplot as plt
from gnss import TIME_FORMAT
import datetime as dt


# file_name = 'Sites.txt'
file_name1 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\test\EU\2024\2024-09-09\3600\Map\MSTID_time_domain\5-30min\14d30m_0d45m_lon_50d0m_0d45m_lat_av.txt"
file_name2 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\test\EU\2024\2024-09-09\3600\Map\MSTID\5-30min\14d30m_0d45m_lon_50d0m_0d45m_lat_av.txt"
file_name3 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\test\EU\2024\2024-09-09\3600\Map\MSTID\All\14d30m_0d45m_lon_50d0m_0d45m_lat_av.txt"
file_names = (file_name1, file_name2)
for file_name in file_names:
    time = []
    data = []
    with open(file_name, mode='r') as file:
        for line in file:
            raw_data = line.split('\t')
            time.append(dt.datetime.strptime(raw_data[0], TIME_FORMAT))
            data.append(float(raw_data[1]))
    plt.plot(time, data)
    plt.gca().set_xlim([dt.datetime(2024, 9, 9,0), dt.datetime(2024, 9, 9,23)])
plt.show()



