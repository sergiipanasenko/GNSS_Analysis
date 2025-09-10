import matplotlib.pyplot as plt
from gnss import TIME_FORMAT
import datetime as dt


# file_name = 'Sites.txt'
file_name1 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\test\EU\2023\2023-04-01\7200\LSTID_TIME\1\10d0m_0d45m_lon_48d0m_0d45m_lat_av.txt"
file_name2 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\test\EU\2023\2023-04-01\7200\LSTID_TIME\1\10d0m_0d45m_lon_52d0m_0d45m_lat_av.txt"
file_names = (file_name2, file_name1)
for file_name in file_names:
    time = []
    data = []
    with open(file_name, mode='r') as file:
        for line in file:
            raw_data = line.split('\t')
            time.append(dt.datetime.strptime(raw_data[0], TIME_FORMAT))
            data.append(float(raw_data[1]))
    plt.plot(time, data)
plt.show()



