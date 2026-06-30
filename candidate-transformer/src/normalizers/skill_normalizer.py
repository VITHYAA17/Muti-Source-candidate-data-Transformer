"""
Skill Normalizer - Standardizes skill names to canonical versions.
"""
from typing import Optional

class SkillNormalizer:
    """
    Standardizes colloquial, abbreviated, or inconsistent skill names.
    """

    # Canonical skill mappings
    CANONICAL_MAP = {
        "js": "JavaScript",
        "javascript": "JavaScript",
        "py": "Python",
        "python": "Python",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "ts": "TypeScript",
        "typescript": "TypeScript",
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "Google Cloud Platform",
        "google cloud": "Google Cloud Platform",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "docker": "Docker",
        "terraform": "Terraform",
        "ansible": "Ansible",
        "jenkins": "Jenkins",
        "git": "Git",
        "github": "GitHub",
        "node": "Node.js",
        "node.js": "Node.js",
        "react": "React",
        "reactjs": "React",
        "distributed systems": "Distributed Systems",
        "system design": "System Design",
        "microservices": "Microservices",
        "ci/cd": "CI/CD"
    }

    def normalize(self, skill_name: str) -> str:
        """
        Map a skill name to its canonical name.
        """
        if not skill_name:
            return ""
        
        cleaned = skill_name.strip()
        key = cleaned.lower()
        
        if key in self.CANONICAL_MAP:
            return self.CANONICAL_MAP[key]
            
        # Capitalize words as fallback for consistent aesthetics
        # but don't capitalize small words like 'and', 'or', 'of'
        words = cleaned.split()
        capitalized_words = []
        for i, word in enumerate(words):
            if word.lower() in ["and", "or", "of", "in", "on", "with", "to", "for", "by", "at"] and i > 0:
                capitalized_words.append(word.lower())
            else:
                # Keep words like iOS, AWS, API, etc. in uppercase
                if word.upper() in ["AWS", "API", "UI", "UX", "GCP", "SQL", "HTML", "CSS", "REST", "JSON", "XML", "CLI", "SDK"]:
                    capitalized_words.append(word.upper())
                else:
                    capitalized_words.append(word.capitalize())
                    
        return " ".join(capitalized_words)
