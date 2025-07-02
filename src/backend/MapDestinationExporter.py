import os
import csv
import time
import googlemaps
from difflib import get_close_matches
from models import Location, db

class MapDestinationExporter:
    def __init__(self, api_key: str):
        self.gmaps = googlemaps.Client(key=api_key)
        self.locations = []

    def clean_destinations(self, raw_destinations):
        """
        Cleans and deduplicates a list of destination strings.
        """
        cleaned = []
        seen = set()
        for place in raw_destinations:
            normalized = place.strip().lower()
            # Remove near duplicates using fuzzy matching
            if normalized and not any(get_close_matches(normalized, seen, cutoff=0.85)):
                seen.add(normalized)
                cleaned.append(place.strip())
        return cleaned

    def geocode_destinations(self, destinations, destinationIDs):
        """
        Geocodes each destination name using Google Maps API.
        Stores results as Location objects in self.locations and DB.
        """
        self.locations = []
        for dest,id in zip(destinations, destinationIDs):
            try:
                geocode = self.gmaps.geocode(dest.name)
                if geocode:
                    loc = geocode[0]["geometry"]["location"]
                    address = geocode[0]["formatted_address"]
                    # Create SQLAlchemy Location object
                    location_obj = Location(
                        destination_id=id,
                        lat=loc["lat"],
                        lng=loc["lng"],
                        place_id=geocode[0].get("place_id"),
                        address=address,
                    )
                    db.session.add(location_obj)
                    db.session.commit()
                    self.locations.append(location_obj)
                else:
                    print(f"[WARN] Could not geocode: {dest}")
            except Exception as e:
                print(f"[ERROR] Geocoding {dest} failed: {e}")
            time.sleep(0.1)  # To avoid rate limits

    def export_to_csv(self, filepath="destinations.csv"):
        """
        Exports stored Location objects to a CSV file.
        """
        with open(filepath, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["destination_id", "formatted_name", "lat", "lng", "place_id", "confidence"])
            writer.writeheader()
            for loc in self.locations:
                writer.writerow({
                    "destination_id": loc.destination_id,
                    "formatted_name": loc.formatted_name,
                    "lat": loc.lat,
                    "lng": loc.lng,
                    "place_id": loc.place_id,
                    "confidence": loc.confidence
                })
        print(f"[INFO] Exported {len(self.locations)} locations to {filepath}")

    def run(self, raw_destinations, destinationIDs):
        print(f"[INFO] Cleaned down to {len(raw_destinations)} unique destinations")
        self.geocode_destinations(raw_destinations, destinationIDs)
