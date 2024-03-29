import tkinter as tk
from typing import Any

from shapely.geometry import Point

from trian.models import Shape
from trian.generator import Generator


class App:

    wire_width = 4
    wire_height = 1
    mat_width = 10
    mat_height = 50
    precision = 1

    def __init__(self, points: list[Point], socket: Point) -> None:
        self.canvas = None
        self.room = None
        self.result = None

        self.root = tk.Tk()
        self.root.title("Canvas")
        self.root.geometry("800x750")

        self.window = tk.Frame(self.root)
        self.window.grid(padx=7, pady=7)

        self.canvas = tk.Canvas(self.window, width=780, height=580, background="white")
        self.canvas.bind("<Enter>", self.update_coords)
        self.canvas.bind("<Motion>", self.update_coords)
        self.coords_label = self.canvas.create_text(10, 10, text="", anchor="nw")
        self.canvas.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2, columnspan=4)

        label = tk.Label(self.window, text="Wire width")
        label.grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)

        self.wire_width_input = tk.Entry(self.window)
        self.wire_width_input.insert(0, str(self.wire_width))
        self.wire_width_input.grid(row=2, column=0, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Wire height")
        label.grid(row=1, column=1, sticky=tk.W, padx=2, pady=2)

        self.wire_height_input = tk.Entry(self.window)
        self.wire_height_input.insert(0, str(self.wire_height))
        self.wire_height_input.grid(row=2, column=1, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Mat width")
        label.grid(row=1, column=2, sticky=tk.W, padx=2, pady=2)

        self.mat_width_input = tk.Entry(self.window)
        self.mat_width_input.insert(0, str(self.mat_width))
        self.mat_width_input.grid(row=2, column=2, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Mat height")
        label.grid(row=1, column=3, sticky=tk.W, pady=2)

        self.mat_height_input = tk.Entry(self.window)
        self.mat_height_input.insert(0, str(self.mat_height))
        self.mat_height_input.grid(row=2, column=3, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Precision")
        label.grid(row=3, column=0, sticky=tk.W, padx=2, pady=2)

        self.precision_input = tk.Entry(self.window)
        self.precision_input.insert(0, str(self.precision))
        self.precision_input.grid(row=4, column=0, sticky=tk.W, padx=2, pady=2)

        self.reverse_x = tk.BooleanVar()
        self.reverse_x_choice = tk.Checkbutton(
            self.window,
            text="Reverse X",
            variable=self.reverse_x,
            onvalue=True,
            offvalue=False,
        )
        self.reverse_x_choice.grid(row=4, column=1, sticky=tk.W, padx=0, pady=2)

        self.reverse_y = tk.BooleanVar()
        self.reverse_y_choice = tk.Checkbutton(
            self.window,
            text="Reverse Y",
            variable=self.reverse_y,
            onvalue=True,
            offvalue=False,
        )
        self.reverse_y_choice.grid(row=4, column=2, sticky=tk.W, padx=0, pady=2)

        self.prioritize_y = tk.BooleanVar()
        self.reverse_x_choice = tk.Checkbutton(
            self.window,
            text="Prioritize Y",
            variable=self.prioritize_y,
            onvalue=True,
            offvalue=False,
        )
        self.reverse_x_choice.grid(row=4, column=3, sticky=tk.W, padx=0, pady=2)

        self.redraw_button = tk.Button(self.window, text="Calculate", command=self.draw)
        self.redraw_button.grid(row=5, column=0, sticky=tk.W, padx=0, pady=5)

        self.result_label = tk.Label(self.window, text="")
        self.result_label.grid(row=5, column=1, sticky=tk.W, padx=2, pady=5)

        self.points = points
        self.socket = socket

        self.draw_room()

        if self.window is not None:
            self.window.mainloop()

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

    def get_params(self) -> dict[str, Any]:
        return {
            "socket": self.socket,
            "points": self.points,
            "mat_width": int(self.mat_width_input.get()),
            "mat_height": int(self.mat_height_input.get()),
            "wire_width": int(self.wire_width_input.get()),
            "wire_height": int(self.wire_height_input.get()),
            "precision": int(self.precision_input.get()),
            "reverse_x": bool(self.reverse_x.get()),
            "reverse_y": bool(self.reverse_y.get()),
            "prioritize_y": bool(self.prioritize_y.get()),
        }

    def draw_tiles(self):
        total_area = 0
        total_length = 0
        field = None
        for i in range(3):  # Up to 3 mats per room
            self.result_label.config(text=f"Processing {i + 1}th cycle")
            self.window.update()

            generator = Generator(**self.get_params(), field=field)
            for shape in generator.calculate():
                shape.draw(canvas=self.canvas)
                self.window.update()

                total_area += shape.area
                total_length += int(shape.length)

            field = generator.field

        ratio = total_area / self.room.area * 100
        result = f"Fill ratio: {ratio:.2f}%, length: {total_length / 100:.2f}m"
        self.result_label.config(text=result)

    def update_coords(self, event: tk.Event):
        self.canvas.itemconfigure(self.coords_label, text=f"{event.x}, {event.y}")
