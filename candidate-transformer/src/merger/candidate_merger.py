"""
Candidate Merger - Merges candidate records using ConflictResolver.
"""
from typing import List
import uuid
from ..models import Candidate, Skill, Experience, Education
from .conflict_resolver import ConflictResolver

class CandidateMerger:
    """
    Merges duplicate Candidates. Delegates field-level resolution to ConflictResolver.
    """

    def __init__(self):
        self.conflict_resolver = ConflictResolver()

    def merge_candidates(self, candidates: List[Candidate]) -> Candidate:
        """
        Merge duplicate Candidate profiles.
        """
        if not candidates:
            raise ValueError("Cannot merge empty candidate list")
            
        if len(candidates) == 1:
            return candidates[0]

        # Sort candidates by source priority descending
        candidates_sorted = sorted(
            candidates, 
            key=lambda c: self.conflict_resolver.SOURCE_PRIORITY.get(c.source, 0), 
            reverse=True
        )

        merged = Candidate(
            candidate_id=str(uuid.uuid4()),
            source="Merged"
        )

        # 1. Basic properties
        merged.full_name = self.conflict_resolver.resolve_field(candidates_sorted, "full_name")
        merged.headline = self.conflict_resolver.resolve_field(candidates_sorted, "headline")
        merged.years_experience = self.conflict_resolver.resolve_field(candidates_sorted, "years_experience")

        # 2. Lists of strings (emails & phones)
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

        # 3. Location and Links
        merged.location = self.conflict_resolver.resolve_location(candidates_sorted)
        merged.links = self.conflict_resolver.resolve_links(candidates_sorted)

        # 4. Skills (Candidate.add_skill merges sources and trust)
        for c in candidates_sorted:
            for skill in c.skills:
                new_skill = Skill(
                    name=skill.name,
                    confidence=skill.confidence,
                    sources=list(skill.sources)
                )
                merged.add_skill(new_skill)

        # 5. Experience
        merged.experience = self._merge_experience(candidates_sorted)

        # 6. Education
        merged.education = self._merge_education(candidates_sorted)

        # 7. Provenance
        for c in candidates_sorted:
            for field_name, prov_list in c.provenance.items():
                if field_name not in merged.provenance:
                    merged.provenance[field_name] = []
                for prov in prov_list:
                    if prov not in merged.provenance[field_name]:
                        merged.provenance[field_name].append(prov)

        return merged

    def _merge_experience(self, sorted_candidates: List[Candidate]) -> List[Experience]:
        """
        Merge experience lists grouping by company and job title.
        """
        merged_exp: List[Experience] = []
        
        for c in sorted_candidates:
            for exp in c.experience:
                if not exp.company:
                    continue
                    
                match = None
                exp_company_clean = exp.company.lower().strip()
                exp_title_clean = (exp.title or "").lower().strip()
                
                for me in merged_exp:
                    me_company_clean = me.company.lower().strip()
                    me_title_clean = (me.title or "").lower().strip()
                    
                    if me_company_clean == exp_company_clean:
                        if me_title_clean == exp_title_clean or not me_title_clean or not exp_title_clean:
                            match = me
                            break
                            
                if match:
                    if not match.title and exp.title:
                        match.title = exp.title
                    if not match.start_date and exp.start_date:
                        match.start_date = exp.start_date
                    if not match.end_date and exp.end_date:
                        match.end_date = exp.end_date
                    if not match.summary and exp.summary:
                        match.summary = exp.summary
                else:
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
        Merge education lists grouping by school/university and degree.
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
