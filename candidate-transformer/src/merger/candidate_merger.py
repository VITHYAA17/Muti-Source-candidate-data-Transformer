"""
Candidate Merger - Merges candidate records using priority-based conflict resolution.
"""
from typing import List, Dict, Optional
import uuid
from ..models import Candidate, Location, Links, Skill, Experience, Education, Provenance

# Source priorities as defined in README/DESIGN
SOURCE_PRIORITY = {
    "Resume": 60,
    "ATS": 50,
    "GitHub": 50,
    "CSV": 50,
    "LinkedIn": 30,
    "Text": 10
}

class CandidateMerger:
    """
    Merges a list of Candidate objects representing the same person.
    Uses priority-based merging for conflicting fields.
    """

    def merge_candidates(self, candidates: List[Candidate]) -> Candidate:
        """
        Merge a group of candidates.
        
        Args:
            candidates: List of Candidate objects to merge
            
        Returns:
            A single merged Candidate object
        """
        if not candidates:
            raise ValueError("Cannot merge empty candidate list")
            
        if len(candidates) == 1:
            return candidates[0]

        # Sort candidates by priority (highest first)
        candidates_sorted = sorted(
            candidates, 
            key=lambda c: SOURCE_PRIORITY.get(c.source, 0), 
            reverse=True
        )

        merged = Candidate(
            candidate_id=str(uuid.uuid4()),
            source="Merged"
        )

        # 1. Merge basic fields by priority
        merged.full_name = self._get_priority_field(candidates_sorted, "full_name")
        merged.headline = self._get_priority_field(candidates_sorted, "headline")
        merged.years_experience = self._get_priority_field(candidates_sorted, "years_experience")

        # 2. Merge emails & phones (unique list preserving order of priority)
        emails = []
        phones = []
        for c in candidates_sorted:
            for email in c.emails:
                if email and email.lower().strip() not in [e.lower().strip() for e in emails]:
                    emails.append(email.strip())
            for phone in c.phones:
                if phone and phone.strip() not in [p.strip() for p in phones]:
                    phones.append(phone.strip())
        merged.emails = emails
        merged.phones = phones

        # 3. Merge Location
        merged.location = self._merge_location(candidates_sorted)

        # 4. Merge Links
        merged.links = self._merge_links(candidates_sorted)

        # 5. Merge Skills
        # Add all skills to the candidate. Candidate.add_skill already merges sources and confidence
        for c in candidates_sorted:
            for skill in c.skills:
                # Re-create skill object to avoid modifying the original parsed candidates
                new_skill = Skill(
                    name=skill.name,
                    confidence=skill.confidence,
                    sources=list(skill.sources)
                )
                merged.add_skill(new_skill)

        # 6. Merge Experience
        merged.experience = self._merge_experience(candidates_sorted)

        # 7. Merge Education
        merged.education = self._merge_education(candidates_sorted)

        # 8. Merge Provenance tracking
        for c in candidates_sorted:
            for field_name, prov_list in c.provenance.items():
                if field_name not in merged.provenance:
                    merged.provenance[field_name] = []
                for prov in prov_list:
                    # Avoid exact duplicate provenances
                    if prov not in merged.provenance[field_name]:
                        merged.provenance[field_name].append(prov)

        return merged

    def _get_priority_field(self, sorted_candidates: List[Candidate], field_name: str):
        """Get the first non-empty field value from candidates sorted by priority."""
        for c in sorted_candidates:
            val = getattr(c, field_name, None)
            if val:
                return val
        return None

    def _merge_location(self, sorted_candidates: List[Candidate]) -> Location:
        """
        Merge location. Take values from the highest priority candidate
        that has location details.
        """
        city, region, country = None, None, None
        for c in sorted_candidates:
            if c.location:
                if not city and c.location.city:
                    city = c.location.city
                if not region and c.location.region:
                    region = c.location.region
                if not country and c.location.country:
                    country = c.location.country
        return Location(city=city, region=region, country=country)

    def _merge_links(self, sorted_candidates: List[Candidate]) -> Links:
        """
        Merge Links. Take primary links from highest priority, and accumulate other links.
        """
        linkedin, github, portfolio = None, None, None
        other_links = []

        for c in sorted_candidates:
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
                        
        # Ensure we don't duplicate primary links in the other list
        primaries = {linkedin, github, portfolio}
        other_links = [l for l in other_links if l not in primaries]

        return Links(linkedin=linkedin, github=github, portfolio=portfolio, other=other_links)

    def _merge_experience(self, sorted_candidates: List[Candidate]) -> List[Experience]:
        """
        Merge experience lists. Group by company + title.
        """
        merged_exp: List[Experience] = []
        
        for c in sorted_candidates:
            for exp in c.experience:
                if not exp.company:
                    continue
                    
                # Look for matching company & title in already merged experience
                match = None
                exp_company_clean = exp.company.lower().strip()
                exp_title_clean = (exp.title or "").lower().strip()
                
                for me in merged_exp:
                    me_company_clean = me.company.lower().strip()
                    me_title_clean = (me.title or "").lower().strip()
                    
                    # Match if companies match, and either titles match or one is missing
                    if me_company_clean == exp_company_clean:
                        if me_title_clean == exp_title_clean or not me_title_clean or not exp_title_clean:
                            match = me
                            break
                            
                if match:
                    # Update fields if empty in the current match (which is higher priority)
                    if not match.title and exp.title:
                        match.title = exp.title
                    if not match.start_date and exp.start_date:
                        match.start_date = exp.start_date
                    if not match.end_date and exp.end_date:
                        match.end_date = exp.end_date
                    if not match.summary and exp.summary:
                        match.summary = exp.summary
                else:
                    # Create a new Experience copy
                    merged_exp.append(
                        Experience(
                            company=exp.company,
                            title=exp.title,
                            start_date=exp.start_date,
                            end_date=exp.end_date,
                            summary=exp.summary
                        )
                    )
        return merged_exp

    def _merge_education(self, sorted_candidates: List[Candidate]) -> List[Education]:
        """
        Merge education lists. Group by institution + degree.
        """
        merged_edu: List[Education] = []
        
        for c in sorted_candidates:
            for edu in c.education:
                if not edu.institution:
                    continue
                    
                match = None
                edu_inst_clean = edu.institution.lower().strip()
                edu_deg_clean = (edu.degree or "").lower().strip()
                
                for me in merged_edu:
                    me_inst_clean = me.institution.lower().strip()
                    me_deg_clean = (me.degree or "").lower().strip()
                    
                    if me_inst_clean == edu_inst_clean:
                        if me_deg_clean == edu_deg_clean or not me_deg_clean or not edu_deg_clean:
                            match = me
                            break
                            
                if match:
                    if not match.degree and edu.degree:
                        match.degree = edu.degree
                    if not match.field and edu.field:
                        match.field = edu.field
                    if not match.end_year and edu.end_year:
                        match.end_year = edu.end_year
                else:
                    merged_edu.append(
                        Education(
                            institution=edu.institution,
                            degree=edu.degree,
                            field=edu.field,
                            end_year=edu.end_year
                        )
                    )
        return merged_edu
