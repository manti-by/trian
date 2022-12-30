import random
import tkinter as tk
from typing import Any, Iterable

from shapely.geometry import Point

from trian.const import MAX_WIRE_LENGTH, MAX_MATS_PER_ROOM
from trian.models import Shape
from trian.router import Router


class App:

    wire_radius = 8
    mat_width = 8
    precision = 1

    def __init__(
        self, shell: list[Point], holes: list[list[Point]], socket: Point
    ) -> None:
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

        label = tk.Label(self.window, text="Wire radius")
        label.grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)

        self.wire_radius_input = tk.Entry(self.window)
        self.wire_radius_input.insert(0, str(self.wire_radius))
        self.wire_radius_input.grid(row=2, column=0, sticky=tk.W, padx=2, pady=2)

        label = tk.Label(self.window, text="Mat width")
        label.grid(row=1, column=2, sticky=tk.W, padx=2, pady=2)

        self.mat_width_input = tk.Entry(self.window)
        self.mat_width_input.insert(0, str(self.mat_width))
        self.mat_width_input.grid(row=2, column=2, sticky=tk.W, padx=2, pady=2)

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
        self.flip_xy_choice.grid(row=4, column=1, sticky=tk.W, padx=0, pady=2)

        self.redraw_button = tk.Button(self.window, text="Calculate", command=self.draw)
        self.redraw_button.grid(row=5, column=0, sticky=tk.W, padx=0, pady=5)

        self.result_label = tk.Label(self.window, text="")
        self.result_label.grid(row=5, column=1, sticky=tk.W, padx=2, pady=5)

        self.shell = shell
        self.holes = holes
        self.socket = socket

        self.attempt = 0

        self.draw_room()

        if self.window is not None:
            self.window.mainloop()

    def get_color(self) -> str:
        if self.attempt % 3 == 1:
            color = "blue"
        elif self.attempt % 3 == 2:
            color = "yellow"
        else:
            color = "green"
        self.attempt += 1
        return color

    def draw(self):
        self.canvas.delete("all")
        self.draw_room()
        self.draw_tiles()

    def draw_room(self):
        # Room walls
        self.room = Shape(points=self.shell)
        self.room.draw(canvas=self.canvas)

        # Cold spots
        if self.holes:
            for hole in self.holes:
                self.room = Shape(points=hole)
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
        def roll_colors() -> Iterable[str]:
            while True:
                yield "green"
                yield "blue"
                yield "yellow"
        return {
            "socket": self.socket,
            "shell": self.shell,
            "holes": self.holes,
            "wire_radius": int(self.wire_radius_input.get()),
            "mat_width": int(self.mat_width_input.get()),
            "mat_fill": self.get_color(),
            "precision": int(self.precision_input.get()),
            "flip_xy": bool(self.flip_xy.get()),
        }

    def draw_tiles(self):
        total_area = 0
        total_length = 0
        field = None
        for i in range(MAX_MATS_PER_ROOM):
            self.result_label.config(text=f"Processing {i + 1}th cycle")
            self.window.update()

            current_length = 0
            router = Router(**self.get_params(), field=field)
            for shape in router.next():
                shape.draw(canvas=self.canvas)
                self.window.update()

                total_area += shape.area
                total_length += int(shape.length)

                current_length += int(shape.length)
                if current_length > MAX_WIRE_LENGTH:
                    break
            field = router.field

        ratio = total_area / self.room.area * 100
        result = f"Fill ratio: {ratio:.2f}%, length: {total_length / 100:.2f}m"
        self.result_label.config(text=result)

    def update_coords(self, event: tk.Event):
        self.canvas.itemconfigure(self.coords_label, text=f"{event.x}, {event.y}")
