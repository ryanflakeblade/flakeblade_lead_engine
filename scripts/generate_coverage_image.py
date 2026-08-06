from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "public" / "canada_leads.json"
DEFAULT_SVG = ROOT / "data" / "public" / "canada_leads_coverage.svg"

WIDTH = 1600
HEIGHT = 900

SNOW_COLOR = "#2f6f9f"
LAWN_COLOR = "#2f8f5b"
TOTAL_COLOR = "#1f2933"
MUTED = "#667085"
INK = "#18221b"
PAPER = "#f7f8f4"
PANEL = "#ffffff"
LINE = "#d8dfd5"
MAP_FILL = "#e6eee3"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt_int(value: object) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def project(lon: float, lat: float) -> tuple[float, float]:
    # Lightweight Canada-focused projection for a static marketing image.
    lon_min, lon_max = -140.0, -52.0
    lat_min, lat_max = 41.0, 71.0
    x = 760 + ((lon - lon_min) / (lon_max - lon_min)) * 720
    y = 435 - ((lat - lat_min) / (lat_max - lat_min)) * 360
    return x, y


def canada_shape() -> str:
    points = [
        (740, 378),
        (775, 263),
        (830, 227),
        (886, 250),
        (941, 197),
        (1014, 217),
        (1077, 175),
        (1135, 211),
        (1210, 194),
        (1281, 215),
        (1358, 256),
        (1471, 286),
        (1495, 348),
        (1430, 388),
        (1348, 365),
        (1291, 416),
        (1210, 397),
        (1143, 452),
        (1064, 419),
        (991, 463),
        (929, 430),
        (849, 453),
        (790, 411),
    ]
    return "M " + " L ".join(f"{x} {y}" for x, y in points) + " Z"


def service_counts(item: dict[str, Any]) -> tuple[int, int, bool]:
    counts = item.get("service_counts") or {}
    snow = int(counts.get("snow_removal", 0) or 0)
    lawn = int(counts.get("lawn_mowing", 0) or 0)
    return snow, lawn, bool(counts)


def city_bar(x: float, y: float, city: dict[str, Any], max_companies: int) -> str:
    companies = int(city.get("companies") or 0)
    total_len = 44 + (companies / max_companies) * 142 if max_companies else 44
    snow, lawn, has_split = service_counts(city)

    if has_split and (snow + lawn) > 0:
        snow_len = total_len * (snow / (snow + lawn))
        lawn_len = total_len - snow_len
        return f"""
        <line x1="{x:.1f}" y1="{y:.1f}" x2="{x + total_len:.1f}" y2="{y:.1f}" stroke="#e8ece7" stroke-width="10" stroke-linecap="round"/>
        <line x1="{x:.1f}" y1="{y:.1f}" x2="{x + snow_len:.1f}" y2="{y:.1f}" stroke="{SNOW_COLOR}" stroke-width="10" stroke-linecap="round"/>
        <line x1="{x + snow_len:.1f}" y1="{y:.1f}" x2="{x + snow_len + lawn_len:.1f}" y2="{y:.1f}" stroke="{LAWN_COLOR}" stroke-width="10" stroke-linecap="round"/>
        """

    return f"""
    <line x1="{x:.1f}" y1="{y:.1f}" x2="{x + total_len:.1f}" y2="{y:.1f}" stroke="#e8ece7" stroke-width="10" stroke-linecap="round"/>
    <line x1="{x:.1f}" y1="{y:.1f}" x2="{x + total_len:.1f}" y2="{y:.1f}" stroke="{TOTAL_COLOR}" stroke-width="10" stroke-linecap="round"/>
    """


def render_city_marker(city: dict[str, Any], max_companies: int) -> str:
    lon = city.get("longitude")
    lat = city.get("latitude")
    if lon is None or lat is None:
        return ""

    x, y = project(float(lon), float(lat))
    label_x = x + 20
    label_y = y - 22
    if x > 1280:
        label_x = x - 178
    if y < 120:
        label_y = y + 46

    companies = int(city.get("companies") or 0)
    dot_r = 7
    name = esc(city.get("city", "Unknown"))
    region = esc(city.get("region", ""))

    return f"""
    <g>
      <line x1="{x:.1f}" y1="{y:.1f}" x2="{label_x - 8:.1f}" y2="{label_y - 8:.1f}" stroke="{LINE}" stroke-width="1.4"/>
      <circle cx="{x:.1f}" cy="{y:.1f}" r="{dot_r}" fill="{TOTAL_COLOR}" stroke="{PANEL}" stroke-width="3"/>
      <text x="{label_x:.1f}" y="{label_y:.1f}" class="city-name">{name}</text>
      <text x="{label_x:.1f}" y="{label_y + 24:.1f}" class="city-count">{fmt_int(companies)} companies · {region}</text>
      {city_bar(label_x, label_y + 42, city, max_companies)}
    </g>
    """


def render_region_bars(regions: list[dict[str, Any]]) -> str:
    top_regions = sorted(regions, key=lambda item: item.get("companies", 0), reverse=True)[:5]
    max_companies = max((int(item.get("companies") or 0) for item in top_regions), default=1)
    rows = []
    for index, region in enumerate(top_regions):
        y = 676 + index * 36
        companies = int(region.get("companies") or 0)
        width = 260 * companies / max_companies
        rows.append(
            f"""
            <text x="778" y="{y}" class="bar-label">{esc(region.get("region", ""))}</text>
            <line x1="900" y1="{y - 5}" x2="1160" y2="{y - 5}" stroke="#e8ece7" stroke-width="12" stroke-linecap="round"/>
            <line x1="900" y1="{y - 5}" x2="{900 + width:.1f}" y2="{y - 5}" stroke="{TOTAL_COLOR}" stroke-width="12" stroke-linecap="round"/>
            <text x="1184" y="{y}" class="bar-value">{fmt_int(companies)}</text>
            """
        )
    return "\n".join(rows)


def render_svg(data: dict[str, Any]) -> str:
    totals = data.get("totals", {})
    cities = data.get("cities", [])
    regions = data.get("regions", [])
    top_cities = sorted(cities, key=lambda item: item.get("companies", 0), reverse=True)[:8]
    max_city_companies = max((int(city.get("companies") or 0) for city in top_cities), default=1)
    has_service_split = any((city.get("service_counts") or {}) for city in top_cities)
    legend_note = "Stacked bars show snow removal vs lawn mowing" if has_service_split else "Bars show company count; rerun JSON export for service split"

    city_markers = "\n".join(render_city_marker(city, max_city_companies) for city in top_cities)
    region_bars = render_region_bars(regions)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Canada business lead coverage snapshot">
  <style>
    .title {{ font: 600 56px Arial, sans-serif; fill: {INK}; }}
    .subtitle {{ font: 400 24px Arial, sans-serif; fill: {MUTED}; }}
    .brand {{ font: 600 22px Arial, sans-serif; fill: {INK}; }}
    .kicker {{ font: 600 16px Arial, sans-serif; fill: {MUTED}; letter-spacing: 1px; }}
    .stat-value {{ font: 600 46px Arial, sans-serif; fill: {INK}; }}
    .stat-label {{ font: 400 18px Arial, sans-serif; fill: {MUTED}; }}
    .city-name {{ font: 600 18px Arial, sans-serif; fill: {INK}; }}
    .city-count {{ font: 400 15px Arial, sans-serif; fill: {MUTED}; }}
    .bar-title {{ font: 600 22px Arial, sans-serif; fill: {INK}; }}
    .bar-label {{ font: 600 17px Arial, sans-serif; fill: {INK}; }}
    .bar-value {{ font: 400 16px Arial, sans-serif; fill: {MUTED}; }}
    .legend {{ font: 400 16px Arial, sans-serif; fill: {MUTED}; }}
  </style>
  <rect width="1600" height="900" fill="{PAPER}"/>
  <rect x="36" y="36" width="1528" height="828" rx="18" fill="{PANEL}" stroke="{LINE}"/>

  <g transform="translate(78 82)">
    <rect x="0" y="0" width="34" height="34" rx="7" fill="{LAWN_COLOR}"/>
    <text x="48" y="25" class="brand">Flakeblade Lead Engine</text>
  </g>

  <text x="78" y="190" class="kicker">CANADA COVERAGE SNAPSHOT</text>
  <text x="78" y="270" class="title">Local service markets</text>
  <text x="78" y="330" class="title">at national scale</text>
  <text x="78" y="386" class="subtitle">Public monthly view for snow removal and lawn mowing companies.</text>

  <g transform="translate(78 492)">
    <line x1="0" y1="0" x2="520" y2="0" stroke="{LINE}"/>
    <text x="0" y="70" class="stat-value">{fmt_int(totals.get("companies"))}</text>
    <text x="0" y="104" class="stat-label">companies</text>
    <text x="190" y="70" class="stat-value">{fmt_int(totals.get("cities"))}</text>
    <text x="190" y="104" class="stat-label">cities</text>
    <text x="338" y="70" class="stat-value">{esc(str(totals.get("service_status", "both")).title())}</text>
    <text x="338" y="104" class="stat-label">services</text>
  </g>

  <text x="78" y="748" class="legend">Updated {esc(data.get("updated_at", ""))}</text>
  <text x="78" y="784" class="legend">{esc(legend_note)}</text>

  <g>
    <path d="{canada_shape()}" fill="{MAP_FILL}" stroke="{LINE}" stroke-width="2"/>
    <path d="M760 492 C895 520, 1020 545, 1140 522 C1245 502, 1350 548, 1450 504" fill="none" stroke="{LINE}" stroke-width="2"/>
    {city_markers}
  </g>

  <g>
    <text x="778" y="628" class="bar-title">Regional coverage</text>
    {region_bars}
  </g>

  <g transform="translate(1286 676)">
    <circle cx="0" cy="0" r="8" fill="{SNOW_COLOR}"/><text x="18" y="6" class="legend">Snow removal</text>
    <circle cx="0" cy="34" r="8" fill="{LAWN_COLOR}"/><text x="18" y="40" class="legend">Lawn mowing</text>
    <circle cx="0" cy="68" r="8" fill="{TOTAL_COLOR}"/><text x="18" y="74" class="legend">City location</text>
  </g>
</svg>
"""


def generate_image(json_path: Path, svg_path: Path) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(render_svg(data), encoding="utf-8")
    print(f"Wrote {svg_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate public Canada coverage SVG from leads JSON.")
    parser.add_argument("--input", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output", type=Path, default=DEFAULT_SVG)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_image(args.input, args.output)


if __name__ == "__main__":
    main()

