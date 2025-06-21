import os
import csv
import time
import googlemaps
from difflib import get_close_matches
from dataclasses import dataclass
from typing import List

@dataclass
class Location:
    name: str
    lat: float
    lng: float
    address: str
    description: str = ""

class MapDestinationExporter:
    def __init__(self, api_key: str):
        self.gmaps = googlemaps.Client(key=api_key)
        self.locations: List[Location] = []

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

    def geocode_destinations(self, destinations):
        """
        Geocodes each destination name using Google Maps API.
        Stores results as Location objects in self.locations.
        """
        self.locations = []
        for dest in destinations:
            try:
                geocode = self.gmaps.geocode(dest.name)
                if geocode:
                    loc = geocode[0]["geometry"]["location"]
                    address = geocode[0]["formatted_address"]
                    self.locations.append(Location(
                        name=dest.name,
                        lat=loc["lat"],
                        lng=loc["lng"],
                        address=address,
                        description=dest.description
                    ))
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
            writer = csv.DictWriter(f, fieldnames=["name", "address", "lat", "lng", "description"])
            writer.writeheader()
            for loc in self.locations:
                writer.writerow({
                    "name": loc.name,
                    "address": loc.address,
                    "lat": loc.lat,
                    "lng": loc.lng,
                    "description": loc.description
                })
        print(f"[INFO] Exported {len(self.locations)} locations to {filepath}")

    def run(self, raw_destinations):
        print(f"[INFO] Cleaned down to {len(raw_destinations)} unique destinations")
        self.geocode_destinations(raw_destinations)
