"""
Conflict Resolver - Resolves conflicts when merging candidate records based on source priority.
"""
from typing import Any, Dict, List, Optional
from ..models import Candidate, Location, Links

class ConflictResolver:
    """
    Resolves data conflicts during duplicate candidate merging.
    Uses priority hierarchy: Resume > ATS = GitHub = CSV > LinkedIn > Text.
    """

    # Numeric representation of source trust priority
    SOURCE_PRIORITY = {
        "Resume": 60,
        "ATS": 50,
        "GitHub": 50,
        "CSV": 50,
        "LinkedIn": 30,
        "Text": 10
    }

    def resolve_field(self, candidates_sorted: List[Candidate], field_name: str) -> Any:
        """
        Returns the field value from the highest priority candidate that has a non-empty value.
        """
        for c in candidates_sorted:
            val = getattr(c, field_name, None)
            if val:
                return val
        return None

    def resolve_location(self, candidates_sorted: List[Candidate]) -> Location:
        """
        Merges location by picking non-empty city, region, and country from the highest priority sources.
        """
        city, region, country = None, None, None
        for c in candidates_sorted:
            if c.location:
                if not city and c.location.city:
                    city = c.location.city
                if not region and c.location.region:
                    region = c.location.region
                if not country and c.location.country:
                    country = c.location.country
        return Location(city=city, region=region, country=country)

    def resolve_links(self, candidates_sorted: List[Candidate]) -> Links:
        """
        Merges Links, resolving primary URLs by priority and accumulating others.
        """
        linkedin, github, portfolio = None, None, None
        other_links = []

        for c in candidates_sorted:
            if c.links:
                if not linkedin and c.links.linkedin:
                    linkedin = c.links.linkedin
                if not github and c.links.github:
                    github = c.links.github
                if not portfolio and c.links.portfolio:
                    portfolio = c.links.portfolio
                for other in c.links.other:
                    if other and other not in other_links:
                        other_links.append(other)

        # Remove primary URLs from other_links
        primaries = {linkedin, github, portfolio}
        other_links = [l for l in other_links if l not in primaries]

        return Links(linkedin=linkedin, github=github, portfolio=portfolio, other=other_links)
