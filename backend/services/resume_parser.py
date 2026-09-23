import os
import pdfplumber
from docx import Document
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ResumeParser:
    """Service for parsing resume files (PDF/DOCX) and extracting text"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx']
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a resume file and extract raw text
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary with 'text' key containing extracted text
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        try:
            if file_ext == '.pdf':
                text = self._parse_pdf(file_path)
            elif file_ext == '.docx':
                text = self._parse_docx(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            return {
                'text': text,
                'file_type': file_ext
            }
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            raise
    
    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text_parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise
        
        return '\n\n'.join(text_parts)
    
    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n\n'.join(paragraphs)
        except Exception as e:
            logger.error(f"Error parsing DOCX: {str(e)}")
            raise
    
    def identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify common resume sections
        
        Args:
            text: Raw resume text
            
        Returns:
            Dictionary mapping section names to their content
        """
        sections = {
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'other': ''
        }
        
        lines = text.split('\n')
        current_section = 'other'
        current_content = []
        
        # Common section headers
        section_keywords = {
            'summary': ['summary', 'objective', 'profile', 'about'],
            'experience': ['experience', 'work history', 'employment', 'professional experience'],
            'education': ['education', 'academic', 'qualifications'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise']
        }
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if line is a section header
            section_found = False
            for section, keywords in section_keywords.items():
                if any(keyword in line_lower for keyword in keywords) and len(line) < 100:
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    # Start new section
                    current_section = section
                    current_content = []
                    section_found = True
                    break
            
            if not section_found and line.strip():
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
if __name__ == "__main__":
    my_parser = ResumeParser()
    resume_text = my_parser.parse("resum_format.pdf")
    print("The Resume Text :",resume_text)
    sections = my_parser.identify_sections(resume_text['text'])
    print("The Sections :",sections)
