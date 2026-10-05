"""
NLP engine for resume information extraction.

Responsibilities:
- Load and manage the configured spaCy model.
- Extract technical skills from resume text.
- Extract work experience entries.
- Extract education information.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import spacy
from spacy.language import Language

from ..core.config import settings


logger = logging.getLogger(__name__)


class NLPEngine:
    """Service responsible for NLP-based resume information extraction."""

    # ==================================================================
    # Supported technical skills
    # ==================================================================

    DEFAULT_SKILLS: Tuple[str, ...] = (
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "angular",
        "vue",
        "node.js",
        "html",
        "css",
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "git",
        "linux",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "natural language processing",
        "nlp",
        "data science",
        "data analysis",
        "eda",
        "data structures",
        "algorithms",
        "operating systems",
        "database management",
        "dbms",
        "oops",
        "network security",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "pandas",
        "numpy",
        "opencv",
        "fastapi",
        "django",
        "flask",
        "rest api",
        "graphql",
        "microservices",
        "ci/cd",
        "agile",
        "scrum",
        "generative ai",
        "large language models",
        "llm",
        "rag",
        "langchain",
        "prompt engineering",
        "power bi",
        "tableau",
        "excel",
        "matplotlib",
        "plotly",
        "seaborn",
        "beautifulsoup",
        "requests",
        "devops",
    )

    # ==================================================================
    # Resume section headers
    # ==================================================================

    SECTION_HEADERS: Set[str] = {
        "education",
        "coursework / skills",
        "coursework/skills",
        "skills",
        "technical skills",
        "technical skill",
        "projects",
        "project",
        "internship",
        "internships",
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "extracurricular",
        "extracurricular activities",
        "certifications",
        "certification",
        "summary",
        "profile",
        "objective",
    }

    # ==================================================================
    # Education keywords
    # ==================================================================

    EDUCATION_KEYWORDS: Tuple[str, ...] = (
        "b.tech",
        "btech",
        "m.tech",
        "mtech",
        "b.sc",
        "bsc",
        "m.sc",
        "msc",
        "b.e",
        "b.e.",
        "m.e",
        "m.e.",
        "bachelor",
        "master",
        "phd",
        "doctorate",
        "diploma",
        "intermediate",
        "secondary education",
        "high school",
        "junior college",
        "university",
        "college",
        "institute",
        "institution",
        "school",
    )

    # ==================================================================
    # Experience keywords
    # ==================================================================

    EXPERIENCE_ROLE_KEYWORDS: Tuple[str, ...] = (
        "intern",
        "developer",
        "engineer",
        "analyst",
        "manager",
        "specialist",
        "scientist",
        "consultant",
        "administrator",
        "architect",
        "designer",
        "trainee",
    )

    # ==================================================================
    # Date patterns
    # ==================================================================

    YEAR_PATTERN = re.compile(
        r"\b(?:19|20)\d{2}\b"
    )

    DATE_RANGE_PATTERN = re.compile(
        r"""
        (?P<start>
            (?:
                (?:0?[1-9]|1[0-2])\s+
            )?
            (?:19|20)\d{2}
        )
        \s*
        [-–—]
        \s*
        (?P<end>
            (?:
                (?:0?[1-9]|1[0-2])\s+
            )?
            (?:
                (?:19|20)\d{2}
                |present
                |current
            )
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    MONTH_YEAR_PATTERN = re.compile(
        r"""
        (?:
            Jan(?:uary)?|
            Feb(?:ruary)?|
            Mar(?:ch)?|
            Apr(?:il)?|
            May|
            Jun(?:e)?|
            Jul(?:y)?|
            Aug(?:ust)?|
            Sep(?:tember)?|
            Oct(?:ober)?|
            Nov(?:ember)?|
            Dec(?:ember)?
        )
        \s+
        (?:19|20)\d{2}
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # ==================================================================
    # Initialization
    # ==================================================================

    def __init__(
        self,
        model_name: Optional[str] = None,
    ) -> None:
        """Initialize the NLP engine."""

        self.model_name = (
            model_name or settings.SPACY_MODEL
        )

        self.nlp: Language = self._load_model()

    # ==================================================================
    # Model loading
    # ==================================================================

    def _load_model(self) -> Language:
        """Load the configured spaCy model."""

        try:
            nlp = spacy.load(self.model_name)

            logger.info(
                "Successfully loaded spaCy model: %s",
                self.model_name,
            )

            return nlp

        except OSError as exc:
            logger.exception(
                "spaCy model '%s' could not be loaded.",
                self.model_name,
            )

            raise RuntimeError(
                f"spaCy model '{self.model_name}' is not installed."
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected error loading spaCy model '%s'.",
                self.model_name,
            )

            raise RuntimeError(
                f"Failed to initialize spaCy model '{self.model_name}'."
            ) from exc

    # ==================================================================
    # General helpers
    # ==================================================================

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize whitespace."""

        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def _unique_preserve_order(
        items: List[str],
    ) -> List[str]:
        """Remove duplicate values while preserving order."""

        seen: Set[str] = set()
        result: List[str] = []

        for item in items:

            cleaned = item.strip()

            if not cleaned:
                continue

            normalized = cleaned.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(cleaned)

        return result

    @staticmethod
    def _clean_bullet(text: str) -> str:
        """Remove common resume bullet characters."""

        return re.sub(
            r"^[•●▪◦\-*]+\s*",
            "",
            text,
        ).strip()

    def _get_lines(
        self,
        text: str,
    ) -> List[str]:
        """Return cleaned, non-empty resume lines."""

        lines: List[str] = []

        for line in text.splitlines():

            cleaned = self._clean_bullet(line)

            if cleaned:
                lines.append(cleaned)

        return lines

    @classmethod
    def _normalize_header(
        cls,
        line: str,
    ) -> str:
        """Normalize a possible section heading."""

        return re.sub(
            r"\s+",
            " ",
            line.strip().lower(),
        )

    @classmethod
    def _is_section_header(
        cls,
        line: str,
    ) -> bool:
        """Return True when a line is a known section heading."""

        normalized = cls._normalize_header(line)

        return normalized in cls.SECTION_HEADERS

    def _find_section(
        self,
        lines: List[str],
        section_names: Set[str],
    ) -> List[str]:
        """Extract lines belonging to a particular resume section."""

        normalized_targets = {
            self._normalize_header(name)
            for name in section_names
        }

        start_index: Optional[int] = None

        for index, line in enumerate(lines):

            if (
                self._normalize_header(line)
                in normalized_targets
            ):
                start_index = index + 1
                break

        if start_index is None:
            return []

        section_lines: List[str] = []

        for line in lines[start_index:]:

            if self._is_section_header(line):
                break

            section_lines.append(line)

        return section_lines

    @staticmethod
    def _remove_years(
        text: str,
    ) -> str:
        """Remove years from a string."""

        return re.sub(
            r"\b(?:19|20)\d{2}\b",
            "",
            text,
        )

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:
        """Clean common PDF extraction artifacts."""

        text = text.replace(
            "(cid:211)",
            "",
        )

        text = text.replace(
            "(cid:135)",
            "",
        )

        text = text.replace(
            "•",
            "",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip(
            " -–—:|,."
        )

    # ==================================================================
    # Skills
    # ==================================================================

    def extract_skills(
        self,
        text: str,
        common_skills: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Extract technical skills using a controlled dictionary.

        Skills are detected from the actual resume text.
        """

        if not text or not text.strip():
            return []

        skills = (
            common_skills
            if common_skills is not None
            else list(self.DEFAULT_SKILLS)
        )

        searchable_text = (
            self._normalize_text(text).lower()
        )

        extracted: List[str] = []

        # --------------------------------------------------------------
        # Dictionary matching
        # --------------------------------------------------------------

        for skill in skills:

            skill_clean = skill.strip()

            if not skill_clean:
                continue

            escaped = re.escape(
                skill_clean.lower()
            )

            pattern = (
                rf"(?<![a-z0-9+#.])"
                rf"{escaped}"
                rf"(?![a-z0-9+#.])"
            )

            if re.search(
                pattern,
                searchable_text,
            ):
                extracted.append(skill_clean)

        # --------------------------------------------------------------
        # Explicit skills section
        # --------------------------------------------------------------

        lines = self._get_lines(text)

        skill_lines = self._find_section(
            lines,
            {
                "skills",
                "technical skills",
                "technical skill",
                "coursework / skills",
                "coursework/skills",
            },
        )

        skill_lookup = {
            skill.lower(): skill
            for skill in skills
        }

        for line in skill_lines:

            if ":" in line:
                _, values = line.split(
                    ":",
                    1,
                )
            else:
                values = line

            candidates = re.split(
                r"[,|;/]",
                values,
            )

            for candidate in candidates:

                candidate = self._clean_text(
                    candidate
                )

                if candidate.lower() in skill_lookup:
                    extracted.append(
                        skill_lookup[
                            candidate.lower()
                        ]
                    )

        return self._unique_preserve_order(
            extracted
        )

    # ==================================================================
    # Dates
    # ==================================================================

    def _extract_date_range(
        self,
        line: str,
    ) -> Optional[Tuple[str, str]]:
        """Extract a start/end date pair."""

        match = self.DATE_RANGE_PATTERN.search(
            line
        )

        if match:

            return (
                match.group("start").strip(),
                match.group("end").strip(),
            )

        return None

    def _extract_year(
        self,
        text: str,
    ) -> Optional[int]:
        """Extract the first four-digit year."""

        match = self.YEAR_PATTERN.search(
            text
        )

        if match:
            return int(match.group())

        return None

    # ==================================================================
    # Experience
    # ==================================================================

    @staticmethod
    def _looks_like_role(
        line: str,
    ) -> bool:
        """Detect whether a line resembles a job role."""

        lower = line.lower()

        return any(
            keyword in lower
            for keyword in NLPEngine.EXPERIENCE_ROLE_KEYWORDS
        )

    @staticmethod
    def _clean_role(
        role: str,
    ) -> str:
        """Clean location names accidentally included in job titles."""

        role = NLPEngine._clean_text(role)

        role = re.sub(
            r"\s+(?:india|hyderabad|bangalore|"
            r"bengaluru|delhi|mumbai|chennai|pune)$",
            "",
            role,
            flags=re.IGNORECASE,
        )

        return role.strip()

    @staticmethod
    def _looks_like_description(
        line: str,
    ) -> bool:
        """Detect likely description/bullet text."""

        lower = line.lower()

        return (
            len(line) > 35
            or lower.startswith(
                (
                    "worked",
                    "developed",
                    "built",
                    "created",
                    "implemented",
                    "designed",
                    "analyzed",
                    "managed",
                    "responsible",
                    "gained",
                    "assisted",
                    "contributed",
                )
            )
        )

    def extract_experience(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:
        """Extract work experience from the experience section."""

        if not text or not text.strip():
            return []

        lines = self._get_lines(text)

        experience_lines = self._find_section(
            lines,
            {
                "experience",
                "work experience",
                "professional experience",
                "internship",
                "internships",
                "employment",
            },
        )

        if not experience_lines:
            return []

        entries: List[Dict[str, Any]] = []

        index = 0

        while index < len(experience_lines):

            line = experience_lines[index]

            year_match = self.YEAR_PATTERN.search(
                line
            )

            date_range = self._extract_date_range(
                line
            )

            # ----------------------------------------------------------
            # Format A
            #
            # Company 2024
            # Role
            # Description
            # ----------------------------------------------------------

            if year_match and not date_range:

                year = year_match.group()

                company = self._clean_text(
                    self.YEAR_PATTERN.sub(
                        "",
                        line,
                    )
                )

                role = ""
                description_parts: List[str] = []

                next_index = index + 1

                if next_index < len(experience_lines):

                    candidate = (
                        experience_lines[next_index]
                    )

                    if self._looks_like_role(
                        candidate
                    ):
                        role = self._clean_role(
                            candidate
                        )

                        next_index += 1

                while next_index < len(
                    experience_lines
                ):

                    candidate = (
                        experience_lines[next_index]
                    )

                    if self._is_section_header(
                        candidate
                    ):
                        break

                    if (
                        self.YEAR_PATTERN.search(
                            candidate
                        )
                        and len(candidate) <= 100
                        and not self._looks_like_description(
                            candidate
                        )
                    ):
                        break

                    if self._looks_like_description(
                        candidate
                    ):
                        description_parts.append(
                            self._clean_text(
                                candidate
                            )
                        )

                    next_index += 1

                if company and role:

                    entries.append(
                        {
                            "dates": [
                                year,
                                year,
                            ],
                            "role": role,
                            "company": company,
                            "description": (
                                " ".join(
                                    description_parts
                                )[:1000]
                            ),
                        }
                    )

                index = max(
                    next_index,
                    index + 1,
                )

                continue

            # ----------------------------------------------------------
            # Format B
            #
            # Company
            # Role
            # 2024 - 2025
            # Description
            # ----------------------------------------------------------

            if date_range:

                start_date, end_date = date_range

                company = ""
                role = ""

                description_parts: List[str] = []

                previous = experience_lines[
                    max(0, index - 3):index
                ]

                for candidate in reversed(
                    previous
                ):

                    if (
                        not role
                        and self._looks_like_role(
                            candidate
                        )
                    ):
                        role = self._clean_role(
                            candidate
                        )
                        continue

                    if not company:
                        company = self._clean_text(
                            candidate
                        )

                next_index = index + 1

                while next_index < len(
                    experience_lines
                ):

                    candidate = (
                        experience_lines[next_index]
                    )

                    if (
                        self.YEAR_PATTERN.search(
                            candidate
                        )
                        or self._extract_date_range(
                            candidate
                        )
                    ):
                        break

                    if self._looks_like_description(
                        candidate
                    ):
                        description_parts.append(
                            self._clean_text(
                                candidate
                            )
                        )

                    next_index += 1

                if role or company:

                    entries.append(
                        {
                            "dates": [
                                start_date,
                                end_date,
                            ],
                            "role": (
                                role
                                or "Unknown"
                            ),
                            "company": (
                                company
                                or "Unknown"
                            ),
                            "description": (
                                " ".join(
                                    description_parts
                                )[:1000]
                            ),
                        }
                    )

                index = max(
                    next_index,
                    index + 1,
                )

                continue

            index += 1

        return entries

    # ==================================================================
    # Education helpers
    # ==================================================================

    @staticmethod
    def _detect_degree(
        text: str,
    ) -> str:
        """Detect a standardized degree name."""

        lower = text.lower()

        if (
            "b.tech" in lower
            or "btech" in lower
            or "bachelor of technology" in lower
        ):
            return "B.Tech"

        if (
            "m.tech" in lower
            or "mtech" in lower
            or "master of technology" in lower
        ):
            return "M.Tech"

        if (
            "b.sc" in lower
            or "bsc" in lower
            or "bachelor of science" in lower
        ):
            return "B.Sc"

        if (
            "m.sc" in lower
            or "msc" in lower
            or "master of science" in lower
        ):
            return "M.Sc"

        if (
            "b.e." in lower
            or "b.e " in lower
            or "be " in lower
            or "bachelor of engineering" in lower
        ):
            return "B.E"

        if (
            "m.e." in lower
            or "m.e " in lower
            or "me " in lower
            or "master of engineering" in lower
        ):
            return "M.E"

        if (
            "b.com" in lower
            or "bcom" in lower
            or "bachelor of commerce" in lower
        ):
            return "B.Com"

        if (
            "m.com" in lower
            or "mcom" in lower
            or "master of commerce" in lower
        ):
            return "M.Com"

        if (
            "bba" in lower
            or "bachelor of business administration"
            in lower
        ):
            return "BBA"

        if (
            "mba" in lower
            or "master of business administration"
            in lower
        ):
            return "MBA"

        if (
            "bca" in lower
            or "bachelor of computer applications"
            in lower
        ):
            return "BCA"

        if (
            "mca" in lower
            or "master of computer applications"
            in lower
        ):
            return "MCA"

        if "phd" in lower or "doctorate" in lower:
            return "PhD"

        if "diploma" in lower:
            return "Diploma"

        if (
            "intermediate" in lower
            or "junior college" in lower
            or "12th" in lower
        ):
            return "Intermediate"

        if (
            "high school" in lower
            or "secondary education" in lower
            or "ssc" in lower
            or "10th" in lower
        ):
            return "High School"

        if "bachelor" in lower:
            return "Bachelor"

        if "master" in lower:
            return "Master"

        return ""

    @staticmethod
    def _extract_field_of_study(
        text: str,
    ) -> str:
        """Extract field of study from degree information."""

        patterns = (
            r"(?:b\.?\s*tech|btech|bachelor\s+of\s+technology)"
            r"\s*(?:[-:,]|\bin\b|\bof\b)\s*"
            r"([A-Za-z][A-Za-z &/.-]{2,80})",

            r"(?:b\.?\s*e|bachelor\s+of\s+engineering)"
            r"\s*(?:[-:,]|\bin\b|\bof\b)\s*"
            r"([A-Za-z][A-Za-z &/.-]{2,80})",

            r"(?:m\.?\s*tech|mtech|master\s+of\s+technology)"
            r"\s*(?:[-:,]|\bin\b|\bof\b)\s*"
            r"([A-Za-z][A-Za-z &/.-]{2,80})",

            r"(?:m\.?\s*e|master\s+of\s+engineering)"
            r"\s*(?:[-:,]|\bin\b|\bof\b)\s*"
            r"([A-Za-z][A-Za-z &/.-]{2,80})",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if not match:
                continue

            value = match.group(1).strip()

            value = re.split(
                r"\s+(?:cgpa|gpa|percentage|percent|"
                r"marks|graduation|passed|passing)\b",
                value,
                flags=re.IGNORECASE,
            )[0]

            value = re.sub(
                r"\b(?:19|20)\d{2}\b",
                "",
                value,
            )

            value = value.strip(
                " -–—:,.|"
            )

            if value.lower() in {
                "technology",
                "engineering",
                "science",
                "commerce",
                "cgpa",
                "percentage",
                "percent",
                "marks",
            }:
                return ""

            return value

        return ""

    @staticmethod
    def _extract_institution(
        line: str,
    ) -> str:
        """Extract likely institution name from an education line."""

        cleaned = NLPEngine._clean_text(line)

        # Remove dates.
        cleaned = re.sub(
            r"\b(?:0?[1-9]|1[0-2])\s+"
            r"(?:19|20)\d{2}\b",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"\b(?:19|20)\d{2}\b",
            "",
            cleaned,
        )

        # Remove degree information only when it appears
        # at the beginning of the line.
        cleaned = re.sub(
            r"^(?:Bachelor|Master)\s+of\s+"
            r"(?:Technology|Engineering|Science|Commerce)"
            r"(?:\s*[,:\-]\s*[^|]+)?",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"^(?:B\.?\s*Tech|BTech|M\.?\s*Tech|MTech)"
            r"(?:\s*[,:\-]\s*[^|]+)?",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        # Remove CGPA / percentage information.
        cleaned = re.sub(
            r"\b(?:CGPA|GPA|percentage|percent|marks)"
            r"\s*[:\-]?\s*[\d.]+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        )

        return cleaned.strip(
            " -–—:|,."
        )

    # ==================================================================
    # Education
    # ==================================================================

    def extract_education(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract structured education information.

        Returns:
            [
                {
                    "institution": "...",
                    "degree": "...",
                    "field": "...",
                    "year": 2025
                }
            ]
        """

        if not text or not text.strip():
            return []

        lines = self._get_lines(text)

        education_lines = self._find_section(
            lines,
            {"education"},
        )

        if not education_lines:
            return []

        entries: List[Dict[str, Any]] = []

        # --------------------------------------------------------------
        # Group education lines into blocks.
        # --------------------------------------------------------------

        blocks: List[List[str]] = []
        current_block: List[str] = []

        for line in education_lines:

            line = line.strip()

            if not line:
                continue

            degree_in_line = self._detect_degree(
                line
            )

            current_has_degree = (
                bool(
                    self._detect_degree(
                        " ".join(current_block)
                    )
                )
                if current_block
                else False
            )

            # New degree = new education record.
            if (
                current_block
                and degree_in_line
                and current_has_degree
            ):
                blocks.append(current_block)
                current_block = []

            current_block.append(line)

        if current_block:
            blocks.append(current_block)

        # --------------------------------------------------------------
        # Parse each education block.
        # --------------------------------------------------------------

        for block in blocks:

            block_text = " ".join(block)
            lower_block = block_text.lower()

            if not any(
                keyword in lower_block
                for keyword in self.EDUCATION_KEYWORDS
            ):
                continue

            # ----------------------------------------------------------
            # Degree
            # ----------------------------------------------------------

            degree = self._detect_degree(
                block_text
            )

            # ----------------------------------------------------------
            # Year
            # ----------------------------------------------------------

            years = [
                int(match.group())
                for match in self.YEAR_PATTERN.finditer(
                    block_text
                )
            ]

            year = max(years) if years else None

            # ----------------------------------------------------------
            # Institution
            # ----------------------------------------------------------

            institution = ""

            institution_keywords = (
                "college",
                "university",
                "institute",
                "institution",
                "school",
            )

            # First: find an explicitly named institution.
            for line in block:

                lower_line = line.lower()

                if any(
                    keyword in lower_line
                    for keyword in institution_keywords
                ):
                    candidate = (
                        self._extract_institution(
                            line
                        )
                    )

                    if candidate:
                        institution = candidate
                        break

            # Second: use a line that does not represent
            # degree information.
            if not institution:

                for line in block:

                    if self._detect_degree(line):
                        continue

                    candidate = (
                        self._extract_institution(
                            line
                        )
                    )

                    if (
                        candidate
                        and len(candidate) >= 3
                    ):
                        institution = candidate
                        break

            # ----------------------------------------------------------
            # Field of study
            # ----------------------------------------------------------

            field = self._extract_field_of_study(
                block_text
            )

            field = field.strip(
                " -–—:,.|"
            )

            # Never return generic degree words as a field.
            if field.lower() in {
                "technology",
                "engineering",
                "science",
                "commerce",
            }:
                field = ""

            # ----------------------------------------------------------
            # Indian education fallbacks
            # ----------------------------------------------------------

            if not degree:

                if (
                    "intermediate" in lower_block
                    or "junior college" in lower_block
                    or "12th" in lower_block
                ):
                    degree = "Intermediate"

                elif (
                    "high school" in lower_block
                    or "secondary education" in lower_block
                    or "ssc" in lower_block
                    or "10th" in lower_block
                ):
                    degree = "High School"

            if not institution:
                continue

            entries.append(
                {
                    "institution": institution,
                    "degree": degree,
                    "field": field,
                    "year": year,
                }
            )

        # --------------------------------------------------------------
        # Remove duplicate records.
        # --------------------------------------------------------------

        unique_entries: List[
            Dict[str, Any]
        ] = []

        seen: Set[str] = set()

        for entry in entries:

            key = (
                f"{entry['institution']}|"
                f"{entry['degree']}|"
                f"{entry['field']}|"
                f"{entry['year']}"
            ).lower()

            if key in seen:
                continue

            seen.add(key)

            unique_entries.append(
                entry
            )

        return unique_entries

    # ==================================================================
    # Main processing
    # ==================================================================

    def process_resume(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """Process resume text and return structured information."""

        if not text or not text.strip():

            return {
                "skills": [],
                "experience": [],
                "education": [],
            }

        logger.info(
            "Processing resume text (%d characters)",
            len(text),
        )

        skills = self.extract_skills(
            text
        )

        experience = self.extract_experience(
            text
        )

        education = self.extract_education(
            text
        )

        logger.info(
            "Resume extraction complete: "
            "skills=%d, experience=%d, education=%d",
            len(skills),
            len(experience),
            len(education),
        )

        return {
            "skills": skills,
            "experience": experience,
            "education": education,
        }