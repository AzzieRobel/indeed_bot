# Milestone 2 - Resume & Cover Letter Generator

## Overview

This milestone implements an **automatic, ATS-optimized resume and cover letter generator** that leverages both traditional keyword extraction and **generative AI models** (Gemini API or OpenAI, if available) to tailor documents for each job posting.

## Features

✅ **ATS-Friendly Formatting**
- Clean, simple layouts using standard fonts (Calibri)
- No graphics, unnecessary tables, or complex formatting
- Clearly separated sections for easy parsing

✅ **Dynamic Keyword Insertion**
- Job descriptions are parsed with AI (Gemini/OpenAI) or fallback keyword extraction
- Extracts job-specific keywords and requirements
- Prioritizes skills that overlap with the user's profile

✅ **Achievement Enhancement**
- Enhances user's achievements by matching job requirements
- AI or heuristics can suggest stronger achievement statements using job language

✅ **Multi-format Output**
- Generates .docx (Word) documents by default
- Optionally exports PDFs (via docx2pdf if available)

✅ **Flexible Template System**
- Uses system from `_doc_generator.py` (Modern, Classic resume templates, standard cover letter)
- Templates are auto-generated if missing

## Class Structure

### `ResumeCoverLetterGenerator`

Main class for document generation. Relies on `TemplateManager` from `_doc_generator.py`, ensuring backward compatibility.

**Core Methods:**
- `analyze_job_description()`: Extracts job keywords/skills/requirements using AI if possible, otherwise basic extraction
- `generate_resume()`: Builds a personalized resume in DOCX
- `generate_cover_letter()`: Builds a tailored cover letter in DOCX
- `export_to_pdf()`: Converts DOCX file(s) to PDF if dependency available
- `generate_documents()`: Full pipeline for resume + cover letter in one step

## Usage

### Typical Usage

```python
import yaml
from _resume_generator import ResumeCoverLetterGenerator
from _gemini_ai import GeminiAI_Manager

# Load user profile from config.yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
user_profile = config["user_profile"]

# Initialize Gemini AI manager (or pass None for fallback logic)
import os
gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_manager = GeminiAI_Manager(api_key=gemini_api_key)
generator = ResumeCoverLetterGenerator(ai_provider=gemini_manager)

# Get Gemini client if available
gemini_client = gemini_manager.get_gemini_client() if gemini_manager else None

# Generate documents
job_description = "Paste job description here."
results = generator.generate_documents(
    candidate_profile=user_profile,
    job_description=job_description,
    company_name="Some Company",
    company_address="123 Main St",
    hiring_manager="John Doe",
    template_name="resume_modern.docx",
    export_pdf=True,
    ai_client=gemini_client,
)
print("Resume file:", results.get("resume_docx"))
print("Cover letter file:", results.get("cover_letter_docx"))
```

### Command Line Usage

```bash
# Generate for a job from the database
python generate_documents.py --from-db

# Generate with a custom job description
python generate_documents.py --job-description "Senior Node.js Developer, remote..."

# Specify which template to use
python generate_documents.py --from-db --template resume_classic.docx

# Output DOCX only (skip PDF)
python generate_documents.py --from-db --no-pdf
```

## Integration Details

- **AI Support**: The `ResumeCoverLetterGenerator` can use an AI provider (`GeminiAI_Manager` or OpenAI manager) for smarter job analysis, but will use a built-in keyword extraction fallback if unavailable.
- **Data Sources**: Loads user profiles from `config.yaml` and jobs from the `Database` class.
- **Templates**: Uses unmodified functions and system from `_doc_generator.py`.
- **Config**: User profile stored in `config.yaml`.

## How it Works

1. **Job Description Analysis:**  
   - Prefers Gemini or OpenAI for extracting technical/soft skills, keywords, and role-specific language.
   - Will fall back to a regex/heuristic keyword extraction if no AI is available.

2. **Resume Generation:**
   - Combines user's skills and achievements with extracted job requirements.
   - Highlights matched skills and tunes achievements for relevance.
   - Formats the resume/cover letter according to chosen template.
   - Fills all placeholders with candidate/job/company data.
   - Outputs DOCX and (optionally) PDF.

3. **Cover Letter Generation:**
   - Uses Gemini/OpenAI to generate personalized content or falls back to template-based paragraphs.
   - Ensures company information, user profile, and date fields are correctly substituted.
   - Produces DOCX (and optionally PDF).

## Output

Default output directory is `output/documents/`:

```
output/documents/
├── resume_YYYYMMDD_HHMMSS.docx
├── resume_YYYYMMDD_HHMMSS.pdf
├── cover_letter_YYYYMMDD_HHMMSS.docx
└── cover_letter_YYYYMMDD_HHMMSS.pdf
```

## Dependencies

- `python-docx` (DOCX generation)
- `PyYAML` (Parsing config)
- `docx2pdf` (optional, PDF export)
- `google-generativeai` (optional, for Gemini support)

Install basics with:
```bash
pip install python-docx PyYAML docx2pdf google-generativeai
```
*(You can skip `docx2pdf` and `google-generativeai` if not exporting PDF or using Gemini.)*

## ATS Optimization Details

- **Simple Formatting:** Calibri font, regular headings, no graphics
- **Keyword Optimization:** Job-matching keywords infused by both AI and fallback
- **Structured Sections:** Experience, Education, Skills, Certifications
- **Bullet Points:** For easy ATS parsing in experience and skills

## Example Output

**Resume Sections:**
- Header: Name, email, phone, location
- Professional Summary: Customized for job
- Skills: User + job-matched
- Experience: Roles, bullets tuned to job language
- Education: Standard/concise display
- Certifications: Optional

**Cover Letter Sections:**
- Date, company header
- Dynamic opening (interest/fit)
- 1-2 rich body paragraphs (achievements, experience)
- Closing with enthusiasm/CTA
- Candidate signature

## Additional Notes

- `_doc_generator.py`’s functions/templates are never modified in place
- Missing templates are auto-generated on demand
- PDF export is optional and requires extra dependencies
- System functions without Gemini or OpenAI (basic keyword extraction only)
- All outputs maintain ATS best practices

## Future Directions

- Enhanced PDF styling/control
- Custom user templates
- Integration with Gemini's vision API for visual resume critique
- Scoring of resumes against job description (ATS simulation)
- CLI batch mode for multiple jobs or candidates
