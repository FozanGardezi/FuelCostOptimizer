import csv
import json
import math
import heapq
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path


from django.conf import settings

MPG = 10
MAX_RANGE_MILES = 500
MILES_PER_METER = 0.000621371
EARTH_RADIUS_MILES = 3958.8


class RoutePlannerError(Exception):
    pass


def _http_json(url: str) -> Dict:
    request = Request(
        url,
        headers={
            'User-Agent': 'FuelCostOptimizer/1.0 (educational demo; fozangardezi@gmail.com)',
            'Accept': 'application/json',
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def geocode_us_location(query: str) -> Dict:
    params = urlencode({'q': query, 'format': 'jsonv2', 'limit': 1, 'countrycodes': 'us'})
    print("Geocoding location with Nominatim:", query)
    data = _http_json(f'https://nominatim.openstreetmap.org/search?{params}')
    if not data:
        raise RoutePlannerError(f'Could not geocode location within the USA: {query}')
    item = data[0]
    return {'label': item.get('display_name', query), 'lat': float(item['lat']), 'lon': float(item['lon'])}


def fetch_route(start: Dict, finish: Dict) -> Dict:
    coords = f"{start['lon']},{start['lat']};{finish['lon']},{finish['lat']}"
    url = (
        f'https://router.project-osrm.org/route/v1/driving/{coords}'
        '?overview=full&geometries=geojson&steps=false'
    )
    data = _http_json(url)
    if data.get('code') != 'Ok' or not data.get('routes'):
        raise RoutePlannerError('Routing service could not build a route for those locations.')
    route = data['routes'][0]
    return {
        'distance_miles': route['distance'] * MILES_PER_METER,
        'duration_seconds': route['duration'],
        'geometry': route['geometry'],
    }


def haversine_miles(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    '''Calculate the great circle distance in miles between two points on the Earth specified in decimal degrees.'''
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(h))

def _read_fuel_price_rows() -> List[Dict]:
    path = Path(getattr(settings, 'FUEL_PRICES_FILE', settings.BASE_DIR / '../fuel_prices_geocoded.csv'))
    if not path.exists():
        raise RoutePlannerError(f'Fuel price file does not exist: {path}')
    with path.open(newline='', encoding='utf-8-sig') as fh:
        sample = fh.read(2048)
        fh.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters='\t,')
        return list(csv.DictReader(fh, dialect=dialect))

def _pick(row: Dict, *names: str) -> Optional[str]:
    lowered = {key.strip().lower().replace(' ', '_'): (value or '').strip() for key, value in row.items()}
    for name in names:
        value = lowered.get(name)
        if value:
            return value
    return None

def load_fuel_prices_geocoded() -> List[Dict]:
    stations = []
    for row in _read_fuel_price_rows():
        try:
            lat = float(_pick(row, 'lat', 'latitude'))
            lon = float(_pick(row, 'lon', 'lng', 'longitude'))
            price = float(str(_pick(row, 'retail_price', 'price', 'fuel_price', 'diesel_price')).replace('$', ''))
        except (TypeError, ValueError):
            continue
        stations.append({
            'opis_truckstop_id': _pick(row, 'opis_truckstop_id'),
            'name': _pick(row, 'truckstop_name', 'name', 'station', 'brand') or 'Fuel stop',
            'address': _pick(row, 'address') or '',
            'city': _pick(row, 'city') or '',
            'state': (_pick(row, 'state') or '').upper(),
            'rack_id': _pick(row, 'rack_id'),
            'lat': lat,
            'lon': lon,
            'price_per_gallon': price,
        })
    return stations


def route_points(route: Dict) -> List[Tuple[float, float]]:
    return [(lat, lon) for lon, lat in route['geometry']['coordinates']]

def cumulative_distances(points: List[Tuple[float, float]]) -> List[float]:
    totals = [0.0]
    for prev, point in zip(points, points[1:]):
        totals.append(totals[-1] + haversine_miles(prev, point))
    return totals


def nearest_route_mile(station: Dict, points: List[Tuple[float, float]], totals: List[float]) -> Tuple[float, float]:
    '''Returns (nearest mile marker on route, detour distance in miles) for a given station.'''
    distances = [haversine_miles((station['lat'], station['lon']), point) for point in points]
    idx = min(range(len(distances)), key=distances.__getitem__)
    return totals[idx], distances[idx]

def optimal_fuel_stops(route: Dict) -> Dict:
    points = route_points(route)
    totals = cumulative_distances(points)
    route_distance = route["distance_miles"]

    fuel_prices = load_fuel_prices_geocoded()

    stations = []
    ''''''
    for station in fuel_prices:
        mile, detour = nearest_route_mile(station, points, totals)
        '''Only consider stations that are within a reasonable detour distance from the route.'''
        if detour <= 25:
            stations.append({
                **station,
                "route_mile": mile,
                "route_detour_miles": detour
            })
    # Add start and destination nodes
    nodes = [
        {
            "name": "START",
            "route_mile": 0,
            "price_per_gallon": None
        }
    ]
    nodes.extend(stations)
    nodes.append({
        "name": "END",
        "route_mile": route_distance,
        "price_per_gallon": None
    })
    # Sort by route position
    nodes.sort(key=lambda x: x["route_mile"])
    n = len(nodes)

    # Distance table
    cost = [math.inf] * n
    parent = [None] * n
    start_index = 0
    cost[start_index] = 0

    # priority queue:
    # (total_cost, node_index)
    pq = [(0, start_index)]
    while pq:
        current_cost, i = heapq.heappop(pq)
        if current_cost > cost[i]:
            continue
        current = nodes[i]
        # Try every reachable next station
        for j in range(i + 1, n):
            nxt = nodes[j]
            distance = (nxt["route_mile"] - current["route_mile"])

            if distance > MAX_RANGE_MILES:
                break

            # Start has no fuel price.
            # Assume starting fuel is free/full tank.
            if current["price_per_gallon"] is None:
                fuel_cost = 0
            else:
                gallons = distance / MPG
                fuel_cost = (gallons * current["price_per_gallon"])
            new_cost = current_cost + fuel_cost

            if new_cost < cost[j]:
                cost[j] = new_cost
                parent[j] = i
                heapq.heappush(pq,( new_cost, j))

    end_index = n - 1
    if cost[end_index] == math.inf:
        return {
            "fuel_stops": [],
            "total_fuel_cost": None
        }

    path = []
    idx = end_index
    while idx is not None:
        path.append(nodes[idx])
        idx = parent[idx]
    path.reverse()
    stops = []
    for i in range(1, len(path)-1):
        stop = path[i]
        prev = path[i-1]
        miles = (stop["route_mile"] - prev["route_mile"])
        gallons = miles / MPG
        stops.append({
            **stop,
            "gallons": round(gallons, 2),
            "estimated_cost": round(
                gallons *
                stop["price_per_gallon"],
                2
            )
        })

    return {
        "fuel_stops": stops,
        "total_fuel_cost": round(cost[end_index], 2)
    }


def build_plan(start_query: str, finish_query: str) -> Dict:
    print(f"Building route fuel plan for start='{start_query}' and finish='{finish_query}'")
    start = geocode_us_location(start_query)
    print(f"Geocoded start: {start['label']} at ({start['lat']}, {start['lon']})")
    finish = geocode_us_location(finish_query)
    route = fetch_route(start, finish)
    duration_minutes = route['duration_seconds'] / 60
    print("Fetched route: distance_miles={:.2f}, duration_minutes={}".format(route['distance_miles'], duration_minutes))
    fuel_plan = optimal_fuel_stops(route)
    gallons_needed = route['distance_miles'] / MPG
    return {
        'start': start,
        'finish': finish,
        'route': {
            'distance_miles': round(route['distance_miles'], 2),
            'duration_seconds': round(route['duration_seconds']),
            'geojson': route['geometry'],
            'map': {
                'provider': 'OpenStreetMap tiles; route from OSRM public demo server',
                'tile_url_template': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                'rendering_hint': 'Render the GeoJSON LineString as a route overlay and plot each fuel stop marker.',
            },
        },
        'vehicle': {'mpg': MPG, 'maximum_range_miles': MAX_RANGE_MILES, 'estimated_gallons_needed': round(gallons_needed, 2)},
        **fuel_plan,
    }
