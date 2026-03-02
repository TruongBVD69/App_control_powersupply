import unittest

from sources.app_core.range_utils import (
    clamp_next_value,
    compute_step,
    next_index,
    range_reached,
)


class RangeUtilsTests(unittest.TestCase):
    def test_next_index_forward_and_reverse(self) -> None:
        self.assertEqual(next_index(0, 4, reverse=False), 1)
        self.assertEqual(next_index(0, 4, reverse=True), 3)

    def test_next_index_with_empty_total(self) -> None:
        self.assertEqual(next_index(2, 0, reverse=False), 2)

    def test_compute_step_direction(self) -> None:
        self.assertEqual(compute_step(1.0, 2.0, 0.1), 0.1)
        self.assertEqual(compute_step(2.0, 1.0, 0.1), -0.1)

    def test_range_reached(self) -> None:
        self.assertTrue(range_reached(1.0, 1.0, 0.1))
        self.assertTrue(range_reached(1.1, 1.0, 0.1))
        self.assertTrue(range_reached(0.9, 1.0, -0.1))
        self.assertFalse(range_reached(0.9, 1.0, 0.1))

    def test_clamp_next_value(self) -> None:
        self.assertEqual(clamp_next_value(0.9, 0.2, 1.0), 1.0)
        self.assertEqual(clamp_next_value(1.1, -0.2, 1.0), 1.0)
        self.assertEqual(clamp_next_value(1.0, 0.1, 2.0), 1.1)


if __name__ == "__main__":
    unittest.main()

