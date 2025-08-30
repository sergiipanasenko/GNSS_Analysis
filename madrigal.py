import madrigalWeb.madrigalWeb as madrigal
import datetime as dt

SITE = 'http://cedar.openmadrigal.org'
USER_FULLNAME = 'Sergii Panasenko'
USER_EMAIL = 'sergii.v.panasenko@gmail.com'
USER_AFFILIATION = 'None'
CATEGORY = 'Distributed Ground Based Satellite Receivers'
INSTRUMENT = 'World-wide GNSS Receiver Network'
INSTR_CODE = 8000


def download_hdf5(date: dt.date, file_name: str, file_destination: str):
    madrigal_data = madrigal.MadrigalData(SITE)
    full_input_file = ''
    experiments = madrigal_data.getExperiments(INSTR_CODE, date.year, date.month, date.day, 0, 0, 1,
                                               date.year, date.month, date.day, 23, 59, 59)
    for exp in experiments:
        file_list = madrigal_data.getExperimentFiles(exp.id)
        for file in file_list:
            if str(file.name).endswith(file_name):
                full_input_file = file.name
                break
    madrigal_data.downloadFile(full_input_file, file_destination,
                               USER_FULLNAME, USER_EMAIL, USER_AFFILIATION, format="hdf5")


if __name__ == '__main__':
    file_name = "los_20231022.001.h5"
    file_destination = f"results/test/{file_name}"
    date = dt.date(2023, 10, 22)
    print(f"{dt.datetime.now()}: Start downloading.")
    download_hdf5(date, file_name, file_destination)
    print(f"{dt.datetime.now()}: End downloading.")
