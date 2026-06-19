# FuelCostOptimizer
Django API for planning cost-effective fuel stops along a USA driving route.

## Load fuel prices

The OPIS truckstop fuel file is tab-delimited and should contain these columns:

```text
OPIS Truckstop ID	Truckstop Name	Address	City	State	Rack ID	Retail Price
```

Create the database table and import the file before using the route API:

```bash
cd FuelCostOptimizer
python manage.py migrate
python manage.py import_fuel_prices fuel_prices.csv --geocode
```

`--geocode` looks up each truckstop address and stores coordinates on the model so the route planner can find stations near the route. Omit `--geocode` only if coordinates have already been populated by another process.

## Endpoint

`GET /api/route/?start=New%20York,%20NY&finish=Chicago,%20IL`

The response includes geocoded endpoints, an OSRM GeoJSON route suitable for rendering on OpenStreetMap/Leaflet, suggested fuel stops, and estimated fuel spend for a vehicle that gets 10 MPG with a 500 mile maximum range.

## Routing and maps

This project uses free OpenStreetMap ecosystem services:

- Nominatim for US-only geocoding.
- OSRM public demo server for route geometry and distance.
- OpenStreetMap tiles can render the returned GeoJSON route in clients such as Leaflet.

The public OSRM and Nominatim services are appropriate for demos and light development. For production traffic, host your own services or use a provider plan that matches your usage.
