"""
Location Normalizer - Standardizes location strings to structured city, region, country.
"""
from typing import Optional
from ..models import Location

class LocationNormalizer:
    """
    Parses and normalizes location names into city, region (state), and country.
    Maps region names to standard codes (e.g. California -> CA) and country names to ISO-3166 alpha-2.
    """

    # US State mappings
    US_STATES = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
        "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
        "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
        "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
        "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
        "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
        "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH",
        "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
        "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
        "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY"
    }

    # Country mappings
    COUNTRIES = {
        "usa": "US",
        "united states": "US",
        "united states of america": "US",
        "us": "US",
        "united kingdom": "GB",
        "uk": "GB",
        "great britain": "GB",
        "canada": "CA",
        "india": "IN",
        "germany": "DE",
        "france": "FR"
    }

    # Cities to states mapping for US cities in input files
    CITY_STATE_MAP = {
        "mountain view": "CA",
        "menlo park": "CA",
        "cupertino": "CA",
        "san francisco": "CA",
        "san jose": "CA",
        "seattle": "WA",
        "redmond": "WA",
    }

    def normalize(self, loc: Location) -> Location:
        """
        Normalize a Location object.
        """
        if not loc:
            return Location()

        city = loc.city.strip() if loc.city else None
        region = loc.region.strip() if loc.region else None
        country = loc.country.strip() if loc.country else None

        # Handle cities that have commas in them e.g. "San Francisco, CA" stored in city
        if city and not region and not country:
            parts = [p.strip() for p in city.split(",")]
            if len(parts) == 2:
                city = parts[0]
                region = parts[1]
            elif len(parts) == 3:
                city = parts[0]
                region = parts[1]
                country = parts[2]

        # Standardize region
        if region:
            reg_lower = region.lower()
            if reg_lower in self.US_STATES:
                region = self.US_STATES[reg_lower]
            elif reg_lower in [v.lower() for v in self.US_STATES.values()]:
                region = region.upper()
        
        # Standardize country
        if country:
            c_lower = country.lower()
            if c_lower in self.COUNTRIES:
                country = self.COUNTRIES[c_lower]
            elif len(country) == 2:
                country = country.upper()

        # If region is missing but city is a known city, infer state/region
        if city and not region:
            city_lower = city.lower()
            if city_lower in self.CITY_STATE_MAP:
                region = self.CITY_STATE_MAP[city_lower]

        # If region is a US state and country is missing, infer USA (US)
        if region and region.upper() in self.US_STATES.values() and not country:
            country = "US"

        # Tidy up strings
        city = city.title() if city else None
        region = region.upper() if region else None
        country = country.upper() if country else None

        return Location(city=city, region=region, country=country)
