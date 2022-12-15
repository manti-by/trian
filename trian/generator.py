import logging
from collections import defaultdict

from typing import Iterable

from shapely.geometry import Point, Polygon

from trian.models import Mat, Shape, Wire

logger = logging.getLogger(__name__)


class Generator:

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
        socket: Point,
        points: list[Point],
        mat_width: int,
        mat_height: int,
        wire_width: int,
        wire_height: int,
        precision: int,
        reverse_x: bool,
        reverse_y: bool,
        prioritize_y: bool,
        field: dict[int, dict[int, str]] = None,
    ):
        """Init the class with values from the UI."""
        self.socket = socket
        self.points = points
        self.polygon = Polygon(self.points)

        self.mat_height = mat_height
        self.mat_width = mat_width
        self.wire_width = wire_width
        self.wire_height = wire_height
        self.precision = precision

        self.min_x, self.max_x, self.min_y, self.max_y = self.get_points_bounds(
            points=self.points
        )

        self.field = field
        self.generate_field()

        self.prev_x, self.prev_y = None, None
        self.direction_x = self.BACKWARD if reverse_x else self.FORWARD
        self.direction_y = self.BACKWARD if reverse_y else self.FORWARD
        self.current_direction = self.VERTICAL if prioritize_y else self.HORIZONTAL

    @property
    def is_horizontal_direction(self) -> bool:
        return self.current_direction == self.HORIZONTAL

    @property
    def is_vertical_direction(self) -> bool:
        return self.current_direction == self.VERTICAL

    @property
    def is_forward_x(self) -> bool:
        return self.direction_x == self.FORWARD

    @property
    def is_forward_y(self) -> bool:
        return self.direction_y == self.FORWARD

    @staticmethod
    def get_points_bounds(points: list[Point]) -> tuple[int, int, int, int]:
        """Calculate the polygon bounding edges."""
        min_x, max_x = int(min(p.x for p in points)), int(max(p.x for p in points))
        min_y, max_y = int(min(p.y for p in points)), int(max(p.y for p in points))
        return min_x, max_x, min_y, max_y

    def calculate_field_bounds(self):
        """Calculate the polygon bounding edges."""
        self.min_x, self.max_x, self.min_y, self.max_y = self.get_points_bounds(
            points=self.points
        )

    def generate_field(self):
        """Generate all points states inside the main polygon."""
        if self.field is None:
            self.field = defaultdict(lambda: defaultdict(str))
            for x in range(self.min_x, self.max_x, self.precision):
                for y in range(self.min_y, self.max_y, self.precision):
                    self.field[x][y] = (
                        self.FREE if self.polygon.contains(Point(x, y)) else self.NULL
                    )

    def get_closest_vertex(self, point: Point) -> Point:
        """Find the closest vertex to the point position."""
        closest_vertex = self.points[0]
        closest_distance = point.distance(closest_vertex)
        for p in self.points[1:]:
            # Check a free point around current vertex
            is_field_cell_free = any(
                (
                    self.field[p.x + self.precision][p.y + self.precision] == self.FREE,
                    self.field[p.x + self.precision][p.y - self.precision] == self.FREE,
                    self.field[p.x - self.precision][p.y + self.precision] == self.FREE,
                    self.field[p.x - self.precision][p.y - self.precision] == self.FREE,
                )
            )
            current_distance = point.distance(p)
            if current_distance < closest_distance and is_field_cell_free:
                closest_vertex = p
                closest_distance = current_distance
        return closest_vertex

    def start_point(self) -> Point:
        """Start from a vertex closest to the socket position."""
        if self.socket:
            return self.get_closest_vertex(self.socket)

        # Otherwise initial position is the closes position to top/left corner
        start_point = self.points[0]
        for point in self.points:
            if point.x <= start_point.x and point.y <= start_point.y:
                start_point = point
        return start_point

    def is_shape_can_be_added(self, points: list[Point]) -> bool:
        """All points should be free in the field."""
        for point in points:
            if self.field[point.x][point.y] not in (self.FREE,):
                return False
        return True

    def update_field(self, points: list[Point]):
        """Fill in all points are covered by a new shape."""
        min_x, max_x, min_y, max_y = self.get_points_bounds(points=points)
        for r_x in range(min_x, max_x):
            for r_y in range(min_y, max_y):
                is_edge_location = any(
                    (r_x == min_x, r_x == max_x, r_y == min_y, r_y == max_y)
                )
                self.field[r_x][r_y] = self.EDGE if is_edge_location else self.BODY

    def choose_next_x(self) -> int:
        """Horizontal direction rules."""
        if self.is_forward_x:  # Forward
            # Check room bounds (fast)
            # Then try to restrict moving outside the room
            if (
                self.prev_x < self.max_x - self.precision
                and self.field[self.prev_x + self.precision][self.prev_y] != self.NULL
            ):
                self.prev_x += self.precision
            # if there is no horizontal way then move vertically
            else:
                self.direction_x = self.BACKWARD
                self.current_direction = self.VERTICAL
        else:  # Backward
            if (
                self.prev_x > self.min_x + self.precision
                and self.field[self.prev_x - self.precision][self.prev_y] != self.NULL
            ):
                self.prev_x -= self.precision
            else:
                self.direction_x = self.FORWARD
                self.current_direction = self.VERTICAL
        return self.prev_x

    def choose_next_y(self):
        """Vertical direction rules."""
        if self.is_forward_y:
            if (
                self.prev_y < self.max_y - self.precision
                and self.field[self.prev_x][self.prev_y + self.precision] != self.NULL
            ):
                self.prev_y += self.precision
            else:
                self.current_direction = self.HORIZONTAL
        else:
            if (
                self.prev_y > self.min_y + self.precision
                and self.field[self.prev_x][self.prev_y - self.precision] != self.NULL
            ):
                self.prev_y -= self.precision
            else:
                self.current_direction = self.HORIZONTAL
        return self.prev_y

    def choose_next_position(self) -> tuple[int, int]:
        """The main part of the generator that chooses a next move."""
        if self.prev_x is None and self.prev_y is None:
            point = self.start_point()
            self.prev_x = int(point.x) + self.precision
            self.prev_y = int(point.y) + self.precision
            return self.prev_x, self.prev_y

        if self.is_horizontal_direction:
            self.prev_x = self.choose_next_x()
        else:
            self.prev_y = self.choose_next_y()

        return self.prev_x, self.prev_y

    def get_shape_points(
        self, x: int, y: int, width: int, height: int
    ) -> list[Point, Point, Point, Point]:
        """Flip shape if direction is changed."""
        flip_x = 1 if self.is_forward_x else -1
        flip_y = 1 if self.is_forward_y else -1

        offset_x = 0 if self.is_forward_x else -1 * self.precision
        offset_y = 0 if self.is_forward_y else -1 * self.precision

        return [
            Point(x + offset_x, y + offset_y),
            Point(x + offset_x + width * flip_x, y + offset_y),
            Point(x + offset_x + width * flip_x, y + offset_y + height * flip_y),
            Point(x + offset_x, y + offset_y + height * flip_y),
        ]

    def calculate(self) -> Iterable[Shape]:
        """Find out shapes that can cover provided polygon."""
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

            # Try to insert a mat
            points = self.get_shape_points(x, y, self.mat_width, self.mat_height)
            if self.is_shape_can_be_added(points=points):
                self.update_field(points=points)
                # self.direction_y = self.BACKWARD if self.is_forward_y else self.FORWARD
                self.current_direction = self.HORIZONTAL

                logger.info("Add mat")
                yield Mat(points=points)
                continue

            # Otherwise try to insert a wire
            points = self.get_shape_points(x, y, self.wire_width, self.wire_height)
            if self.is_shape_can_be_added(points=points):
                self.update_field(points=points)
                self.direction_x = self.BACKWARD if self.is_forward_x else self.FORWARD
                self.current_direction = self.VERTICAL

                logger.info("Add wire")
                yield Wire(points=points)
                continue
