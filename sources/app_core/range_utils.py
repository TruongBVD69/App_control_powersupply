from __future__ import annotations


def next_index(current_index: int, total: int, reverse: bool) -> int:
    if total <= 0:
        return current_index
    if reverse:
        return (current_index - 1) % total
    return (current_index + 1) % total


def range_reached(current: float, target: float, step: float) -> bool:
    if step > 0:
        return current >= target - 1e-9
    return current <= target + 1e-9


def compute_step(current: float, target: float, base_step: float) -> float:
    if target < current:
        return -abs(base_step)
    return abs(base_step)


def clamp_next_value(current: float, step: float, target: float) -> float:
    next_value = current + step
    if (step > 0 and next_value > target) or (step < 0 and next_value < target):
        next_value = target
    return round(next_value, 6)

