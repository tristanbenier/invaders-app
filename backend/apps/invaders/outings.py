"""Outing routes: which invaders to visit, and in which order, within a time budget.

Distances are as the crow flies, plus 30% for the detours of real streets (no routing service):
an estimate, good enough to size an outing. Each stop also costs a few minutes to find and
flash the invader.
"""

import math

from .models import Invader, Status, TransportMode
from .naming import SPECIAL_NAMES

# Average speeds in town (km/h); public transport includes the walk and the wait.
SPEED_KMH = {
    TransportMode.WALK: 4.5,
    TransportMode.BIKE: 14,
    TransportMode.CAR: 25,
    TransportMode.TRANSIT: 15,
}
DETOUR_FACTOR = 1.3
FLASH_MINUTES = 2
EARTH_RADIUS_KM = 6371
# 2-opt passes over the route (each pass is quadratic in the number of stops).
MAX_IMPROVEMENT_PASSES = 20


def distance_km(a, b):
    """Great-circle distance between two (lat, lng) points."""
    lat1, lng1, lat2, lng2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def travel_minutes(a, b, mode):
    return distance_km(a, b) * DETOUR_FACTOR / SPEED_KMH[mode] * 60


def estimate(start, points, end, mode):
    """{"distance_km", "minutes"} of the route start → points → end, flashes included."""
    path = [start, *points, end]
    distance = sum(distance_km(a, b) for a, b in zip(path, path[1:])) * DETOUR_FACTOR
    minutes = distance / SPEED_KMH[mode] * 60 + FLASH_MINUTES * len(points)
    return {"distance_km": round(distance, 1), "minutes": round(minutes)}


def candidates(team, participants, city=None):
    """Team invaders that none of the participants has flashed and that can still be flashed."""
    queryset = (
        Invader.objects.filter(team=team)
        .exclude(status=Status.DESTROYED)
        .exclude(name__in=SPECIAL_NAMES)
        .exclude(flashes__user__in=participants)
    )
    if city is not None:
        queryset = queryset.filter(city=city)
    return list(queryset.only("id", "lat", "lng"))


def _point(invader):
    return (float(invader.lat), float(invader.lng))


def improve_order(start, invaders, end, mode):
    """Shorter order for the same invaders (2-opt: reverse a segment while it shortens the route)."""
    order = list(invaders)
    if len(order) < 2:
        return order
    for _ in range(MAX_IMPROVEMENT_PASSES):
        improved = False
        for i in range(len(order) - 1):
            for j in range(i + 1, len(order)):
                before = start if i == 0 else _point(order[i - 1])
                after = end if j == len(order) - 1 else _point(order[j + 1])
                current = distance_km(before, _point(order[i])) + distance_km(_point(order[j]), after)
                reversed_ = distance_km(before, _point(order[j])) + distance_km(_point(order[i]), after)
                if reversed_ < current - 1e-9:
                    order[i : j + 1] = reversed(order[i : j + 1])
                    improved = True
        if not improved:
            break
    return order


def plan(start, end, mode, duration_minutes, invaders):
    """Invaders to visit from start to end within the duration, in visiting order.

    Greedy: always go to the nearest invader from which the end can still be reached in time,
    then shorten the order (2-opt).
    """
    budget = duration_minutes
    # Out of reach even for a round trip with nothing else: never worth considering.
    remaining = [
        invader
        for invader in invaders
        if travel_minutes(start, _point(invader), mode) + FLASH_MINUTES + travel_minutes(_point(invader), end, mode)
        <= budget
    ]
    route = []
    current, used = start, 0.0
    while remaining:
        best, best_time = None, None
        for invader in remaining:
            point = _point(invader)
            to_invader = travel_minutes(current, point, mode)
            if best_time is not None and to_invader >= best_time:
                continue
            if used + to_invader + FLASH_MINUTES + travel_minutes(point, end, mode) <= budget:
                best, best_time = invader, to_invader
        if best is None:
            break
        route.append(best)
        remaining.remove(best)
        used += best_time + FLASH_MINUTES
        current = _point(best)
    return improve_order(start, route, end, mode)
