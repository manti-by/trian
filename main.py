import logging

from shapely.geometry import Point

from trian.app import App

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    """All sizes in centimeters."""
    shell = [
        Point(370, 60),
        Point(670, 60),
        Point(670, 520),
        Point(110, 520),
        Point(110, 330),
        Point(220, 220),
        Point(370, 220),
    ]
    holes = [
        [
            Point(420, 450),
            Point(660, 450),
            Point(660, 510),
            Point(420, 510),
        ],
        [
            Point(420, 290),
            Point(420, 350),
            Point(620, 350),
            Point(620, 290),
        ],
    ]
    socket = Point(270, 220)
    app = App(shell=shell, holes=holes, socket=socket)
