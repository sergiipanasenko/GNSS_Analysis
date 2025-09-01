import datetime as dt


def convert_to_hours(tt: dt.datetime) -> float:
    return tt.hour + tt.minute / 60. + tt.second / 3600.


def convert_to_seconds(tt: dt.datetime) -> int:
    return tt.hour * 3600 + tt.minute * 60 + tt.second


def timedelta_to_time(tt: dt.timedelta) -> dt.time:
    total_sec = tt.total_seconds()
    hours = int(total_sec // 3600)
    minutes = int((total_sec % 3600) // 60)
    seconds = tt.seconds
    return dt.time(hour=hours, minute=minutes, second=seconds)


def time_to_timedelta(tt: dt.time) -> dt.timedelta:
    return dt.timedelta(hours=tt.hour, minutes=tt.minute, seconds=tt.second)

