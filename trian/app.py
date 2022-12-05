import tkinter as tk

from shapely.geometry import Point

from trian.models import Shape
from trian.processor import Processor


class App:

    wire_size = 2
    mat_size = 50

    def __init__(self, points: list[Point], socket: Point) -> None:
        self.window = None
        self.canvas = None
        self.room = None
        self.result = None

        self.points = points
        self.socket = socket

        self.create_window()
        self.draw_room()
        self.draw_tiles()

        if self.window is not None:
            self.window.mainloop()

    def create_window(self):
        self.window = tk.Tk()
        self.window.title("Canvas")
        self.window.geometry("800x600")

        self.canvas = tk.Canvas(self.window, width=800, height=600)
        self.canvas.pack()

    def draw_room(self):
        # Room walls
        self.room = Shape(points=self.points)
        self.room.draw(canvas=self.canvas)

        # Socket position
        socket_size = 10 / 2
        self.canvas.create_oval(
            self.socket.x - socket_size,
            self.socket.y - socket_size,
            self.socket.x + socket_size,
            self.socket.y + socket_size,
            fill="red",
        )

    def draw_tiles(self):
        processor = Processor(
            points=self.points, wire_size=self.wire_size, mat_size=self.mat_size
        )
        self.result = processor.calculate()
        for shape in self.result:
            shape.draw(canvas=self.canvas)
