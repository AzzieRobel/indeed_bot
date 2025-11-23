from typing import Any, Optional, List, Dict
import json
import re

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError("You must install the google-generativeai package: pip install google-generativeai")

class GeminiAI_Manager:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def get_gemini_client(self) -> Optional[Any]:
        if not self.api_key:
            return None
        try:
            genai.configure(api_key=self.api_key)
            return genai.GenerativeModel("gemini-pro")
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
            return None

    def extract_job_summary_with_gemini(
        self, job_detail: dict, client: Any
    ) -> Optional[str]:
        if not client:
            return None
        prompt = (
            "Extract and summarize the following job posting details. "
            "Provide a concise summary (300-400 words) including: "
            "- Job title\n"
            "- Company name\n"
            "- Salary(Pay)\n"
            "- Job types (Fixed period/Part time/Full time/contract)\n"
            "- Location (city/state/remote)\n"
            "- About the Role\n"
            "- Key Responsibilities\n"
            "- Tools You May Work With\n"
            "- What We Offer\n\n"
            f"Job posting details:\n{str(job_detail)[:6000]}"
        )
        try:
            response = client.generate_content(
                [prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3, max_output_tokens=800
                ),
            )
            summary = response.text.strip() if hasattr(response, "text") else response.candidates[0].content.parts[0].text.strip()
            return summary
        except Exception as e:
            print(f"Error extracting job summary with Gemini: {e}")
            return None

    def analyze_job_description_for_resume(
        self, job_description: str, client: Any
    ) -> Optional[Dict[str, Any]]:
        if not client:
            return None
        prompt = f"""Analyze the following job description and extract:
                1. Key technical skills and technologies mentioned (as a comma-separated list)
                2. Key soft skills mentioned (as a comma-separated list)
                3. Important keywords and phrases that should appear in a resume (as a comma-separated list)
                4. Metrics or achievements mentioned (e.g., "increase sales by 20%", "manage team of 10")
                5. Key responsibilities and requirements (as a brief summary)

                Job Description:
                {job_description[:4000]}

                Respond in JSON format:
                {{
                    "technical_skills": ["skill1", "skill2", ...],
                    "soft_skills": ["skill1", "skill2", ...],
                    "keywords": ["keyword1", "keyword2", ...],
                    "achievements": ["achievement1", "achievement2", ...],
                    "requirements_summary": "brief summary of key requirements"
                }}"""
        try:
            response = client.generate_content(
                [prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3, max_output_tokens=900
                ),
            )
            result = response.text.strip() if hasattr(response, "text") else response.candidates[0].content.parts[0].text.strip()
            json_match = re.search(r"\{[\s\S]*\}", result)
            if json_match:
                return json.loads(json_match.group())
            else:
                return None
        except Exception as e:
            print(f"Error analyzing job description with Gemini: {e}")
            return None

    def enhance_achievements_with_gemini(
        self,
        user_achievements: List[str],
        job_requirements_summary: str,
        client: Any,
    ) -> Optional[List[str]]:
        if not client or not user_achievements:
            return None
        try:
            prompt = f"""Given these user achievements:
                {json.dumps(user_achievements, indent=2)}

                And these job requirements:
                {job_requirements_summary}

                Suggest 2-3 enhanced achievement statements that:
                1. Include relevant keywords from the job
                2. Use metrics where possible
                3. Match the job's focus areas

                Return as JSON array of strings."""
            response = client.generate_content(
                [prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4, max_output_tokens=400
                ),
            )
            result = response.text.strip() if hasattr(response, "text") else response.candidates[0].content.parts[0].text.strip()
            json_match = re.search(r"\[[\s\S]*\]", result)
            if json_match:
                suggested = json.loads(json_match.group())
                return suggested[:2]
            return None
        except Exception as e:
            print(f"Error enhancing achievements with Gemini: {e}")
            return None

    def enhance_achievements_with_ai(
        self,
        user_achievements: List[str],
        job_requirements_summary: str,
        client: Any,
    ) -> Optional[List[str]]:
        """
        Generic alias for enhance_achievements_with_gemini to match OpenAI_Manager interface.
        """
        return self.enhance_achievements_with_gemini(
            user_achievements, job_requirements_summary, client
        )

    def generate_cover_letter_content(
        self,
        user_profile: Dict[str, Any],
        job_description: str,
        job_requirements_summary: str,
        client: Any,
    ) -> Optional[Dict[str, str]]:
        if not client:
            return None
        try:
            prompt = f"""Write a professional cover letter for this candidate applying to this job.

                Candidate Profile:
                Name: {user_profile.get('name', '')}
                Summary: {user_profile.get('professional_summary', '')[:300]}
                Key Skills: {', '.join(user_profile.get('technical_skills', [])[:10])}

                Job Description:
                {job_description[:1500]}

                Requirements:
                {job_requirements_summary}

                Write:
                1. Opening paragraph (2-3 sentences) - why interested
                2. Body paragraph 1 (3-4 sentences) - relevant experience and skills
                3. Body paragraph 2 (3-4 sentences) - specific achievements and fit
                4. Closing paragraph (2-3 sentences) - enthusiasm and call to action

                Return as JSON:
                {{
                    "opening": "...",
                    "body1": "...",
                    "body2": "...",
                    "closing": "..."
                }}"""
            response = client.generate_content(
                [prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7, max_output_tokens=700
                ),
            )
            result = response.text.strip() if hasattr(response, "text") else response.candidates[0].content.parts[0].text.strip()
            json_match = re.search(r"\{[\s\S]*\}", result)
            if json_match:
                return json.loads(json_match.group())
            return None
        except Exception as e:
            print(f"Error generating cover letter content with Gemini: {e}")
            return None

    def get_embedding(
        self,
        text: str,
        client: Any,
        model: str = "models/embedding-001",
        max_length: int = 8000,
        retries: int = 2,
    ) -> Optional[List[float]]:
        # Note: Gemini currently exposes text embedding via the Vertex AI or PaLM APIs
        # Below is a simulated stub; actual Gemini embeddings endpoint integration will differ.
        # If you have Google Vertex AI setup, you would use their SDK accordingly.
        print("Gemini's public API for text embeddings is NOT directly available via google-generativeai package as of 2024-06; returning NotImplemented.")
        return None
