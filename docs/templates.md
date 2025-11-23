# Resume & Cover Letter Template Placeholders

These are the variable placeholders recognized by the resume and cover letter generators. The code will replace these tokens in DOCX templates using the information from your profile, AI-extracted job data, and config.yaml.

## Resume Templates

### `resume_classic.docx`
| Placeholder                  | Description                            |
|------------------------------|----------------------------------------|
| `${FULL_NAME}`               | Candidate's full name                  |
| `${PROFESSIONAL_TITLE}`      | Target job title                       |
| `${CONTACT_BLOCK}`           | Email, phone, location, links          |
| `${SUMMARY}`                 | Short professional summary             |
| `${CORE_SKILL_1}` ...<br>`${CORE_SKILL_4}` | Top 4 core skills as bullets/fields        |
| `${EXPERIENCE_SECTION}`      | Full formatted work experience block   |
| `${EDUCATION_SECTION}`       | Educational background                 |
| `${CERTIFICATIONS_SECTION}`  | Certifications, awards, or licenses    |

### `resume_modern.docx`
| Placeholder                  | Description                                 |
|------------------------------|---------------------------------------------|
| `${FULL_NAME}`               | Candidate's name                            |
| `${TAGLINE}`                 | One-line positioning statement              |
| `${CONTACT_BLOCK}`           | Contact info (matches classic)              |
| `${PROFESSIONAL_PROFILE}`    | Summary/profile (from profile or AI)        |
| `${TECH_STACK}`              | Main tech skills - as keywords or line      |
| `${SOFT_SKILLS}`             | Relevant soft/personal skills               |
| `${EXPERIENCE_SECTION}`      | Work experience (smart merged for keywords) |
| `${PROJECTS_SECTION}`        | Top projects or quantified achievements     |
| `${EDUCATION_SECTION}`       | Educational background                      |

- Skills and achievements will be auto-blended with job requirements and ATS-friendly keywords by `_resume_generator.py`.
- Most templates require only `${...}` tokens as anchors; formatting and ordering are handled by the generator.

## Cover Letter Template

### `cover_letter_standard.docx`
| Placeholder              | Description                                        |
|--------------------------|----------------------------------------------------|
| `${DATE}`                | Today's date (auto-filled)                         |
| `${HIRING_MANAGER}`      | Hiring manager (provided/prompted/blank default)  |
| `${COMPANY_NAME}`        | Target company                                     |
| `${COMPANY_ADDRESS}`     | Address/location                                   |
| `${OPENING_PARAGRAPH}`   | Tailored intro (AI/persona-driven)                 |
| `${BODY_PARAGRAPH_1}`    | Paragraph highlighting fit (skills, achievements)  |
| `${BODY_PARAGRAPH_2}`    | Optional second body paragraph                     |
| `${CLOSING_PARAGRAPH}`   | Strong closing paragraph—enthusiasm, follow-up     |
| `${SIGN_OFF}`            | Sign-off line (e.g., "Sincerely" or "Best")        |
| `${FULL_NAME}`           | Candidate's name                                   |

---

**Note:**  
- All `${...}` placeholders are required in templates.  
- Do **not** remove or rename; the bot relies on these exact tokens for replacement and style preservation.
- To add fields (e.g. `${LINKEDIN}`), add them in the DOCX and extend your profile/config as needed.
- For advanced usage, see `docs/MILESTONE_2_README.md` and `_resume_generator.py` for mapping logic and extension options.
