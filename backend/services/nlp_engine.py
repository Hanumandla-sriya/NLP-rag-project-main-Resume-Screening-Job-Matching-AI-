import spacy
import re
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NLPEngine:
    """NLP service for extracting structured information from resume text"""
    
    def __init__(self):
        """
        Initialize NLP engine with spaCy model
        
        Args:
            model_name: Name of the spaCy model to use
        """

    
    def extract_skills(self, text: str, common_skills: Optional[List[str]] = None) -> List[str]:
        """
        Extract skills from resume text
        
        Args:
            text: Resume text
            common_skills: Optional list of common skills to look for
            
        Returns:
            List of extracted skills
        """
        if common_skills is None:
            common_skills = [
                'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'postgresql',
                'mongodb', 'docker', 'kubernetes', 'aws', 'azure', 'git', 'linux',
                'machine learning', 'deep learning', 'nlp', 'data science', 'tensorflow',
                'pytorch', 'fastapi', 'django', 'flask', 'html', 'css', 'typescript',
                'angular', 'vue', 'rest api', 'graphql', 'microservices', 'ci/cd',
                'agile', 'scrum', 'project management'
            ]
        
        skills_found = []
        text_lower = text.lower()
        
        # Check for common skills
        for skill in common_skills:
            if skill.lower() in text_lower:
                skills_found.append(skill)
        
        # Use NER to find potential skills (ORG entities often indicate technologies)
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"]:
                # Filter out common non-skill organizations
                if ent.text.lower() not in ['university', 'college', 'inc', 'ltd', 'corp']:
                    if len(ent.text) > 2 and ent.text.lower() not in [s.lower() for s in skills_found]:
                        skills_found.append(ent.text)
        
        # Remove duplicates and return
        return list(set(skills_found))
    
    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract work experience from resume text
        
        Args:
            text: Resume text
            
        Returns:
            List of experience entries with company, role, dates, etc.
        """
        experience_entries = []
        
        # Pattern to match dates (e.g., "Jan 2020 - Present", "2020-2023")
        date_pattern = r'(\d{4}|\w+\s+\d{4})\s*[-–—]\s*(\d{4}|\w+\s+\d{4}|Present|present|Current|current)'
        
        # Split text into lines
        lines = text.split('\n')
        
        current_entry = {}
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains date pattern (likely an experience entry)
            dates = re.findall(date_pattern, line)
            if dates:
                # Save previous entry if exists
                if current_entry:
                    experience_entries.append(current_entry)
                
                # Start new entry
                current_entry = {
                    'dates': dates[0] if dates else None,
                    'description': []
                }
                
                # Try to extract role/company from surrounding lines
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if prev_line and len(prev_line) < 100:
                        current_entry['role'] = prev_line
                
                if i < len(lines) - 1:
                    next_line = lines[i+1].strip()
                    if next_line and len(next_line) < 100 and 'role' not in current_entry:
                        current_entry['company'] = next_line
            
            elif current_entry:
                # Add description lines
                if len(line) > 20:  # Likely a description line
                    current_entry['description'].append(line)
        
        # Add last entry
        if current_entry:
            experience_entries.append(current_entry)
        
        # Clean up entries
        cleaned_entries = []
        for entry in experience_entries:
            cleaned = {
                'dates': entry.get('dates'),
                'role': entry.get('role', 'Unknown'),
                'company': entry.get('company', 'Unknown'),
                'description': ' '.join(entry.get('description', []))[:500]  # Limit description length
            }
            cleaned_entries.append(cleaned)
        
        return cleaned_entries
    
    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract education information from resume text
        
        Args:
            text: Resume text
            
        Returns:
            List of education entries
        """
        education_entries = []
        
        # Keywords that indicate education sections
        education_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'degree', 'university', 
                             'college', 'diploma', 'certificate', 'b.sc', 'm.sc', 'b.tech', 'm.tech']
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains education keywords
            if any(keyword in line_lower for keyword in education_keywords):
                entry = {
                    'institution': '',
                    'degree': '',
                    'field': '',
                    'year': None
                }
                
                # Extract degree and institution
                doc = self.nlp(line)
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        entry['institution'] = ent.text
                
                # Look for degree type
                if 'bachelor' in line_lower or 'b.sc' in line_lower or 'b.tech' in line_lower:
                    entry['degree'] = 'Bachelor'
                elif 'master' in line_lower or 'm.sc' in line_lower or 'm.tech' in line_lower:
                    entry['degree'] = 'Master'
                elif 'phd' in line_lower or 'doctorate' in line_lower:
                    entry['degree'] = 'PhD'
                
                # Extract year
                year_match = re.search(r'\d{4}', line)
                if year_match:
                    entry['year'] = int(year_match.group())
                
                # Get field of study from line or next line
                if not entry['field']:
                    # Try to extract field (usually after degree type)
                    field_match = re.search(r'(?:in|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line)
                    if field_match:
                        entry['field'] = field_match.group(1)
                
                if entry['degree'] or entry['institution']:
                    education_entries.append(entry)
        
        return education_entries
    
    def process_resume(self, text: str) -> Dict[str, Any]:
        """
        Process resume text and extract all information
        
        Args:
            text: Raw resume text
            
        Returns:
            Dictionary with extracted skills, experience, and education
        """
        return {
            'skills': self.extract_skills(text),
            'experience': self.extract_experience(text),
            'education': self.extract_education(text)
        }

if __name__ == "__main__":
    my_engine = NLPEngine()
    resume_text = """
        Experienced Python developer with strong knowledge of Django, FastAPI, 
        PostgreSQL, Docker, and AWS. Worked on machine learning and NLP projects.
        """
    skills = my_engine.extract_skills(resume_text)
    print("The Extracted skills :",skills)
