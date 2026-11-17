# Automated Resume Parser

Extract structured candidate information (name, skills, education, contact details)
from resumes (PDF / DOCX), store it in PostgreSQL, and search it through a Flask API
and lightweight web UI.

## Tech stack

| Layer | Technology |
| --- | --- |
| Web framework | Flask |
| ORM / database | SQLAlchemy + PostgreSQL |
| Text extraction | pdfplumber (PDF), python-docx (DOCX) |
| NLP | spaCy (`en_core_web_sm`) with regex fallbacks |
| Server | Gunicorn (production) / Flask dev server |

## Features

- Upload one or more resumes at once (`.pdf`, `.doc`, `.docx`, max 10 MB each).
- Extract **name**, **email**, **phone**, **location**, **summary**,
  **years of experience**, **skills** and **education**.
- Skills are matched against a curated, extensible catalogue
  (`app/parser/skills_data.py`) with alias support.
- Normalised relational storage: candidates ↔ skills (many-to-many), education
  records (one-to-many).
- Search across name, email, location, raw text, skills and education; filter by
  skill; paginated results.
- Simple browser UI for uploading, browsing, viewing and deleting candidates.

## Setup

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts PostgreSQL on `localhost:5432` with user `resume`, password `resume`,
database `resume_parser`. Alternatively, use any PostgreSQL instance and set
`DATABASE_URL` accordingly.

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

> The spaCy model is optional. If it isn't installed, the parser still works using
> regex/keyword fallbacks (name detection falls back to the first line).

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` as needed (secret key, database URL, upload folder, etc.).

### 4. Run

```bash
python run.py
```

Open <http://localhost:5000>. Tables are created automatically on startup.

For production:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/api/resumes/upload` | Multipart upload (`files`) and parse resumes |
| `GET` | `/api/candidates` | List/search candidates (`q`, `skill`, `page`, `per_page`) |
| `GET` | `/api/candidates/<id>` | Candidate detail (includes raw text) |
| `DELETE` | `/api/candidates/<id>` | Delete a candidate |
| `GET` | `/api/skills` | All known skills |

### Example

```bash
# Upload
curl -F "files=@resume.pdf" http://localhost:5000/api/resumes/upload

# Search
curl "http://localhost:5000/api/candidates?q=python&skill=Docker"
```

Example upload response:

```json
{
  "created": [{
    "id": 1,
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "phone": "+1 (415) 555-0132",
    "location": "San Francisco",
    "years_experience": 5.0,
    "skills": ["AWS", "Docker", "Machine Learning", "Python", "SQL"],
    "education": [{
      "degree": "M.S.",
      "institution": "Stanford University",
      "field_of_study": "Computer Science",
      "year": "2019"
    }]
  }],
  "errors": []
}
```

## Sample resumes

Eight test resumes (4 candidates in both PDF and DOCX) are stored on the Desktop in
`C:\Users\Ilyas\Desktop\sample_resumes`. Regenerate them with:

```bash
python samples/generate_samples.py
```

## Tests

```bash
pytest -q
```

## Project structure

```
resume_parser/
├── app/
│   ├── __init__.py        # app factory
│   ├── config.py          # environment-based config
│   ├── extensions.py      # SQLAlchemy instance
│   ├── models.py          # Candidate / Skill / Education models
│   ├── parser/
│   │   ├── extractor.py   # PDF/DOCX text extraction
│   │   ├── nlp.py         # field extraction logic
│   │   └── skills_data.py # skill catalogue
│   ├── routes/api.py      # API + UI routes
│   ├── templates/         # web UI
│   └── static/            # styles
├── tests/                 # parser unit tests
├── uploads/               # stored originals (gitignored)
├── docker-compose.yml     # local PostgreSQL
├── run.py                 # dev entry point
└── requirements.txt
```

## Notes & limitations

- **Scanned/image-only PDFs** contain no text layer and cannot be parsed without OCR.
  Add Tesseract + `pytesseract` if OCR support is needed.
- Legacy `.doc` files are not fully supported by `python-docx`; convert to `.docx`
  for reliable results.
- Extraction is heuristic. For higher accuracy, fine-tune a spaCy NER model on
  labelled resumes or integrate an LLM-based extractor.
