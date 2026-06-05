"""Resume parser service - extracts structured data from PDF/DOCX resumes"""
import os, json, logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ResumeParser:
    """Parse PDF/DOCX resumes and extract structured information"""

    async def parse(self, file_path: str, file_type: str) -> dict:
        """
        Parse a resume file and return structured data.
        file_type: pdf, doc, docx
        """
        raw_text = ""
        try:
            if file_type == "pdf":
                raw_text = await self._parse_pdf(file_path)
            elif file_type in ("doc", "docx"):
                raw_text = await self._parse_docx(file_path)
            else:
                raw_text = await self._parse_fallback(file_path)
        except Exception as e:
            logger.error(f"Resume parsing error: {e}")

        # Use LLM for structured extraction if available
        from app.services.llm_service import llm_service
        try:
            structured = await llm_service.parse_resume(raw_text)
            return structured
        except Exception as e:
            logger.error(f"LLM resume parsing failed: {e}")

        # Fallback: basic regex extraction
        return self._extract_basic(raw_text)

    async def _parse_pdf(self, path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        import fitz
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    async def _parse_docx(self, path: str) -> str:
        """Extract text from DOCX using python-docx"""
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    async def _parse_fallback(self, path: str) -> str:
        """Fallback: read as plain text"""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _extract_basic(self, text: str) -> dict:
        """Basic regex-based extraction when LLM is unavailable"""
        import re
        result = {"name": "", "education": [], "experience": [], "skills": [], "projects": []}

        # Try to extract name (first non-empty line)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            result["name"] = lines[0]

        # Try to extract skills (comma-separated technical terms)
        tech_keywords = r"(React|Vue|Angular|TypeScript|JavaScript|Python|Java|Go|Rust|Node\.?js|Docker|Kubernetes|AWS|Azure|GCP|SQL|NoSQL|Redis|PostgreSQL|MongoDB|Git|CI/CD|HTML|CSS|SASS|webpack|Vite)"
        skills = list(set(re.findall(tech_keywords, text, re.IGNORECASE)))
        if skills:
            result["skills"] = skills

        return result


resume_parser = ResumeParser()
