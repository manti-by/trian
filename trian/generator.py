import logging
from collections import defaultdict
from functools import partial

from typing import Iterable

from shapely.geometry import Point, Polygon

from trian.models import Mat, Shape, Wire

logger = logging.getLogger(__name__)


class Generator:

    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"

    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"

    SOCKET_MAX_DISTANCE = 370

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
        field: dict[int, dict[int, bool]] = None,
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

        self.field = field if field else defaultdict(lambda: defaultdict(partial(bool, False)))

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
        x_list, y_list = [int(p.x) for p in points], [int(p.y) for p in points]
        return min(x_list), max(x_list), min(y_list), max(y_list)

    def get_point_neighbors_statuses(self, point: Point) -> tuple[bool, bool, bool, bool]:
        """Top-Right, Bottom-Right, Bottom-Left, Top-Left."""
        return (
            self.field[point.x + self.precision][point.y - self.precision],
            self.field[point.x + self.precision][point.y + self.precision],
            self.field[point.x - self.precision][point.y + self.precision],
            self.field[point.x - self.precision][point.y - self.precision],
        )

    def calculate_field_bounds(self):
        """Calculate the polygon bounding edges."""
        self.min_x, self.max_x, self.min_y, self.max_y = self.get_points_bounds(
            points=self.points
        )

    def get_closest_vertex(self, point: Point) -> Point | None:
        """Find the closest vertex to the point position."""
        closest_vertex = None
        closest_distance = None
        for p in self.points:
            # Check a free point around current vertex
            is_any_cell_neighbors_is_free = any(
                (x is False for x in self.get_point_neighbors_statuses(p))
            )
            current_distance = point.distance(p)
            if (
                closest_distance is None
                or current_distance < closest_distance
                and current_distance < self.SOCKET_MAX_DISTANCE
                and is_any_cell_neighbors_is_free
            ):
                closest_vertex = p
                closest_distance = current_distance
        return closest_vertex

    def get_start_point(self) -> Point:
        """Start from a vertex closest to the socket position or socket itself."""
        if self.socket:
            closest_vertex = self.get_closest_vertex(self.socket)
            if closest_vertex is None:
                closest_vertex = self.socket
            return closest_vertex

        # Otherwise initial position is the closes position to top/left corner
        start_point = self.points[0]
        for point in self.points:
            if point.x <= start_point.x and point.y <= start_point.y:
                start_point = point
        return start_point

    def is_shape_can_be_added(self, points: list[Point]) -> bool:
        """All points should be free in the field."""
        min_x, max_x, min_y, max_y = self.get_points_bounds(points=points)
        for r_x in range(min_x, max_x):
            for r_y in range(min_y, max_y):
                if self.field[r_x][r_y] is True or not self.polygon.contains(Point(r_x, r_y)):
                    return False
        return True

    def update_field(self, points: list[Point]):
        """Fill in all points are covered by a new shape."""
        min_x, max_x, min_y, max_y = self.get_points_bounds(points=points)
        for r_x in range(min_x, max_x):
            for r_y in range(min_y, max_y):
                self.field[r_x][r_y] = True

    def choose_next_x(self) -> int:
        """Horizontal direction rules."""
        if self.is_forward_x:  # Forward
            # Check room bounds (fast)
            # Then try to restrict moving outside the room
            if self.prev_x <= self.max_x - self.precision:
                self.prev_x += self.precision
        else:  # Backward
            if self.prev_x >= self.min_x + self.precision:
                self.prev_x -= self.precision
        return self.prev_x

    def choose_next_y(self):
        """Vertical direction rules."""
        if self.is_forward_y:
            if self.prev_y <= self.max_y - self.precision:
                self.prev_y += self.precision
        else:
            if self.prev_y >= self.min_y + self.precision:
                self.prev_y -= self.precision
        return self.prev_y

    def choose_next_position(self) -> tuple[int, int]:
        """The main part of the generator that chooses a next move."""
        if self.prev_x is None and self.prev_y is None:
            point = self.get_start_point()
            self.prev_x = int(point.x)
            self.prev_y = int(point.y)

            # Chose direction using start point neighbors statuses
            statuses = self.get_point_neighbors_statuses(point)
            if statuses[0] is True:
                self.direction_x, self.direction_y = self.FORWARD, self.BACKWARD
                self.prev_x += 1
                self.prev_x -= 1
            elif statuses[1] is True:
                self.direction_x, self.direction_y = self.FORWARD, self.FORWARD
                self.prev_x += 1
                self.prev_x += 1
            elif statuses[2] is True:
                self.direction_x, self.direction_y = self.BACKWARD, self.FORWARD
                self.prev_x -= 1
                self.prev_x += 1
            elif statuses[3] is True:
                self.direction_x, self.direction_y = self.BACKWARD, self.BACKWARD
                self.prev_x -= 1
                self.prev_x -= 1

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

        offset_x = 1 if self.is_forward_x else 0
        offset_y = 1 if self.is_forward_y else 0

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
        while True:
            x, y = self.choose_next_position()
            logger.info(f"{x}, {y}")

            # Try to detect a loop
            if loop_x == x and loop_y == y:
                is_loop += 1
                if is_loop > 10:
                    break
            loop_x, loop_y = x, y

            # Skip already filled positions
            if self.field[x][y] is True:
                continue

            # Try to insert a mat
            points = self.get_shape_points(x, y, self.mat_width, self.mat_height)
            if self.is_shape_can_be_added(points=points):
                self.update_field(points=points)
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
