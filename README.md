# VERITO — AI-Powered Evidence-Based News Verification

VERITO is an evidence-based fact-checking assistant designed to verify news claims transparently. Rather than generating opaque, arbitrary confidence scores (e.g. "82% real"), VERITO follows a structured verification methodology:

```
ARTICLE URL
    ↓
EXTRACT MAIN CLAIM
    ↓
SEARCH INDEPENDENT FACT-CHECK REGISTRIES & SOURCES
    ↓
CONTRAST EVIDENCE (SUPPORTING vs. CONTRADICTING)
    ↓
AI-POWERED EVIDENCE SYNTHESIS & REASONING
    ↓
SOURCE CITATIONS WITH DIRECT LINKS
```

---

## Repository Structure

```
AI-powered-fake-news-verification-tool/
├── frontend/                     # React + Vite + TypeScript frontend
│   ├── public/
│   │   └── favicon.svg           # VERITO favicon
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/           # Icons, Navbar, Footer
│   │   │   ├── layout/           # App layout wrappers
│   │   │   └── verification/     # UrlInput, ClaimSection, EvidenceSection,
│   │   │                         # EvidenceCard, AnalysisSection, SourcesSection,
│   │   │                         # StatusBadge, LoadingState, ErrorState, ResultsView
│   │   ├── services/
│   │   │   ├── api.ts            # Verification API client layer
│   │   │   └── api.test.ts       # Automated API & error-handling tests
│   │   ├── types/
│   │   │   └── verification.ts   # Shared TypeScript API contracts
│   │   ├── utils/
│   │   │   ├── urlValidator.ts   # URL format & protocol validation
│   │   │   └── urlValidator.test.ts # URL validation unit tests
│   │   ├── App.tsx               # Main application workflow & state
│   │   ├── index.css             # Modern CSS design system
│   │   └── main.tsx              # React DOM entrypoint
│   ├── .env                      # Local environment configuration
│   ├── .env.example              # Template environment variables
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                      # Flask + Python backend (Managed by teammate)
├── .gitignore                    # Git ignore rules for Node and Python
└── README.md                     # Project architecture and setup guide
```

---

## Technology Stack

* **Frontend:** Vite, React 19, TypeScript, Modern CSS design system (zero bloated CSS/component libraries).
* **Backend:** Flask, Python 3.12 (developed by backend teammate).
* **Communication Protocol:** JSON over HTTP (`POST /verify`).

---

## Getting Started (Frontend)

### Prerequisites

* Node.js `v20+` (tested on Node `v24.21.0`)
* npm `v10+` (tested on npm `11.19.0`)

### Installation & Development

1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   *(By default, `.env` points to `http://localhost:5000`)*

4. Start the development server:
   ```bash
   npm run dev
   ```
   The application will be available at: **`http://localhost:5173`**

### Scripts

* `npm run dev`: Launch local Vite development server on port 5173.
* `npm run build`: Typecheck with TypeScript and compile production bundle to `/dist`.
* `npm run lint`: Fast linting with oxlint.
* `npm test`: Run automated tests for URL validation and API error handling via Node's native test runner.

---

## Frontend-Backend API Contract

The frontend sends article verification requests to the Flask backend via:

### `POST /verify`

#### Request Body
```json
{
  "url": "https://example.com/news/article"
}
```

#### Successful Response (`200 OK`)
```json
{
  "claim": "Central factual assertion extracted from the article.",
  "status": "supported | contradicted | mixed | inconclusive",
  "supporting_evidence": [
    {
      "title": "Corroborating Report Title",
      "url": "https://trusted-source.org/factcheck/123",
      "source": "FactCheck Registry",
      "snippet": "Relevant excerpt supporting the claim..."
    }
  ],
  "contradicting_evidence": [
    {
      "title": "Debunking Report Title",
      "url": "https://factcheck.org/rebuttal/456",
      "source": "FactCheck.org",
      "snippet": "Relevant excerpt refuting the claim..."
    }
  ],
  "analysis": "AI-generated synthesis explaining what the gathered evidence indicates.",
  "sources": [
    {
      "title": "Source Article Title",
      "url": "https://trusted-source.org/factcheck/123",
      "source": "FactCheck Registry"
    }
  ]
}
```

#### Error Response (`400` / `500`)
```json
{
  "error": "Human-readable description of why extraction or verification failed."
}
```

---

## Note for Backend Teammate: CORS Requirement

When running locally (`http://localhost:5173` for frontend and `http://localhost:5000` for backend), browsers enforce the Same-Origin Policy. 

To enable seamless local communication, ensure Flask has **CORS** enabled for `http://localhost:5173`:

```python
# Example Flask CORS setup:
# pip install flask-cors
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/verify": {"origins": "http://localhost:5173"}})
```
