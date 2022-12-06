import logging
from collections import defaultdict
from typing import Iterable

from shapely.geometry import Point, Polygon

from trian.models import Mat, Shape, Wire

logger = logging.getLogger(__name__)


class Processor:

    EDGE = "EDGE"
    BODY = "BODY"

    FREE = "FREE"
    NULL = "NULL"

    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"

    def __init__(
        self,
        points: list[Point],
        wire_size: int,
        mat_width: int,
        mat_height: int,
        precision: int,
        flip_xy: bool,
    ):
        self.points = points
        self.polygon = Polygon(self.points)

        self.wire_size = wire_size
        self.mat_height = mat_height
        self.mat_width = mat_width
        self.precision = precision
        self.flip_xy = flip_xy

        self.min_x, self.max_x = None, None
        self.min_y, self.max_y = None, None
        self.calculate_bounds()

        self.prev_x, self.prev_y = self.min_x, self.min_y
        self.direction_x, self.direction_y = self.FORWARD, self.FORWARD
        self.is_mat_added, self.is_wire_added = False, False

        self.field = None
        self.generate_field()

    def calculate_bounds(self):
        self.min_x, self.max_x = int(min(p.x for p in self.points)), int(
            max(p.x for p in self.points)
        )
        self.min_y, self.max_y = int(min(p.y for p in self.points)), int(
            max(p.y for p in self.points)
        )

    def generate_field(self):
        self.field = defaultdict(lambda: defaultdict(str))
        for x in range(self.min_x, self.max_x, self.precision):
            for y in range(self.min_y, self.max_y, self.precision):
                self.field[x][y] = (
                    self.FREE if self.polygon.contains(Point(x, y)) else self.NULL
                )

    def is_shape_can_be_added(self, shape: Mat | Wire) -> bool:
        for point in shape.points:
            if self.field[point.x][point.y] not in (self.FREE,):
                return False
        return True

    def update_field(self, x: int, y: int, width: int, height: int):
        for r_x in range(x, x + width):
            for r_y in range(y, y + height):
                is_edge_location = any(
                    (r_x == x, r_x == x + width, r_y == y, r_y == y + height)
                )
                self.field[r_x][r_y] = self.EDGE if is_edge_location else self.BODY
        self.prev_x, self.prev_y = x + width, y

    def choose_next_position(self):
        if self.prev_x < self.max_x - self.precision:
            self.prev_x += self.precision if self.direction_x == self.FORWARD else -1 * self.precision

        else:
            self.prev_x = self.min_x
            self.prev_y += self.precision if self.direction_y == self.FORWARD else -1 * self.precision

        return self.prev_x, self.prev_y

    def calculate(self) -> Iterable[Shape]:
        iterations = (self.max_y - self.min_y) * (self.max_x - self.min_x)
        while iterations:
            iterations -= 1
            x, y = self.choose_next_position()
            logger.info(f"{x}, {y}")

            self.is_mat_added = False
            self.is_wire_added = False
            if not self.field[x][y] or self.field[x][y] == self.NULL:
                self.prev_x, self.prev_y = x, y
                continue

            mat = Mat(
                points=[
                    Point(x, y),
                    Point(x + self.mat_width, y),
                    Point(x + self.mat_width, y + self.mat_height),
                    Point(x, y + self.mat_height),
                ]
            )
            if self.is_shape_can_be_added(shape=mat):
                self.update_field(x, y, self.mat_width, self.mat_height)
                self.is_mat_added = True
                yield mat
                continue

            wire = Wire(
                points=[
                    Point(x, y),
                    Point(x + self.wire_size, y),
                    Point(x + self.wire_size, y + self.wire_size),
                    Point(x, y + self.wire_size),
                ]
            )
            if self.is_shape_can_be_added(shape=wire):
                self.update_field(x, y, self.wire_size, self.wire_size)
                self.is_wire_added = True
                yield wire
                continue
