class GeoCoord:
    def __init__(self, degs: int, mins: int, secs=0):
        self.degs = degs
        self.mins = mins
        self.secs = secs

    def get_float_degs(self) -> float:
        return self.degs + self.mins / 60. + self.secs / 3600.
