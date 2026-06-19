import csv
import time
import requests

# Configuration
INPUT_FILE = 'fuel-prices.csv'
OUTPUT_FILE = 'fuel_prices_geocoded.csv'

# Nominatim Usage Policy requires a valid User-Agent identifying your application.
# Replace 'your_email@example.com' with your actual email or website URL.
HEADERS = {
    'User-Agent': 'MyTruckstopGeocoder/1.0 (fozangardezi@gmail.com)'
}

def query_nominatim(query):
    """Sends a request to Nominatim and returns (lat, lon) or (None, None)."""
    params = {
        'q': query,
        'format': 'json',
        'limit': 1
    }
    try:
        response = requests.get('https://nominatim.openstreetmap.org/search', params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        # IMPORTANT: Nominatim has a strict maximum rate limit of 1 request per second.
        time.sleep(1) 
        
        if data:
            return data[0]['lat'], data[0]['lon']
    except Exception as e:
        print(f"    Error querying '{query}': {e}")
        time.sleep(1) # Still sleep even on error to respect rate limits
        
    return None, None

def get_lat_lon(address, city, state):
    """Tries to geocode the full address, falls back to City/State if it fails."""
    # Clean and construct queries, ignoring empty fields
    full_query = ", ".join([p.strip() for p in [address, city, state] if p and p.strip()])
    fallback_query = ", ".join([p.strip() for p in [city, state] if p and p.strip()])
    
    if not full_query:
        return None, None

    print(f"  Trying: {full_query}")
    lat, lon = query_nominatim(full_query)
    
    # Fallback to just City and State if full address fails
    if not lat and fallback_query and fallback_query != full_query:
        print(f"    Full address failed. Falling back to: {fallback_query}")
        lat, lon = query_nominatim(fallback_query)
        
    return lat, lon

def main():
    with open(INPUT_FILE, mode='r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        
        # Add Latitude and Longitude to the existing fieldnames
        fieldnames = reader.fieldnames + ['Latitude', 'Longitude']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, row in enumerate(reader):
            print(f"Processing row {i+1}: {row['Truckstop Name']}...")
            
            lat, lon = get_lat_lon(row['Address'], row['City'], row['State'])
            
            # Update the row with coordinates (empty string if not found)
            row['Latitude'] = lat if lat else ''
            row['Longitude'] = lon if lon else ''
            
            writer.writerow(row)
            
    print(f"\nGeocoding complete! Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()