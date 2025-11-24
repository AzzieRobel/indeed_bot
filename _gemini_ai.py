from typing import Any, Optional, List, Dict
import json
import time
import re

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "You must install the google-generativeai package: pip install google-generativeai"
    )

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


class GeminiAI_Manager:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._model = None

    def get_gemini_client(self) -> Optional[Any]:
        if self._model is not None:
            return self._model
        if not self.api_key:
            return None
        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(DEFAULT_GEMINI_MODEL)
            return self._model
        except Exception as e:
            print(f"Error initializing Gemini client/model: {e}")
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
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 500,
                },
            )
            result = getattr(response, "text", None)
            if (
                not result
                and hasattr(response, "candidates")
                and hasattr(response.candidates[0].content.parts[0], "text")
            ):
                result = response.candidates[0].content.parts[0].text.strip()
            elif result:
                result = result.strip()
            else:
                result = ""
            return result
        except Exception as e:
            print(f"Error extracting job summary with Gemini: {e}")
            return None

    def get_embedding(
        self,
        text: str,
        client: Any,
        model: str = "models/embedding-001",
        max_length: int = 8000,
        retries: int = 2,
    ) -> Optional[List[float]]:

        if not text or not isinstance(text, str):
            print("Error: Invalid or empty text passed to get_embedding()")
            return None
        clean_text = text.strip()
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length]

        attempt = 0
        last_err = None
        while attempt < retries:
            try:
                resp = genai.embed_content(
                    model=model,
                    content=clean_text,
                    task_type="retrieval_document",
                )
                embedding = resp.get("embedding")
                if isinstance(embedding, list) and all(
                    isinstance(x, (float, int)) for x in embedding
                ):
                    return list(map(float, embedding))
                else:
                    print("Gemini API did not return valid embedding.")
                    return None
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    time.sleep(0.8 * (attempt + 1))
            attempt += 1
        print(f"Error obtaining Gemini embedding after {retries} attempts: {last_err}")
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
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 800,
                },
            )
            result = getattr(response, "text", None)
            if (
                not result
                and hasattr(response, "candidates")
                and hasattr(response.candidates[0].content.parts[0], "text")
            ):
                result = response.candidates[0].content.parts[0].text.strip()
            elif result:
                result = result.strip()
            else:
                result = ""
            json_match = re.search(r"\{[\s\S]*\}", result)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except Exception as e:
                    print(f"Error decoding JSON from Gemini response: {e}")
                    return None
            return None
        except Exception as e:
            print(f"Error analyzing job description with Gemini: {e}")
            return None

    def enhance_achievements_with_ai(
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
                prompt,
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 300,
                },
            )
            result = getattr(response, "text", None)
            if (
                not result
                and hasattr(response, "candidates")
                and hasattr(response.candidates[0].content.parts[0], "text")
            ):
                result = response.candidates[0].content.parts[0].text.strip()
            elif result:
                result = result.strip()
            else:
                result = ""
            json_match = re.search(r"\[[\s\S]*\]", result)
            if json_match:
                try:
                    suggested = json.loads(json_match.group())
                    return suggested[:2]
                except Exception as e:
                    print(f"Error decoding Gemini achievements JSON: {e}")
                    return None
            return None
        except Exception as e:
            print(f"Error enhancing achievements with Gemini: {e}")
            return None

    def generate_resume_content(
        self,
        user_profile: dict,
        job_summary: str,
        client: Any = None,
    ) -> str:
        if not client:
            raise ValueError("AI client (Gemini) must be supplied.")
        prompt = f"""Generate a professional resume for the following candidate.
            You are an expert resume writer.
            Use an ATS-optimized, modern template.
            Return ONLY the resume content as a single string in markdown or plain text.
            Do not add any explanations.

            Candidate Profile:
            {json.dumps(user_profile, indent=2)}

            Job Summary:
            {job_summary}
            """
        try:
            response = client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.5,
                    "max_output_tokens": 1200,
                },
            )
            result = getattr(response, "text", None)
            if (
                not result
                and hasattr(response, "candidates")
                and hasattr(response.candidates[0].content.parts[0], "text")
            ):
                result = response.candidates[0].content.parts[0].text.strip()
            elif result:
                result = result.strip()
            else:
                result = ""
            return result
        except Exception as e:
            print(f"Error generating resume content with Gemini: {e}")
            return ""

    def generate_cover_letter_content(
        self,
        user_profile: Dict[str, Any],
        job_summary: str,
        client: Any = None,
    ) -> Optional[Dict[str, str]]:
        if not client:
            return None
        prompt = f"""Write a professional cover letter for this candidate applying to this job.

            Candidate Profile:
            Name: {user_profile.get('name', '')}
            Summary: {user_profile.get('professional_summary', '')[:300]}
            Key Skills: {', '.join(user_profile.get('technical_skills', [])[:10])}

            Job Summary:
            {job_summary}

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
        try:
            response = client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 600,
                },
            )
            result = getattr(response, "text", None)
            if (
                not result
                and hasattr(response, "candidates")
                and hasattr(response.candidates[0].content.parts[0], "text")
            ):
                result = response.candidates[0].content.parts[0].text.strip()
            elif result:
                result = result.strip()
            else:
                result = ""
            json_match = re.search(r"\{[\s\S]*\}", result)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except Exception as e:
                    print(f"Error decoding Gemini cover letter JSON: {e}")
                    return None
            return None
        except Exception as e:
            print(f"Error generating cover letter content with Gemini: {e}")
            return None
