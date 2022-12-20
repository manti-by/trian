import logging

from shapely.geometry import Point

from trian.app import App

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    """All sizes in centimeters."""
    points = [
        Point(370, 60),
        Point(670, 60),
        Point(670, 520),
        Point(110, 520),
        # Point(110, 220),
        Point(110, 330),
        Point(220, 220),
        Point(370, 220),
    ]
    socket = Point(370, 110)
    #socket = Point(270, 220)
    app = App(points=points, socket=socket)
