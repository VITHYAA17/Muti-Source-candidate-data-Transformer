"""
Candidate Matcher - Identifies duplicate candidates across different sources.
"""
from typing import List, Set
from ..models import Candidate

class CandidateMatcher:
    """
    Groups candidate records that refer to the same physical person.
    Matches are transitive: if A matches B, and B matches C, then A, B, and C are grouped.
    """

    def match_candidates(self, candidates: List[Candidate]) -> List[List[Candidate]]:
        """
        Groups duplicate candidates.
        
        Args:
            candidates: List of Candidate objects to be grouped
            
        Returns:
            List of lists of Candidate objects, where each sublist represents a single candidate.
        """
        if not candidates:
            return []

        n = len(candidates)
        parent = list(range(n))

        def find(i: int) -> int:
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i: int, j: int) -> None:
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        # Compare every pair of candidates to see if they represent the same person
        for i in range(n):
            c1 = candidates[i]
            for j in range(i + 1, n):
                c2 = candidates[j]
                
                # Match by email (case-insensitive)
                email_match = False
                if c1.emails and c2.emails:
                    emails1 = {e.strip().lower() for e in c1.emails if e}
                    emails2 = {e.strip().lower() for e in c2.emails if e}
                    if emails1.intersection(emails2):
                        email_match = True

                # Match by phone number (clean non-digits or compare exact E.164 strings)
                phone_match = False
                if c1.phones and c2.phones:
                    # Compare digits only to be safe with minor format variations
                    phones1 = {"".join(c for c in p if c.isdigit()) for p in c1.phones if p}
                    phones2 = {"".join(c for c in p if c.isdigit()) for p in c2.phones if p}
                    # Filter out empty or too short strings
                    phones1 = {p for p in phones1 if len(p) >= 7}
                    phones2 = {p for p in phones2 if len(p) >= 7}
                    if phones1.intersection(phones2):
                        phone_match = True

                if email_match or phone_match:
                    union(i, j)

        # Build the final groups based on disjoint set roots
        groups = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(candidates[i])

        return list(groups.values())
