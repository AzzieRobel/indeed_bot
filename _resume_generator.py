from __future__ import annotations

import re
import uuid
from docx import Document
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from _doc_generator import TemplateManager, TEMPLATE_DIR

class ResumeCoverLetterGenerator:
    def __init__(
        self,
        ai_provider: Optional[Any] = None,
        template_dir: Path = TEMPLATE_DIR,
        output_dir: Path = Path("output/documents"),
    ):
        self.template_manager = TemplateManager(template_dir)
        self.ai_provider = ai_provider
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_job_description(
        self, job_description: str, ai_client: Any
    ) -> Dict[str, Any]:
        if ai_client and self.ai_provider:
            result = self.ai_provider.analyze_job_description_for_resume(
                job_description, ai_client
            )
            if result:
                return result
        return self._extract_keywords_basic(job_description)

    def _extract_keywords_basic(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        tech_skills = []
        common_tech = [
            "python",
            "javascript",
            "react",
            "node.js",
            "java",
            "sql",
            "aws",
            "docker",
            "kubernetes",
            "git",
            "agile",
            "scrum",
            "api",
            "rest",
            "graphql",
            "mongodb",
            "postgresql",
            "mysql",
            "redis",
            "linux",
            "typescript",
            "angular",
            "vue",
            "django",
            "flask",
            "laravel",
            "spring",
            "microservices",
            "ci/cd",
            "jenkins",
            "terraform",
        ]
        for skill in common_tech:
            if skill in text_lower:
                tech_skills.append(skill.title())

        words = re.findall(r"\b[A-Z][a-z]{2,}\b", text)
        keywords = list(set([w for w in words if len(w) > 3][:20]))

        return {
            "technical_skills": tech_skills[:15],
            "soft_skills": [],
            "keywords": keywords[:20],
            "achievements": [],
            "requirements_summary": text[:200] + "...",
        }

    def merge_skills_with_job(
        self, candidate_skills: List[str], job_skills: List[str]
    ) -> List[str]:
        candidate_skills_lower = [s.lower().strip() for s in candidate_skills]
        job_skills_lower = [s.lower().strip() for s in job_skills]

        matched_skills = [
            s for s in candidate_skills if s.lower().strip() in job_skills_lower
        ]

        remaining_candidate = [
            s for s in candidate_skills if s.lower().strip() not in job_skills_lower
        ]

        new_job_skills = [
            s for s in job_skills if s.lower().strip() not in candidate_skills_lower
        ]

        return matched_skills[:4] + remaining_candidate[:8] + new_job_skills[:4]

    def enhance_achievements(
        self,
        candidate_achievements: List[str],
        job_analysis: Dict[str, Any],
        ai_client: Optional[Any] = None,
    ) -> List[str]:
        enhanced = candidate_achievements.copy()
        job_achievements = job_analysis.get("achievements", [])
        if job_achievements:
            enhanced.extend(job_achievements[:2])
        if ai_client and self.ai_provider and candidate_achievements:
            suggested = self.ai_provider.enhance_achievements_with_ai(
                candidate_achievements,
                job_analysis.get("requirements_summary", ""),
                ai_client,
            )
            if suggested:
                enhanced.extend(suggested)
        return enhanced[:6]

    def format_experience_section(
        self, employment_history: List[Dict[str, Any]], job_keywords: List[str]
    ) -> str:
        sections = []
        for exp in employment_history:
            title = exp.get("title", "")
            company = exp.get("company", "")
            location = exp.get("location", "")
            duration = exp.get("duration", "")
            description = exp.get("description", "")

            header_parts = [title]
            if company:
                header_parts.append(f"at {company}")
            if location:
                header_parts.append(f"({location})")
            if duration:
                header_parts.append(f"[{duration}]")

            section = " | ".join(header_parts) + "\n"

            if isinstance(description, str):
                desc_lines = description.split("\n")
                formatted_lines = []
                for line in desc_lines:
                    if line.strip():
                        line_lower = line.lower()
                        keyword_found = any(
                            kw.lower() in line_lower for kw in job_keywords[:10]
                        )
                        if keyword_found or not formatted_lines:
                            formatted_lines.append(f"• {line.strip()}")
                section += "\n".join(formatted_lines)
            else:
                section += str(description)

            sections.append(section)

        return "\n\n".join(sections)

    def format_education_section(self, education: List[Dict[str, Any]]) -> str:
        sections = []
        for edu in education:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            location = edu.get("location", "")
            duration = edu.get("duration", "")
            year = edu.get("year", "")

            parts = [degree]
            if institution:
                parts.append(f"from {institution}")
            if location:
                parts.append(f"({location})")
            if duration:
                parts.append(f"[{duration}]")
            elif year:
                parts.append(f"[{year}]")

            sections.append(" | ".join(parts))

        return "\n".join(sections)

    def format_certifications_section(self, certifications: List[Any]) -> str:
        certs = []
        for cert in certifications:
            if isinstance(cert, dict):
                name = cert.get("name", "")
                issuer = cert.get("issuer", "")
                if name:
                    certs.append(f"{name}" + (f" from {issuer}" if issuer else ""))
            elif isinstance(cert, str) and cert.strip():
                certs.append(cert.strip())

        return "\n".join(certs) if certs else ""

    def generate_resume(
        self,
        user_profile: Dict[str, Any],
        job_summary: Optional[str] = None,
        ai_client: Optional[Any] = None,
    ) -> str:
        if not self.ai_provider or not ai_client:
            raise ValueError("AI provider and client must be supplied.")
        return self.ai_provider.generate_resume_content(
            user_profile,
            job_summary,
            ai_client,
        )

    def generate_cover_letter(
        self,
        user_profile: Dict[str, Any],
        job_summary: str,
        ai_client: Optional[Any] = None,
    ) -> Optional[Dict[str, str]]:
        if not self.ai_provider or not ai_client:
            raise ValueError("AI provider and client must be supplied.")
        return self.ai_provider.generate_cover_letter_content(
            user_profile,
            job_summary,
            ai_client,
        )

    def export_to_pdf(self, docx_path: Path) -> Path:
        try:
            try:
                from docx2pdf import convert

                pdf_path = docx_path.with_suffix(".pdf")
                convert(str(docx_path), str(pdf_path))
                return pdf_path
            except ImportError:
                pass

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet

                pdf_path = docx_path.with_suffix(".pdf")
                doc = Document(str(docx_path))

                pdf_doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
                styles = getSampleStyleSheet()
                story = []

                for paragraph in doc.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        style = styles["Normal"]
                        if paragraph.style.name.startswith("Heading"):
                            level = (
                                int(paragraph.style.name[-1])
                                if paragraph.style.name[-1].isdigit()
                                else 1
                            )
                            style = styles[f"Heading{min(level, 3)}"]
                        story.append(Paragraph(text, style))
                        story.append(Spacer(1, 12))

                pdf_doc.build(story)
                return pdf_path
            except ImportError:
                print(
                    "Warning: PDF export requires 'docx2pdf' or 'reportlab'. "
                    "Install with: pip install docx2pdf"
                )
                raise ImportError("PDF export library not available")

        except Exception as e:
            print(f"Error converting to PDF: {e}")
            raise

    def generate_documents(
        self,
        candidate_profile: Dict[str, Any],
        job_description: str,
        company_name: Optional[str] = None,
        company_address: Optional[str] = None,
        hiring_manager: Optional[str] = None,
        template_name: str = "resume_modern.docx",
        export_pdf: bool = True,
        ai_client: Optional[Any] = None,
    ) -> Dict[str, Path]:
        results = {}

        resume_result = self.generate_resume(
            candidate_profile,
            job_description,
            template_name=template_name,
            ai_client=ai_client,
        )
        results["resume"] = resume_result

        cover_letter_result = self.generate_cover_letter(
            candidate_profile,
            job_description,
            company_name=company_name,
            company_address=company_address,
            hiring_manager=hiring_manager,
            ai_client=ai_client,
        )
        results["cover_letter"] = cover_letter_result

        return results
