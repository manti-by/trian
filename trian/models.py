import tkinter as tk

from shapely.geometry import Point, Polygon


class Shape:
    fill = ""
    outline = "black"
    width = "2"

    def __init__(self, points: list[Point]):
        self.points = points
        self.polygon = Polygon(points)

    @property
    def area(self) -> int:
        return self.polygon.area

    @property
    def length(self) -> int:
        return self.polygon.bounds[2] - self.polygon.bounds[0]

    def draw(self, canvas: tk.Canvas):
        canvas.create_polygon(
            [(p.x, p.y) for p in self.points],
            fill=self.fill,
            outline=self.outline,
            width=self.width,
        )


class Mat(Shape):
    fill = "green"
    outline = "black"
    width = "1"


class Wire(Shape):
    fill = "red"
    outline = "red"
    width = "1"
