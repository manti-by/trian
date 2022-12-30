from typing import Any

from shapely.geometry import Point

from trian.router import Router


class TestRouter:
    def test_get_start_position(self, base_params: dict[str, Any]):
        router = Router(**base_params)
        assert router.get_start_position() == (371, 61)

        router.add_polygon_to_field(
            [Point(371, 61), Point(490, 61), Point(490, 200), Point(371, 200)]
        )
        assert router.get_start_position() == (371, 221)

    def test_is_shape_can_be_added(self, base_params: dict[str, Any]):
        router = Router(**base_params)

        shape = [Point(470, 110), Point(520, 110), Point(520, 180), Point(470, 180)]
        assert router.is_shape_can_be_added(shape)

        shape = [Point(520, 180), Point(520, 300), Point(440, 300), Point(440, 180)]
        assert not router.is_shape_can_be_added(shape)
