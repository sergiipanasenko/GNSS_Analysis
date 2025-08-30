import datetime as dt


def convert_to_hours(tt: dt.datetime) -> float:
    return tt.hour + tt.minute / 60. + tt.second / 3600.


def convert_to_seconds(tt: dt.datetime) -> int:
    return tt.hour * 3600 + tt.minute * 60 + tt.second
