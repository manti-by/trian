from shapely.geometry import Point

from trian.app import App


if __name__ == "__main__":
    """All sizes in centimeters."""
    points = [
        Point(370, 110),
        Point(630, 110),
        Point(630, 520),
        Point(110, 520),
        Point(110, 220),
        Point(370, 220),
    ]
    socket = Point(150, 220)
    app = App(points=points, socket=socket)
