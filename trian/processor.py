from collections import defaultdict

from shapely.geometry import Point, Polygon

from trian.models import Shape, Mat, Wire


class Processor:

    EDGE = "E"
    BODY = "B"

    FREE = "F"
    NULL = "N"

    precision = 10

    def __init__(self, points: list[Point], wire_size: int, mat_size: int):
        self.result = []
        self.points = points
        self.polygon = Polygon(self.points)

        self.wire_size = wire_size
        self.mat_size = mat_size

        self.min_x, self.max_x = None, None
        self.min_y, self.max_y = None, None
        self.calculate_bounds()

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
        for x in range(self.min_x, self.max_x):
            for y in range(self.min_y, self.max_y):
                self.field[x][y] = self.FREE if self.polygon.contains(Point(x, y)) else self.NULL

    def is_shape_can_be_added(self, shape: Mat | Wire) -> bool:
        for point in shape.points:
            if self.field[point.x][point.y] not in (self.FREE, self.EDGE):
                return False
        return True

    def update_field(self, x: int, y: int, size: int):
        for r_x in range(x, x + size):
            for r_y in range(y, y + size):
                is_edge_location = any((
                    r_x == x, r_x == x + size, r_y == y, r_y == y + size
                ))
                self.field[r_x][r_y] = self.EDGE if is_edge_location else self.BODY

    def calculate(self) -> list[Shape]:
        for y in range(self.min_y, self.max_y, self.precision):
            for x in range(self.min_x, self.max_x, self.precision):
                if not self.field[x][y] or self.field[x][y] == self.NULL:
                    continue
                mat = Mat(
                    points=[
                        Point(x, y),
                        Point(x + self.mat_size, y),
                        Point(x + self.mat_size, y + self.mat_size),
                        Point(x, y + self.mat_size),
                    ]
                )
                if self.is_shape_can_be_added(shape=mat):
                    self.result.append(mat)
                    self.update_field(x, y, self.mat_size)
                    continue
        return self.result
