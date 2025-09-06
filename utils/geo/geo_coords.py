class GeoCoord:
    def __init__(self, degs: int, mins: int, secs=0):
        self.degs = degs
        self.mins = mins
        self.secs = secs

    def __eq__(self, other):
        return (self.degs == other.degs) and (self.mins == other.mins) and (self.secs == other.secs)

    def __add__(self, other):
        sum_mins = self.mins
        sum_degs = self.degs
        if self.degs >= 0:
            sum_secs = self.secs + other.secs
            if sum_secs >= 60:
                sum_secs -= 60
                sum_mins += 1
            sum_mins += other.mins
            if sum_mins >= 60:
                sum_mins -= 60
                sum_degs += 1
        else:
            sum_secs = self.secs - other.secs
            if sum_secs < 0:
                sum_secs += 60
                sum_mins -= 1
            sum_mins -= other.mins
            if sum_mins < 0:
                sum_mins += 60
                sum_degs += 1
        sum_degs += other.degs
        return GeoCoord(sum_degs, sum_mins, sum_secs)

    def __sub__(self, other):
        sub_secs = self.secs - other.secs
        sub_mins = self.mins
        sub_degs = self.degs
        if sub_secs < 0:
            sub_secs += 60
            sub_mins -= 1
        sub_mins -= other.mins
        if sub_mins < 0:
            sub_mins += 60
            sub_degs -= 1
        sub_degs -= other.degs
        return GeoCoord(sub_degs, sub_mins, sub_secs)

    def __gt__(self, other):
        if self.degs != other.degs:
            return True if self.degs > other.degs else False
        if self.mins != other.mins:
            return True if self.mins > other.mins else False
        return True if self.secs > other.secs else False

    def __ge__(self, other):
        return (self == other) or (self > other)

    def get_float_degs(self) -> float:
        return self.degs + self.mins / 60. + self.secs / 3600.


COORDS = {
    'UA': {'min_lat': GeoCoord(44, 0), 'max_lat': GeoCoord(52, 30),
           'min_lon': GeoCoord(22, 0), 'max_lon': GeoCoord(40, 30),
           'central_long': GeoCoord(31, 30), 'central_lat': GeoCoord(48, 30)},
    'EU': {'min_lat': GeoCoord(36, 0), 'max_lat': GeoCoord(71, 0),
           'min_lon': GeoCoord(-10, 0), 'max_lon': GeoCoord(30, 0),
           'central_long': GeoCoord(10, 0), 'central_lat': GeoCoord(53, 30)},
    'US': {'min_lat': GeoCoord(23, 0), 'max_lat': GeoCoord(55, 0),
           'min_lon': GeoCoord(-126, 0), 'max_lon': GeoCoord(-66, 0),
           'central_long': GeoCoord(-96, 0), 'central_lat': GeoCoord(39, 0)},
    'SA': {'min_lat': GeoCoord(-35, 0), 'max_lat': GeoCoord(-20, 0),
           'min_lon': GeoCoord(15, 0), 'max_lon': GeoCoord(35, 0),
           'central_long': GeoCoord(25, 0), 'central_lat': GeoCoord(-27, 30)}
}
