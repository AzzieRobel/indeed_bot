import requests

class GeminiAI:

    def __init__(self, api_key: str, model: str = "models/gemini-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        # Don't import requests here; assume it is available in the environment.

    def extract_summary(self, job_detail: str, extra_context: str = "") -> str:

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
        if extra_context:
            prompt += extra_context + "\n\n"
        prompt += f"Job Description:\n{job_detail.strip()}"

        endpoint = f"{self.base_url}/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        try:
            response = requests.post(endpoint, json=body, headers=headers, params=params, timeout=25)
            response.raise_for_status()
            data = response.json()
            # Safely extract the summary text
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"].strip()
        except Exception as e:
            print(f"Gemini summary extraction error: {e}")
        return ""

