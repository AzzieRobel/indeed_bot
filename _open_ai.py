from typing import Any, Optional, List
import time

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not installed. Install with: pip install openai")


class OpenAI_Manager:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def get_openai_client(self) -> Optional[Any]:
        if not OPENAI_AVAILABLE:
            return None

        if not self.api_key:
            return None

        try:
            return OpenAI(api_key=self.api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return None


    def extract_job_summary_with_openai(
        self, job_link: str, client: Any, browser_page=None
    ) -> Optional[str]:
        if not client:
            return None

        text_content = None

        try:
            if browser_page:
                try:
                    browser_page.goto(job_link, wait_until="load", timeout=30000)
                    time.sleep(2)

                    try:
                        body_text = browser_page.query_selector("body")
                        if body_text:
                            text_content = body_text.inner_text()[:8000]
                    except Exception:
                        html = browser_page.content()
                        text_content = html[:8000]

                except Exception as e:
                    print(f"  Warning: Browser failed, falling back to HTTP: {e}")
                    text_content = None

            if text_content:
                prompt = f"""
                    Extract and summarize the following job posting text.

                    Provide a concise summary (200–300 words) including:
                    - Job title
                    - Company name
                    - Location (city/state/remote)
                    - Job type (FT/PT/contract)
                    - Technical skills
                    - Soft skills
                    - Languages
                    - Job preferences
                    - Experience level
                    - Key responsibilities
                    - Salary if mentioned

                    Job posting content:
                    {text_content[:6000]}
                """
            else:
                prompt = f"""
                Extract and summarize the job posting from this URL:
                URL: {job_link}

                If the page content cannot be accessed, infer based on the URL structure.

                Provide a concise 200–300 word summary including:
                - Job title (if identifiable)
                - Company name (if identifiable)
                - Location (if identifiable)
                - Any other inferred details
                """

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
