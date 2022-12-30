from typing import Any

import pytest
from shapely.geometry import Point


@pytest.fixture
def base_params() -> dict[str, Any]:
    socket = Point(370, 110)
    shell = [
        Point(370, 60),
        Point(670, 60),
        Point(670, 520),
        Point(110, 520),
        Point(110, 330),
        Point(220, 220),
        Point(370, 220),
    ]
    holes = [
        [
            Point(420, 450),
            Point(660, 450),
            Point(660, 510),
            Point(420, 510),
        ],
        [
            Point(420, 250),
            Point(420, 350),
            Point(620, 350),
            Point(620, 250),
        ],
    ]
    return {
        "socket": socket,
        "shell": shell,
        "holes": holes,
        "wire_radius": 8,
        "mat_width": 55,
        "mat_fill": "green",
        "precision": 1,
        "flip_xy": False,
    }
