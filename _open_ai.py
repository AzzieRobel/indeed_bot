from typing import Any, Optional, List, Dict
from openai import OpenAI
import json
import re

class OpenAI_Manager:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def get_openai_client(self) -> Optional[Any]:
        if not self.api_key:
            return None
        try:
            return OpenAI(api_key=self.api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return None

    def extract_job_summary_with_openai(
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
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a job posting analyzer. Extract key information from job postings and create structured summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error extracting job summary with OpenAI: {e}")
            return None

    def get_embedding(
        self,
        text: str,
        client: Any,
        model: str = "text-embedding-3-small",
        max_length: int = 8000,
        retries: int = 2,
    ) -> Optional[List[float]]:
        if not client:
            print("Error: OpenAI client missing in get_embedding()")
            return None
        if not text or not isinstance(text, str):
            print("Error: Invalid or empty text passed to get_embedding()")
            return None
        clean_text = text.strip()
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length]
        for attempt in range(retries + 1):
            try:
                response = client.embeddings.create(model=model, input=clean_text)
                if not response or not response.data or len(response.data) == 0:
                    print("Error: Empty embedding response from OpenAI")
                    continue
                return response.data[0].embedding
            except Exception as e:
                print(f"[Attempt {attempt+1}] Error getting embedding: {e}")
        print("Embedding failed after retries.")
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
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a job description analyzer. Extract key information in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.3,
            )
            result = response.choices[0].message.content.strip()
            json_match = re.search(r"\{[\s\S]*\}", result)
            if json_match:
                return json.loads(json_match.group())
            else:
                return None
        except Exception as e:
            print(f"Error analyzing job description with OpenAI: {e}")
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
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a resume optimizer. Suggest enhanced achievement statements.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.4,
            )
            result = response.choices[0].message.content.strip()
            json_match = re.search(r"\[[\s\S]*\]", result)
            if json_match:
                suggested = json.loads(json_match.group())
                return suggested[:2]
            return None
        except Exception as e:
            print(f"Error enhancing achievements with OpenAI: {e}")
            return None

    def generate_resume_content(
        self,
        user_profile: dict,
        job_summary: str,
        ai_client: Any = None,
    ) -> str:
        if not ai_client:
            raise ValueError("AI client (OpenAI) must be supplied.")
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
        system_message = (
            "You are an expert resume writer. "
            "Generate a concise, ATS-friendly, modern resume based on the information provided."
        )
        try:
            response = ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1200,
                temperature=0.5,
            )
            resume = response.choices[0].message.content.strip()
            return resume
        except Exception as e:
            print(f"Error generating resume content with OpenAI: {e}")
            return ""

    def generate_cover_letter_content(
        self,
        user_profile: Dict[str, Any],
        job_summary: str,
        ai_client: Any = None,
    ) -> Optional[Dict[str, str]]:
        if not ai_client:
            return None
        try:
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
            response = ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional cover letter writer. Write compelling, ATS-friendly cover letters.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=600,
                temperature=0.7,
            )
            result = response.choices[0].message.content.strip()
            json_match = re.search(r"\{[\s\S]*\}", result)
            if json_match:
                return json.loads(json_match.group())
            return None
        except Exception as e:
            print(f"Error generating cover letter content with OpenAI: {e}")
            return None
