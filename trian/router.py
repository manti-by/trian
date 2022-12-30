import logging
from collections import defaultdict
from functools import partial
from itertools import chain
from math import ceil, floor
from time import sleep
from typing import Iterable

from shapely.geometry import LinearRing, Point, Polygon

from trian.const import (
    BACKWARD,
    BX_BY,
    BX_FY,
    FORWARD,
    FX_BY,
    FX_FY,
    HORIZONTAL,
    MAT_HORIZONTAL,
    MAT_VERTICAL,
    MAX_SOCKET_DISTANCE,
    VERTICAL,
    WIRE_HORIZONTAL,
    WIRE_VERTICAL,
)
from trian.models import Mat, Shape, Wire

logger = logging.getLogger(__name__)


class Router:
    def __init__(
        self,
        socket: Point,
        shell: list[Point],
        holes: list[list[Point]],
        wire_radius: int,
        mat_width: int,
        mat_fill: str,
        precision: int,
        flip_xy: bool,
        field: dict[int, dict[int, bool]] = None,
    ):
        """Init the class with values from the UI."""
        self.socket = socket
        self.shell = shell
        self.holes = holes
        self.shell_polygon = Polygon(shell=self.shell)
        self.hole_polygons = [Polygon(shell=points) for points in self.holes]

        self.wire_radius = wire_radius
        self.mat_width = mat_width
        self.mat_fill = mat_fill
        self.precision = precision

        self.min_x, self.max_x, self.min_y, self.max_y = self.shell_polygon.bounds
        self.field = (
            field if field else defaultdict(lambda: defaultdict(partial(bool, False)))
        )

        self.curr_x, self.curr_y = None, None
        self.direction_x, self.direction_y = FORWARD, FORWARD
        self.current_direction = VERTICAL if flip_xy else HORIZONTAL

        self.points = None
        self.directions = (BX_BY, FX_BY, FX_FY, BX_FY) if flip_xy else (FX_FY, BX_FY, BX_BY, FX_BY)
        self.methods = {
            MAT_HORIZONTAL: (self.wire_radius, self.mat_width),
            MAT_VERTICAL: (self.mat_width, self.wire_radius),
            WIRE_HORIZONTAL: (self.wire_radius * 2, self.wire_radius),
            WIRE_VERTICAL: (self.wire_radius, self.wire_radius * 2),
        }

    @property
    def is_horizontal_direction(self) -> bool:
        return self.current_direction == HORIZONTAL

    @property
    def is_vertical_direction(self) -> bool:
        return self.current_direction == VERTICAL

    @property
    def is_forward_x(self) -> bool:
        return self.direction_x == FORWARD

    @property
    def is_forward_y(self) -> bool:
        return self.direction_y == FORWARD

    def get_point_neighbors_statuses(
        self, point: Point
    ) -> list[bool, bool, bool, bool]:
        """Bottom-Right, Bottom-Left, Top-Left, Top-Right."""
        result = []
        for direction in self.directions:
            direction_x, direction_y = direction
            curr_x = point.x + self.precision * direction_x
            curr_y = point.y + self.precision * direction_y
            is_polygon_contains = self.shell_polygon.contains(Point(curr_x, curr_y))
            result.append(self.field[curr_x][curr_y] or not is_polygon_contains)
        return result

    def get_closest_vertex(self, point: Point) -> Point | None:
        """Find the closest vertex to the point position."""
        closest_vertex = None
        closest_distance = None
        for p in self.shell:
            # Check a free point around current vertex
            is_any_cell_neighbors_is_free = any(
                (x is False for x in self.get_point_neighbors_statuses(p))
            )
            current_distance = point.distance(p)
            if (
                (closest_distance is None or current_distance < closest_distance)
                and current_distance < MAX_SOCKET_DISTANCE
                and is_any_cell_neighbors_is_free
            ):
                closest_vertex = p
                closest_distance = current_distance
        return closest_vertex

    def get_start_position(self) -> tuple[int, int]:
        """Start from a vertex closest to the socket position or socket itself."""
        closest_vertex = self.get_closest_vertex(self.socket)
        if closest_vertex is None:
            closest_vertex = self.socket

        start_x = int(closest_vertex.x)
        start_y = int(closest_vertex.y)

        # Chose direction using start point neighbors statuses
        statuses = self.get_point_neighbors_statuses(closest_vertex)
        if statuses[0] is False:
            start_x += self.precision
            start_y += self.precision
        elif statuses[1] is False:
            start_x -= self.precision
            start_y += self.precision
        elif statuses[2] is False:
            start_x -= self.precision
            start_y -= self.precision
        elif statuses[3] is False:
            start_x += self.precision
            start_y -= self.precision

        return start_x, start_y

    def find_closest_free_position(self) -> tuple[int, int] | None:
        for curr_x in range(int(self.min_x), int(self.max_x)):
            for curr_y in range(int(self.min_y), int(self.max_y)):
                is_polygon_contains = self.shell_polygon.contains(Point(curr_x, curr_y))
                if is_polygon_contains and not self.field[curr_x][curr_y]:
                    return curr_x, curr_y

    def is_shape_can_be_added(self, points: list[Point]) -> bool:
        """All points should be covered by polygon and free in the field."""
        new_shape = Polygon(shell=points)
        if not self.shell_polygon.contains(new_shape):
            return False
        if any(
            (x.overlaps(new_shape) or x.contains(new_shape) for x in self.hole_polygons)
        ):
            return False
        min_x, min_y, max_x, max_y = list(map(lambda x: int(x), new_shape.bounds))
        for curr_x in range(min_x, max_x):
            for curr_y in range(min_y, max_y):
                if self.field[curr_x][curr_y]:
                    return False
        return True

    def add_polygon_to_field(self, points: list[Point]):
        """Fill in all points are covered by a new shape."""
        new_shape = Polygon(shell=points)
        min_x, min_y, max_x, max_y = list(map(lambda x: int(x), new_shape.bounds))
        for curr_x in range(min_x, max_x):
            for curr_y in range(min_y, max_y):
                self.field[curr_x][curr_y] = True

    def find_next_route_for_point(
        self, x: int, y: int
    ) -> tuple[str, tuple[int, int], tuple[int, int]] | None:
        """Find the best method and route for the given point to go next."""
        for method, options in self.methods.items():
            width, height = options
            for direction in self.directions:
                direction_x, direction_y = direction
                points = [
                    Point(x, y),
                    Point(x, y + height * direction_y),
                    Point(x + width * direction_x, y),
                    Point(x + width * direction_x, y + height * direction_y),
                ]
                if self.is_shape_can_be_added(points=points):
                    return method, (x, y), direction

    def find_next_route(
        self, points: list[Point]
    ) -> tuple[str, tuple[int, int], tuple[int, int]] | None:
        """Find the best method and route to go next."""
        new_shape = Polygon(shell=points)
        min_x, min_y, max_x, max_y = list(map(lambda x: int(x), new_shape.bounds))
        for curr_x in (min_x, max_x):
            for curr_y in (min_y, max_y):
                result = self.find_next_route_for_point(curr_x, curr_y)
                if result is not None:
                    return result

    def get_shape_points(
        self, x: int, y: int, width: int, height: int
    ) -> list[Point, Point, Point, Point]:
        """Flip shape if direction is changed."""
        flip_x = 1 if self.is_forward_x else -1
        flip_y = 1 if self.is_forward_y else -1
        return [
            Point(x, y),
            Point(x + width * flip_x, y),
            Point(x + width * flip_x, y + height * flip_y),
            Point(x, y + height * flip_y),
        ]

    def next(self) -> Iterable[Shape]:
        """Find out shapes that can cover provided polygon."""
        if self.curr_x is None and self.curr_y is None:
            self.curr_x, self.curr_y = self.get_start_position()

        # If start point can be determined try to find the closest free point
        result = self.find_next_route_for_point(self.curr_x, self.curr_y)
        if result is None:
            position = self.find_closest_free_position()
            if position is None:
                logger.error("There are no free positions")
                return
            self.curr_x, self.curr_y = position

        while True:
            # sleep(0.01)
            result = self.find_next_route_for_point(self.curr_x, self.curr_y)
            if not result and self.points:
                result = self.find_next_route(self.points)

            if result is None:
                logger.warning("Can't choose next position, exit")
                return

            # Unpack result
            method, point, direction = result
            self.curr_x, self.curr_y = point

            logger.info(f"x: {self.curr_x}, y: {self.curr_y}")

            direction_x, direction_y = direction
            self.direction_x = FORWARD if direction_x == 1 else BACKWARD
            self.direction_y = FORWARD if direction_y == 1 else BACKWARD

            shape = 0
            if method == MAT_HORIZONTAL:
                self.current_direction = HORIZONTAL
                self.points = self.get_shape_points(
                    self.curr_x, self.curr_y, self.wire_radius, self.mat_width
                )
                self.curr_x += self.wire_radius * (1 if self.is_forward_x else -1)

                self.add_polygon_to_field(points=self.points)
                shape = Mat(points=self.points, fill=self.mat_fill)
                logger.info("Add horizontal mat")

            elif method == MAT_VERTICAL:
                self.current_direction = VERTICAL
                self.points = self.get_shape_points(
                    self.curr_x, self.curr_y, self.mat_width, self.wire_radius
                )
                self.curr_y += self.wire_radius * (1 if self.is_forward_y else -1)

                self.add_polygon_to_field(points=self.points)
                shape = Mat(points=self.points, fill=self.mat_fill)
                logger.info("Add vertical mat")

            elif method == WIRE_HORIZONTAL:
                self.current_direction = HORIZONTAL
                self.points = self.get_shape_points(
                    self.curr_x, self.curr_y, self.wire_radius, self.wire_radius
                )
                self.curr_x += self.wire_radius * (1 if self.is_forward_x else -1)

                self.add_polygon_to_field(points=self.points)
                shape = Wire(points=self.points)
                logger.info("Add horizontal wire")

            elif method == WIRE_VERTICAL:
                self.current_direction = VERTICAL
                self.points = self.get_shape_points(
                    self.curr_x, self.curr_y, self.wire_radius, self.wire_radius
                )
                self.curr_y += self.wire_radius * (1 if self.is_forward_y else -1)

                self.add_polygon_to_field(points=self.points)
                shape = Wire(points=self.points)
                logger.info("Add vertical wire")

            if shape is not None:
                yield shape
