import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for matching resumes with job descriptions using semantic similarity"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize matching service with sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            return [0.0] * 384  # Default dimension for all-MiniLM-L6-v2
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def calculate_semantic_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        
        similarity = cosine_similarity(vec1, vec2)[0][0]
        return float(similarity)
    
    def calculate_skill_match_score(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """
        Calculate skill matching score
        
        Args:
            resume_skills: List of skills from resume
            job_skills: List of required/preferred skills from job
            
        Returns:
            Skill match score between 0 and 1
        """
        if not job_skills:
            return 1.0  # If no skills specified, give full score
        
        if not resume_skills:
            return 0.0
        
        # Normalize skills to lowercase for comparison
        resume_skills_lower = [s.lower().strip() for s in resume_skills]
        job_skills_lower = [s.lower().strip() for s in job_skills]
        
        # Calculate intersection
        matched_skills = set(resume_skills_lower) & set(job_skills_lower)
        
        # Score = matched skills / total required skills
        score = len(matched_skills) / len(job_skills_lower) if job_skills_lower else 0.0
        
        return min(score, 1.0)  # Cap at 1.0
    
    def calculate_experience_score(self, resume_experience: List[Dict], job_experience_level: Optional[str] = None) -> float:
        """
        Calculate experience relevance score
        
        Args:
            resume_experience: List of experience entries from resume
            job_experience_level: Required experience level (entry/mid/senior)
            
        Returns:
            Experience score between 0 and 1
        """
        if not resume_experience:
            return 0.0
        
        # Count years of experience (rough estimate)
        total_years = len(resume_experience)  # Simplified: each entry = ~1-2 years
        
        # Score based on experience level
        if job_experience_level:
            level = job_experience_level.lower()
            if level == 'entry' and total_years >= 0:
                return min(total_years / 2, 1.0)
            elif level == 'mid' and total_years >= 2:
                return min((total_years - 2) / 3, 1.0)
            elif level == 'senior' and total_years >= 5:
                return min((total_years - 5) / 5, 1.0)
        
        # Default: score based on having experience
        return min(total_years / 5, 1.0)
    
    def calculate_education_score(self, resume_education: List[Dict], job_requirements: Optional[Dict] = None) -> float:
        """
        Calculate education alignment score
        
        Args:
            resume_education: List of education entries from resume
            job_requirements: Optional job education requirements
            
        Returns:
            Education score between 0 and 1
        """
        if not resume_education:
            return 0.5  # Neutral score if no education info
        
        # If education exists, give base score
        has_degree = any(edu.get('degree') for edu in resume_education)
        
        if has_degree:
            return 1.0
        
        return 0.5
    
    def calculate_overall_score(
        self,
        semantic_similarity: float,
        skill_match: float,
        experience_score: float,
        education_score: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate weighted overall matching score
        
        Args:
            semantic_similarity: Semantic similarity score
            skill_match: Skill matching score
            experience_score: Experience score
            education_score: Education score
            weights: Optional custom weights for each factor
            
        Returns:
            Overall score between 0 and 1
        """
        if weights is None:
            weights = {
                'semantic': 0.4,
                'skills': 0.3,
                'experience': 0.2,
                'education': 0.1
            }
        
        overall = (
            semantic_similarity * weights['semantic'] +
            skill_match * weights['skills'] +
            experience_score * weights['experience'] +
            education_score * weights['education']
        )
        
        return float(overall)
    
    def match_resume_to_job(
        self,
        resume_text: str,
        resume_skills: List[str],
        resume_experience: List[Dict],
        resume_education: List[Dict],
        job_description: str,
        job_skills: List[str],
        job_experience_level: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Match a resume to a job description and return scores
        
        Args:
            resume_text: Full text of the resume
            resume_skills: Skills extracted from resume
            resume_experience: Experience entries from resume
            resume_education: Education entries from resume
            job_description: Job description text
            job_skills: Required/preferred skills for the job
            job_experience_level: Required experience level
            
        Returns:
            Dictionary with all matching scores
        """
        # Generate embeddings
        resume_embedding = self.generate_embedding(resume_text)
        job_embedding = self.generate_embedding(job_description)
        
        # Calculate semantic similarity
        semantic_sim = self.calculate_semantic_similarity(resume_embedding, job_embedding)
        
        # Calculate skill match
        skill_match = self.calculate_skill_match_score(resume_skills, job_skills)
        
        # Calculate experience score
        experience_score = self.calculate_experience_score(resume_experience, job_experience_level)
        
        # Calculate education score
        education_score = self.calculate_education_score(resume_education)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(
            semantic_sim, skill_match, experience_score, education_score
        )
        
        return {
            'overall_score': overall_score,
            'semantic_similarity': semantic_sim,
            'skill_match_score': skill_match,
            'experience_score': experience_score,
            'education_score': education_score,
            'resume_embedding': resume_embedding,
            'job_embedding': job_embedding
        }
