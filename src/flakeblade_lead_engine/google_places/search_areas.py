from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchBox:
    name: str
    low_latitude: float
    low_longitude: float
    high_latitude: float
    high_longitude: float

    def to_places_rectangle(self) -> dict[str, Any]:
        return {
            "low": {"latitude": self.low_latitude, "longitude": self.low_longitude},
            "high": {"latitude": self.high_latitude, "longitude": self.high_longitude},
        }


GREATER_MONTREAL_BOXES = [
    SearchBox("montreal_core", 45.42, -73.76, 45.62, -73.47),
    SearchBox("laval_north", 45.55, -73.90, 45.78, -73.55),
    SearchBox("south_shore", 45.35, -73.65, 45.58, -73.25),
    SearchBox("west_island_vaudreuil", 45.32, -74.10, 45.58, -73.70),
    SearchBox("north_shore", 45.62, -74.05, 45.88, -73.55),
]

SNOW_REMOVAL_KEYWORDS = [
    "déneigement commercial Montréal",
    "entrepreneur déneigement Montréal",
    "snow removal contractor Montreal",
    "déneigement stationnement Montréal",
]

