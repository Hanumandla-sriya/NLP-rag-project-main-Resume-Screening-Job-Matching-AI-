"""
Resume-to-job matching service.

Calculates:
- Semantic similarity
- Skill matching
- Experience matching
- Education matching
- Weighted overall score

All internal scores are normalized between 0.0 and 1.0.
The frontend should multiply these values by 100 when displaying percentages.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.config import settings


logger = logging.getLogger(__name__)


class MatchingService:
    """Service for calculating resume-to-job compatibility scores."""

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "semantic": 0.30,
        "skills": 0.40,
        "experience": 0.20,
        "education": 0.10,
    }

    EMBEDDING_DIMENSION = 384

    EXPERIENCE_REQUIREMENTS: Dict[str, float] = {
        "fresher": 0.0,
        "entry": 0.0,
        "entry-level": 0.0,
        "entry level": 0.0,
        "junior": 0.0,
        "mid": 2.0,
        "mid-level": 2.0,
        "mid level": 2.0,
        "senior": 5.0,
        "senior-level": 5.0,
        "senior level": 5.0,
    }

    # Common variations of skills.
    SKILL_ALIASES: Dict[str, str] = {
        "python programming": "python",
        "python programming language": "python",
        "sql database": "sql",
        "structured query language": "sql",
        "machine learning": "machine learning",
        "ml": "machine learning",
        "deep learning": "deep learning",
        "dl": "deep learning",
        "natural language processing": "nlp",
        "natural language processing (nlp)": "nlp",
        "exploratory data analysis": "eda",
        "exploratory data analysis (eda)": "eda",
        "power bi": "power bi",
        "powerbi": "power bi",
        "scikit learn": "scikit-learn",
        "sklearn": "scikit-learn",
        "scikit_learn": "scikit-learn",
        "numpy": "numpy",
        "pandas": "pandas",
        "tensorflow": "tensorflow",
        "pytorch": "pytorch",
        "opencv": "opencv",
        "generative ai": "generative ai",
        "gen ai": "generative ai",
    }

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = (
            model_name or settings.SENTENCE_TRANSFORMER_MODEL
        )

        self.model = self._load_model()

    def _load_model(self) -> SentenceTransformer:
        """Load Sentence Transformer model."""
        try:
            model = SentenceTransformer(self.model_name)

            logger.info(
                "Successfully loaded Sentence Transformer model: %s",
                self.model_name,
            )

            return model

        except Exception as exc:
            logger.exception(
                "Failed to load Sentence Transformer model '%s'.",
                self.model_name,
            )

            raise RuntimeError(
                f"Failed to load Sentence Transformer model "
                f"'{self.model_name}'."
            ) from exc

    # ------------------------------------------------------------------
    # TEXT / SKILL NORMALIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(text: Optional[str]) -> str:
        """Normalize text before embedding."""
        if not text:
            return ""

        return re.sub(r"\s+", " ", str(text)).strip()

    @classmethod
    def _normalize_skill(cls, skill: str) -> str:
        """Normalize an individual skill."""

        if not skill:
            return ""

        value = str(skill).strip().lower()

        # Remove bullets and unnecessary punctuation.
        value = re.sub(r"^[•●▪◦\-\*\s]+", "", value)
        value = re.sub(r"\s+", " ", value)

        # Remove surrounding punctuation.
        value = value.strip(".,;:|/")

        # Apply aliases.
        value = cls.SKILL_ALIASES.get(value, value)

        return value

    @classmethod
    def _normalize_skills(
        cls,
        skills: Optional[Sequence[str]],
    ) -> set[str]:
        """
        Convert skills into a normalized set.

        Handles:
        - lists
        - tuples
        - comma-separated strings
        - semicolon-separated strings
        - newline-separated strings
        """

        if not skills:
            return set()

        # Sometimes the parser returns a single string instead
        # of a list. Handle that safely.
        if isinstance(skills, str):
            raw_skills = re.split(r"[,;\n|]+", skills)
        else:
            raw_skills = []

            for skill in skills:
                if not skill:
                    continue

                # Handle accidental comma-separated items.
                parts = re.split(r"[,;\n|]+", str(skill))
                raw_skills.extend(parts)

        normalized = set()

        for skill in raw_skills:
            cleaned = cls._normalize_skill(skill)

            if cleaned:
                normalized.add(cleaned)

        return normalized

    @staticmethod
    def _clamp_score(score: float) -> float:
        """Ensure a score remains between 0 and 1."""
        return max(0.0, min(float(score), 1.0))

    # ------------------------------------------------------------------
    # EMBEDDINGS
    # ------------------------------------------------------------------

    def generate_embedding(
        self,
        text: str,
    ) -> List[float]:
        """Generate a semantic embedding."""

        normalized_text = self._normalize_text(text)

        if not normalized_text:
            return [0.0] * self.EMBEDDING_DIMENSION

        try:
            embedding = self.model.encode(
                normalized_text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            return embedding.astype(float).tolist()

        except Exception as exc:
            logger.exception(
                "Failed to generate text embedding."
            )

            raise RuntimeError(
                "Failed to generate text embedding."
            ) from exc

    def generate_embeddings(
        self,
        texts: Sequence[str],
    ) -> List[List[float]]:
        """Generate multiple embeddings."""

        normalized_texts = [
            self._normalize_text(text)
            for text in texts
        ]

        if not normalized_texts:
            return []

        try:
            embeddings = self.model.encode(
                normalized_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            return embeddings.astype(float).tolist()

        except Exception as exc:
            logger.exception(
                "Failed to generate text embeddings."
            )

            raise RuntimeError(
                "Failed to generate text embeddings."
            ) from exc

    def calculate_semantic_similarity(
        self,
        embedding1: Sequence[float],
        embedding2: Sequence[float],
    ) -> float:
        """
        Calculate cosine similarity.

        Because Sentence Transformers embeddings are normalized,
        cosine similarity is naturally in approximately [-1, 1].

        We convert it to [0, 1] for scoring.
        """

        if not embedding1 or not embedding2:
            return 0.0

        vector1 = np.asarray(
            embedding1,
            dtype=float,
        ).reshape(1, -1)

        vector2 = np.asarray(
            embedding2,
            dtype=float,
        ).reshape(1, -1)

        if vector1.shape[1] != vector2.shape[1]:
            raise ValueError(
                "Embedding dimensions do not match."
            )

        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = cosine_similarity(
            vector1,
            vector2,
        )[0][0]

        # Convert [-1, 1] -> [0, 1].
        normalized_similarity = (
            float(similarity) + 1.0
        ) / 2.0

        return self._clamp_score(
            normalized_similarity
        )

    # ------------------------------------------------------------------
    # SKILL MATCHING
    # ------------------------------------------------------------------

    def get_skill_match_details(
        self,
        resume_skills: Optional[Sequence[str]],
        job_skills: Optional[Sequence[str]],
    ) -> Dict[str, List[str]]:
        """Return matched and missing skills."""

        resume_set = self._normalize_skills(
            resume_skills
        )

        job_set = self._normalize_skills(
            job_skills
        )

        matched_skills = sorted(
            resume_set.intersection(job_set)
        )

        missing_skills = sorted(
            job_set.difference(resume_set)
        )

        return {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        }

    def calculate_skill_match_score(
        self,
        resume_skills: Optional[Sequence[str]],
        job_skills: Optional[Sequence[str]],
    ) -> float:
        """
        Calculate required skill coverage.

        Example:

        Resume:
            Python, SQL, Pandas, NumPy

        Job:
            Python, SQL, Pandas, NumPy, Power BI

        Score:
            4 / 5 = 0.80
        """

        resume_set = self._normalize_skills(
            resume_skills
        )

        job_set = self._normalize_skills(
            job_skills
        )

        if not job_set:
            return 1.0

        if not resume_set:
            return 0.0

        matched_skills = resume_set.intersection(
            job_set
        )

        return self._clamp_score(
            len(matched_skills) / len(job_set)
        )

    # ------------------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------------------

    def calculate_experience_years(
        self,
        resume_experience: Optional[
            Sequence[Dict[str, Any]]
        ],
    ) -> float:
        """Estimate total professional experience."""

        if not resume_experience:
            return 0.0

        total_months = 0

        for entry in resume_experience:

            if not isinstance(entry, dict):
                continue

            dates = entry.get("dates")

            if not dates or not isinstance(
                dates,
                (tuple, list),
            ):
                continue

            if len(dates) != 2:
                continue

            start_date, end_date = dates

            start_year = self._extract_year(
                start_date
            )

            end_year = self._extract_year(
                end_date
            )

            if start_year is None:
                continue

            if str(end_date).strip().lower() in {
                "present",
                "current",
                "now",
            }:
                end_year = datetime.now().year

            if (
                end_year is None
                or end_year < start_year
            ):
                continue

            total_months += (
                end_year - start_year
            ) * 12

        # If experience entries exist but dates could not
        # be parsed, do not invent 6 months per entry.
        return round(
            total_months / 12.0,
            2,
        )

    @staticmethod
    def _extract_year(
        value: Any,
    ) -> Optional[int]:
        """Extract a four-digit year from a date."""

        if value is None:
            return None

        match = re.search(
            r"\b(?:19|20)\d{2}\b",
            str(value),
        )

        return (
            int(match.group())
            if match
            else None
        )

    def calculate_experience_score(
        self,
        resume_experience: Optional[
            Sequence[Dict[str, Any]]
        ],
        job_experience_level: Optional[str] = None,
    ) -> float:
        """Calculate experience compatibility."""

        experience_years = (
            self.calculate_experience_years(
                resume_experience
            )
        )

        if not job_experience_level:
            # No requirement: experience should not
            # unfairly penalize a fresher.
            return 1.0

        level = (
            str(job_experience_level)
            .strip()
            .lower()
        )

        required_years = (
            self.EXPERIENCE_REQUIREMENTS.get(level)
        )

        if required_years is None:

            # Try to extract explicit years such as:
            # "2+ years", "3 years experience".
            year_match = re.search(
                r"(\d+(?:\.\d+)?)\s*\+?\s*years?",
                level,
            )

            if year_match:
                required_years = float(
                    year_match.group(1)
                )
            else:
                # Unknown requirement.
                return 1.0

        if required_years <= 0:
            return 1.0

        if experience_years >= required_years:
            return 1.0

        return self._clamp_score(
            experience_years / required_years
        )

    # ------------------------------------------------------------------
    # EDUCATION
    # ------------------------------------------------------------------

    def calculate_education_score(
        self,
        resume_education: Optional[
            Sequence[Dict[str, Any]]
        ],
        job_requirements: Optional[
            Dict[str, Any]
        ] = None,
    ) -> float:
        """Calculate education alignment."""

        if not resume_education:
            # For jobs where education is not explicitly
            # required, do not automatically punish the candidate.
            if not job_requirements:
                return 1.0

            return 0.0

        degrees = []

        for entry in resume_education:
            if not isinstance(entry, dict):
                continue

            degree = str(
                entry.get("degree", "")
            ).lower().strip()

            if degree:
                degrees.append(degree)

        if not degrees:
            return 0.5

        if not job_requirements:
            return 1.0

        required_degree = str(
            job_requirements.get(
                "degree",
                "",
            )
        ).lower().strip()

        if not required_degree:
            return 1.0

        for degree in degrees:

            if (
                required_degree in degree
                or degree in required_degree
            ):
                return 1.0

        return 0.5

    # ------------------------------------------------------------------
    # OVERALL SCORE
    # ------------------------------------------------------------------

    def calculate_overall_score(
        self,
        semantic_similarity: float,
        skill_match: float,
        experience_score: float,
        education_score: float,
        weights: Optional[
            Dict[str, float]
        ] = None,
    ) -> float:
        """
        Calculate weighted overall score.

        Returns a value from 0.0 to 1.0.

        Default:
            Semantic     30%
            Skills       40%
            Experience   20%
            Education    10%
        """

        selected_weights = (
            weights.copy()
            if weights is not None
            else self.DEFAULT_WEIGHTS.copy()
        )

        required_keys = {
            "semantic",
            "skills",
            "experience",
            "education",
        }

        if set(selected_weights) != required_keys:
            raise ValueError(
                "Weights must contain exactly: "
                "semantic, skills, experience, education."
            )

        total_weight = sum(
            selected_weights.values()
        )

        if total_weight <= 0:
            raise ValueError(
                "The total weight must be greater than zero."
            )

        normalized_weights = {
            key: value / total_weight
            for key, value in selected_weights.items()
        }

        overall = (
            self._clamp_score(semantic_similarity)
            * normalized_weights["semantic"]
            + self._clamp_score(skill_match)
            * normalized_weights["skills"]
            + self._clamp_score(experience_score)
            * normalized_weights["experience"]
            + self._clamp_score(education_score)
            * normalized_weights["education"]
        )

        return self._clamp_score(overall)

    # ------------------------------------------------------------------
    # COMPLETE MATCH
    # ------------------------------------------------------------------

    def match_resume_to_job(
        self,
        resume_text: str,
        resume_skills: Optional[Sequence[str]],
        resume_experience: Optional[
            Sequence[Dict[str, Any]]
        ],
        resume_education: Optional[
            Sequence[Dict[str, Any]]
        ],
        job_description: str,
        job_skills: Optional[Sequence[str]],
        job_experience_level: Optional[str] = None,
        resume_embedding: Optional[
            Sequence[float]
        ] = None,
        job_embedding: Optional[
            Sequence[float]
        ] = None,
    ) -> Dict[str, Any]:
        """Match a resume against a job description."""

        final_resume_embedding = (
            list(resume_embedding)
            if resume_embedding
            else self.generate_embedding(
                resume_text
            )
        )

        final_job_embedding = (
            list(job_embedding)
            if job_embedding
            else self.generate_embedding(
                job_description
            )
        )

        semantic_similarity = (
            self.calculate_semantic_similarity(
                final_resume_embedding,
                final_job_embedding,
            )
        )

        skill_match = (
            self.calculate_skill_match_score(
                resume_skills,
                job_skills,
            )
        )

        skill_details = (
            self.get_skill_match_details(
                resume_skills,
                job_skills,
            )
        )

        experience_score = (
            self.calculate_experience_score(
                resume_experience,
                job_experience_level,
            )
        )

        education_score = (
            self.calculate_education_score(
                resume_education,
            )
        )

        overall_score = (
            self.calculate_overall_score(
                semantic_similarity=semantic_similarity,
                skill_match=skill_match,
                experience_score=experience_score,
                education_score=education_score,
            )
        )

        return {
            # Internal scores remain 0.0 - 1.0.
            "overall_score": round(
                overall_score,
                4,
            ),

            "semantic_similarity": round(
                semantic_similarity,
                4,
            ),

            "skill_match_score": round(
                skill_match,
                4,
            ),

            "experience_score": round(
                experience_score,
                4,
            ),

            "education_score": round(
                education_score,
                4,
            ),

            "matched_skills": skill_details[
                "matched_skills"
            ],

            "missing_skills": skill_details[
                "missing_skills"
            ],

            "resume_embedding": final_resume_embedding,
            "job_embedding": final_job_embedding,
        }
