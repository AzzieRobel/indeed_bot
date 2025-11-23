from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from _doc_generator import TemplateManager, TEMPLATE_DIR
from _open_ai import OpenAI_Manager


class ResumeCoverLetterGenerator:

    def __init__(
        self,
        openai_manager: Optional[OpenAI_Manager] = None,
        template_dir: Path = TEMPLATE_DIR,
        output_dir: Path = Path("output/documents"),
    ):
        self.template_manager = TemplateManager(template_dir)
        self.openai_manager = openai_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_job_description(
        self, job_description: str, openai_client: Any
    ) -> Dict[str, Any]:
        if openai_client and self.openai_manager:
            result = self.openai_manager.analyze_job_description_for_resume(
                job_description, openai_client
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
        self, user_skills: List[str], job_skills: List[str]
    ) -> List[str]:
        user_skills_lower = [s.lower().strip() for s in user_skills]
        job_skills_lower = [s.lower().strip() for s in job_skills]

        matched_skills = []
        for skill in user_skills:
            if skill.lower().strip() in job_skills_lower:
                matched_skills.append(skill)

        remaining_user = [
            s for s in user_skills if s.lower().strip() not in job_skills_lower
        ]

        new_job_skills = [
            s for s in job_skills if s.lower().strip() not in user_skills_lower
        ]

        return matched_skills[:4] + remaining_user[:8] + new_job_skills[:4]

    def enhance_achievements(
        self,
        user_achievements: List[str],
        job_analysis: Dict[str, Any],
        openai_client: Optional[Any] = None,
    ) -> List[str]:
        enhanced = user_achievements.copy()
        job_achievements = job_analysis.get("achievements", [])
        if job_achievements:
            enhanced.extend(job_achievements[:2])
        if openai_client and self.openai_manager and user_achievements:
            suggested = self.openai_manager.enhance_achievements_with_openai(
                user_achievements,
                job_analysis.get("requirements_summary", ""),
                openai_client,
            )
            if suggested:
                enhanced.extend(suggested)

        return enhanced[:6]

    def format_experience_section(
        self, work_experience: List[Dict[str, Any]], job_keywords: List[str]
    ) -> str:
        sections = []
        for exp in work_experience:
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
        job_description: Optional[str] = None,
        job_analysis: Optional[Dict[str, Any]] = None,
        template_name: str = "resume_modern.docx",
        openai_client: Optional[Any] = None,
    ) -> Path:
        self.template_manager.ensure_template_pack()

        if job_description and not job_analysis and openai_client:
            job_analysis = self.analyze_job_description(job_description, openai_client)
        elif not job_analysis:
            job_analysis = {
                "technical_skills": [],
                "soft_skills": [],
                "keywords": [],
                "achievements": [],
                "requirements_summary": "",
            }

        template_path = self.template_manager.template_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        doc = Document(str(template_path))

        job_keywords = job_analysis.get("keywords", [])
        job_tech_skills = job_analysis.get("technical_skills", [])

        full_name = user_profile.get("name", "${FULL_NAME}")
        professional_title = user_profile.get("job_preferences", {}).get(
            "desired_role", ""
        )
        email = user_profile.get("email", "")
        location = user_profile.get("location", "")
        phone = user_profile.get("phone", "")

        contact_parts = []
        if email:
            contact_parts.append(email)
        if phone:
            contact_parts.append(phone)
        if location:
            contact_parts.append(location)
        contact_block = (
            " | ".join(contact_parts) if contact_parts else "${CONTACT_BLOCK}"
        )

        user_tech_skills = user_profile.get("technical_skills", [])
        enhanced_tech_skills = self.merge_skills_with_job(
            user_tech_skills, job_tech_skills
        )

        user_achievements = user_profile.get("key_achievements", [])
        enhanced_achievements = self.enhance_achievements(
            user_achievements, job_analysis, openai_client
        )

        experience_section = self.format_experience_section(
            user_profile.get("work_experience", []), job_keywords
        )
        education_section = self.format_education_section(
            user_profile.get("education", [])
        )
        certifications_section = self.format_certifications_section(
            user_profile.get("certifications", [])
        )

        replacements = {
            "${FULL_NAME}": full_name,
            "${PROFESSIONAL_TITLE}": professional_title,
            "${CONTACT_BLOCK}": contact_block,
            "${TAGLINE}": professional_title or "Professional",
            "${SUMMARY}": user_profile.get("professional_summary", ""),
            "${PROFESSIONAL_PROFILE}": user_profile.get("professional_summary", ""),
            "${CORE_SKILL_1}": (
                enhanced_tech_skills[0] if len(enhanced_tech_skills) > 0 else ""
            ),
            "${CORE_SKILL_2}": (
                enhanced_tech_skills[1] if len(enhanced_tech_skills) > 1 else ""
            ),
            "${CORE_SKILL_3}": (
                enhanced_tech_skills[2] if len(enhanced_tech_skills) > 2 else ""
            ),
            "${CORE_SKILL_4}": (
                enhanced_tech_skills[3] if len(enhanced_tech_skills) > 3 else ""
            ),
            "${TECH_STACK}": ", ".join(enhanced_tech_skills[:12]),
            "${SOFT_SKILLS}": ", ".join(user_profile.get("soft_skills", [])[:10]),
            "${EXPERIENCE_SECTION}": experience_section,
            "${EDUCATION_SECTION}": education_section,
            "${CERTIFICATIONS_SECTION}": certifications_section,
            "${PROJECTS_SECTION}": "\n".join(enhanced_achievements[:4]),
        }

        for paragraph in doc.paragraphs:
            full_text = paragraph.text
            for placeholder, value in replacements.items():
                if placeholder in full_text:
                    full_text = full_text.replace(placeholder, value)
            if full_text != paragraph.text:
                paragraph.clear()
                paragraph.add_run(full_text)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"resume_{timestamp}.docx"
        output_path = self.output_dir / output_filename
        doc.save(str(output_path))

        return output_path

    def generate_cover_letter(
        self,
        user_profile: Dict[str, Any],
        job_description: str,
        company_name: Optional[str] = None,
        company_address: Optional[str] = None,
        hiring_manager: Optional[str] = None,
        job_analysis: Optional[Dict[str, Any]] = None,
        openai_client: Optional[Any] = None,
    ) -> Path:
        self.template_manager.ensure_template_pack()

        if not job_analysis and openai_client:
            job_analysis = self.analyze_job_description(job_description, openai_client)
        elif not job_analysis:
            job_analysis = {
                "technical_skills": [],
                "soft_skills": [],
                "keywords": [],
                "requirements_summary": job_description[:200],
            }

        template_path = (
            self.template_manager.template_dir / "cover_letter_standard.docx"
        )
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        doc = Document(str(template_path))

        if openai_client and self.openai_manager:
            ai_content = self.openai_manager.generate_cover_letter_content(
                user_profile,
                job_description,
                job_analysis.get("requirements_summary", ""),
                openai_client,
            )
        else:
            ai_content = None

        current_date = datetime.now().strftime("%B %d, %Y")
        full_name = user_profile.get("name", "${FULL_NAME}")

        opening = (
            ai_content.get("opening", "")
            if ai_content
            else f"I am writing to express my interest in the position. With my background in {', '.join(user_profile.get('technical_skills', [])[:3])}, I am excited about this opportunity."
        )
        body1 = (
            ai_content.get("body1", "")
            if ai_content
            else f"My experience includes {user_profile.get('professional_summary', '')[:200]}."
        )
        body2 = (
            ai_content.get("body2", "")
            if ai_content
            else f"I have successfully {user_profile.get('key_achievements', ['delivered results'])[0] if user_profile.get('key_achievements') else 'achieved results'}."
        )
        closing = (
            ai_content.get("closing", "")
            if ai_content
            else "I am excited about the opportunity to contribute to your team and would welcome the chance to discuss how my skills align with your needs."
        )

        replacements = {
            "${DATE}": current_date,
            "${HIRING_MANAGER}": hiring_manager or "Hiring Manager",
            "${COMPANY_NAME}": company_name or "Company Name",
            "${COMPANY_ADDRESS}": company_address or "",
            "${OPENING_PARAGRAPH}": opening,
            "${BODY_PARAGRAPH_1}": body1,
            "${BODY_PARAGRAPH_2}": body2,
            "${CLOSING_PARAGRAPH}": closing,
            "${SIGN_OFF}": "Sincerely,",
            "${FULL_NAME}": full_name,
        }

        for paragraph in doc.paragraphs:
            full_text = paragraph.text
            for placeholder, value in replacements.items():
                if placeholder in full_text:
                    full_text = full_text.replace(placeholder, value)
            if full_text != paragraph.text:
                paragraph.clear()
                paragraph.add_run(full_text)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"cover_letter_{timestamp}.docx"
        output_path = self.output_dir / output_filename
        doc.save(str(output_path))

        return output_path

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
        user_profile: Dict[str, Any],
        job_description: str,
        company_name: Optional[str] = None,
        company_address: Optional[str] = None,
        hiring_manager: Optional[str] = None,
        template_name: str = "resume_modern.docx",
        export_pdf: bool = True,
        openai_client: Optional[Any] = None,
    ) -> Dict[str, Path]:
        results = {}

        resume_docx = self.generate_resume(
            user_profile,
            job_description,
            template_name=template_name,
            openai_client=openai_client,
        )
        results["resume_docx"] = resume_docx

        if export_pdf:
            try:
                results["resume_pdf"] = self.export_to_pdf(resume_docx)
            except Exception as e:
                print(f"Could not export resume to PDF: {e}")

        cover_letter_docx = self.generate_cover_letter(
            user_profile,
            job_description,
            company_name=company_name,
            company_address=company_address,
            hiring_manager=hiring_manager,
            openai_client=openai_client,
        )
        results["cover_letter_docx"] = cover_letter_docx

        if export_pdf:
            try:
                results["cover_letter_pdf"] = self.export_to_pdf(cover_letter_docx)
            except Exception as e:
                print(f"Could not export cover letter to PDF: {e}")

        return results
