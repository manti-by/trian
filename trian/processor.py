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

    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"

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

        self.field = None
        self.generate_field()

        self.prev_x, self.prev_y = None, None
        self.direction_x, self.direction_y = self.FORWARD, self.FORWARD
        self.current_direction = self.HORIZONTAL

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

    def choose_start_point(self) -> Point:
        # Initial position is the closes position to top/left corner
        # TODO: Update to the socket position
        start_point = self.points[0]
        for point in self.points:
            if point.x <= start_point.x and point.y <= start_point.y:
                start_point = point
        return start_point

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

    @property
    def is_horizontal_direction(self) -> bool:
        return self.current_direction == self.HORIZONTAL

    @property
    def is_forward_x(self) -> bool:
        return self.direction_x == self.FORWARD

    @property
    def is_forward_y(self) -> bool:
        return self.direction_y == self.FORWARD

    def choose_next_position(self) -> tuple[int, int]:
        if self.prev_x is None and self.prev_y is None:
            point = self.choose_start_point()
            self.prev_x = int(point.x) + self.precision
            self.prev_y = int(point.y) + self.precision
            return self.prev_x, self.prev_y

        if self.is_horizontal_direction:
            # Forward horizontal rules
            if self.is_forward_x:
                # Check room bounds (fast)
                # Then try to restrict moving outside the room
                if (
                    self.prev_x < self.max_x - self.precision and
                    self.field[self.prev_x + self.precision][self.prev_y] != self.NULL
                ):
                    self.prev_x += self.precision
                # if there is no horizontal way then move vertically
                else:
                    self.direction_x = self.BACKWARD
                    self.current_direction = self.VERTICAL
            else:
                # Backward move direction
                if (
                    self.prev_x > self.min_x + self.precision and
                    self.field[self.prev_x - self.precision][self.prev_y] != self.NULL
                ):
                    self.prev_x -= self.precision
                else:
                    self.direction_x = self.FORWARD
                    self.current_direction = self.VERTICAL

        # The same rules but for vertical direction
        else:
            if self.is_forward_y:
                if (
                    self.prev_y < self.max_y - self.precision and
                    self.field[self.prev_x][self.prev_y + self.precision] != self.NULL
                ):
                    self.prev_y += self.precision
                else:
                    self.current_direction = self.HORIZONTAL
            else:
                if (
                    self.prev_y > self.min_y + self.precision and
                    self.field[self.prev_x][self.prev_y - self.precision] != self.NULL
                ):
                    self.prev_y -= self.precision
                else:
                    self.current_direction = self.HORIZONTAL

        return self.prev_x, self.prev_y

    def calculate(self) -> Iterable[Shape]:
        is_loop = 0
        loop_x, loop_y = None, None
        iterations = (self.max_y - self.min_y) * (self.max_x - self.min_x)
        while iterations:
            iterations -= 1
            x, y = self.choose_next_position()
            logger.info(f"{x}, {y}")

            # Try to detect a loop
            if loop_x == x and loop_y == y:
                is_loop += 1
                if is_loop > 10:
                    break
            loop_x, loop_y = x, y

            # Skip already filled positions
            if self.field[x][y] != self.FREE:
                continue

            # Flip shape if direction is backward
            flip_x = 1 if self.is_forward_x else -1

            mat = Mat(
                points=[
                    Point(x, y),
                    Point(x + self.mat_width * flip_x, y),
                    Point(x + self.mat_width * flip_x, y + self.mat_height),
                    Point(x, y + self.mat_height),
                ]
            )
            # Try to insert a mat
            if self.is_shape_can_be_added(shape=mat):
                self.current_direction = self.HORIZONTAL
                if flip_x == -1:
                    self.direction_x = self.BACKWARD
                    self.update_field(x - self.mat_width, y, self.mat_width, self.mat_height)
                else:
                    self.direction_x = self.FORWARD
                    self.update_field(x, y, self.mat_width, self.mat_height)
                logger.info("Add mat")
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
            # Otherwise try to insert a wire
            if self.is_shape_can_be_added(shape=wire):
                self.update_field(x, y, self.wire_size, self.wire_size)
                self.current_direction = self.VERTICAL
                self.direction_x = self.BACKWARD
                logger.info("Add wire")
                yield wire
                continue
