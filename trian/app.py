import tkinter as tk

from shapely.geometry import Point

from trian.models import Shape
from trian.processor import Processor


class App:

    wire_size = 4
    mat_width = 10
    mat_height = 50
    precision = 2

    def __init__(self, points: list[Point], socket: Point) -> None:
        self.window = None
        self.canvas = None
        self.room = None
        self.result = None

        self.redraw_button = None
        self.wire_size_input = None
        self.mat_width_input = None
        self.mat_height_input = None
        self.precision_input = None
        self.flip_xy = None
        self.flip_xy_choice = None
        self.result_label = None

        self.points = points
        self.socket = socket

        self.create_window()
        self.draw_room()

        if self.window is not None:
            self.window.mainloop()

    def create_window(self):
        self.window = tk.Tk()
        self.window.title("Canvas")
        self.window.geometry("850x750")

        self.canvas = tk.Canvas(self.window, width=700, height=600)
        self.canvas.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2, columnspan=3)

        label = tk.Label(self.window, text="Wire size")
        label.grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)

        self.wire_size_input = tk.Entry(self.window)
        self.wire_size_input.insert(0, str(self.wire_size))
        self.wire_size_input.grid(row=2, column=0, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Mat width")
        label.grid(row=1, column=1, sticky=tk.W, padx=2, pady=2)

        self.mat_width_input = tk.Entry(self.window)
        self.mat_width_input.insert(0, str(self.mat_width))
        self.mat_width_input.grid(row=2, column=1, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Mat height")
        label.grid(row=1, column=2, sticky=tk.W, pady=2)

        self.mat_height_input = tk.Entry(self.window)
        self.mat_height_input.insert(0, str(self.mat_height))
        self.mat_height_input.grid(row=2, column=2, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Precision")
        label.grid(row=3, column=0, sticky=tk.W, padx=2, pady=2)

        self.precision_input = tk.Entry(self.window)
        self.precision_input.insert(0, str(self.precision))
        self.precision_input.grid(row=4, column=0, sticky=tk.W, padx=2, pady=2)

        self.flip_xy = tk.BooleanVar()
        self.flip_xy_choice = tk.Checkbutton(
            self.window,
            text="Flip XY",
            variable=self.flip_xy,
            onvalue=True,
            offvalue=False,
        )
        self.flip_xy_choice.grid(row=4, column=1, sticky=tk.W, padx=2, pady=2)

        self.redraw_button = tk.Button(self.window, text="Calculate", command=self.draw)
        self.redraw_button.grid(row=5, column=0, sticky=tk.W, padx=2, pady=2)

        self.result_label = tk.Label(self.window, text="")
        self.result_label.grid(row=5, column=1, sticky=tk.W, padx=2, pady=2)

    def draw(self):
        self.canvas.delete("all")
        self.draw_room()
        self.draw_tiles()

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
        mat_width = int(self.mat_width_input.get())
        mat_height = int(self.mat_height_input.get())
        if self.flip_xy.get():
            mat_height = int(self.mat_width_input.get())
            mat_width = int(self.mat_height_input.get())
        processor = Processor(
            points=self.points,
            mat_width=mat_width,
            mat_height=mat_height,
            wire_size=int(self.wire_size_input.get()),
            precision=int(self.precision_input.get()),
            flip_xy=self.flip_xy.get(),
        )
        total_area = 0
        for shape in processor.calculate():
            shape.draw(canvas=self.canvas)
            self.window.update()
            total_area += shape.area
        result = f"Fill size: {total_area / self.room.area:.2f}"
        self.result_label.config(text=result)
