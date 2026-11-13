# BhoomiVaani (భూమివాణి)
### AI-Powered Voice-First Land Intelligence & Legal Awareness Platform

> **DEMONSTRATION PROTOTYPE NOTICE:**  
> BhoomiVaani utilizes entirely synthetic land records and simulated revenue extracts for educational and awareness purposes. Never execute binding financial transactions or property purchases without independent verification from a qualified civil property advocate and local land revenue authorities.

---

## 1. Project Overview

**BhoomiVaani** helps Indian land buyers—especially first-time agricultural land buyers, rural farmers, and urban investors—understand land listings, detect legal title risks (such as unreleased bank mortgages and disputed ancestral inheritance), verify speculative broker infrastructure claims, and explore opportunities using natural voice conversations in **Telugu (తెలుగు)**, **Hindi (हिन्दी)**, and **Indian English**.

The platform tackles information asymmetry in the Indian real estate market, reducing vulnerability to misleading broker statements through transparent, evidence-based data.

---

## 2. Technology Stack

- **Frontend:**
  - **Framework:** React 18, Vite 5, TypeScript 5
  - **Styling:** Tailwind CSS (Fintech forest-green, warm ivory, and gold palette)
  - **Icons:** Lucide React
  - **Analytics:** Recharts (3-year & 5-year illustrative growth projections)
- **Backend:**
  - **Framework:** Python 3.12, FastAPI, Pydantic v2, Uvicorn
  - **PDF Intelligence & Extraction:** `pypdf` (safe text extraction), `reportlab` (dynamic PDF dossier generation)
  - **HTTP & Networking:** `httpx` with timeout management and graceful connection fallbacks
- **AI Integration Pipeline:**
  - **STT (Speech-to-Text):** Gnani Prisma v2.5 (`https://api.vachana.ai/stt/v3`)
  - **Reasoning Engine:** Gnani Evon v3.3 30B (`gnani-evon-v3.3-30b-a3b` / Artha Sovereign AI stack)
  - **TTS (Text-to-Speech):** Gnani Timbre v2.5 (`https://api.vachana.ai/api/v1/tts/inference`)
  - **Simulation Mode:** Deterministic, offline `MOCK_MODE` with realistic Indic speech parsing and audio chime synthesis when credentials are not supplied.

---

## 3. Mandatory AI Pipeline

```
USER MICROPHONE
       │
       ▼
PRISMA v2.5 (Speech-to-Text)
       │
       ▼
TRANSCRIBED USER QUERY (Telugu / Hindi / English)
       │
       ▼
EVON v3.3 30B (Reasoning Engine)
       │
       ▼
STRUCTURED REASONING PAYLOAD
       ├────── Matched Land IDs (Selected strictly from database)
       ├────── Legal Risk Analysis (Mortgages, liens, civil suits)
       ├────── Infrastructure Claim Analysis (Officially announced vs Unverified)
       └────── Natural Language Explanation (Conversational Indic response)
       │
       ▼
TIMBRE v2.5 (Text-to-Speech)
       │
       ▼
AUDIO PLAYBACK (Audio Response in Browser)
```

---

## 4. Synthetic Land Database (`backend/data/lands.json`)

The platform contains exactly **6 realistic, fictional property holdings** around Hyderabad and Telangana:

| Land ID | Title | Location | District | Extent | Total Price | Legal Status | Key Infrastructure |
|---|---|---|---|---|---|---|---|
| **bv-hyd-01** | Sri Venkateshwara Farm Groves | Chevella | Ranga Reddy | 10.0 Acres | ₹420 Lakhs | **Clean Title Verified** | RRR Southern Arc (4.5 km) - Officially announced |
| **bv-hyd-02** | Ananthagiri Eco Terraces | Vikarabad Hills | Vikarabad | 5.5 Acres | ₹154 Lakhs | **Clean Title Verified** | Eco-Tourism Circuit (6 km) - Proposed |
| **bv-hyd-03** | Pragati Highway Agri-Vistas | Shadnagar | Ranga Reddy | 12.0 Acres | ₹660 Lakhs | **Clean Title Verified** | NH-44 6-Lane Expansion (2.1 km) - Operational |
| **bv-hyd-04** | Keesara Sunrise Meadows (Plot 4) | Keesara Gutta | Medchal-Malkajgiri | 6.0 Acres | ₹216 Lakhs | **Disputed / Active Encumbrance** | ₹85L Bank Lien + Pending Civil Suit OS 412/2022 |
| **bv-hyd-05** | Yadadri Divine Orchard | Bhuvanagiri | Yadadri | 8.0 Acres | ₹256 Lakhs | **Clean Title Verified** | Warangal Smart Highway (3.2 km) - Under construction |
| **bv-hyd-06** | Medak Heritage Farmlands | Narsapur | Medak | 10.0 Acres | ₹350 Lakhs | **Clean Title Verified** | RRR Northern Arc (2.8 km) - Officially announced |

---

## 5. Key Implemented Features

### Feature A: Voice-First Land Search
- Natural voice interaction with animated audio visualizer.
- Speech transcribed via **Prisma v2.5**, interpreted via **Evon v3.3 30B**, and spoken back via **Timbre v2.5**.
- Matching property cards are dynamically highlighted in the dashboard with animated golden-green borders.
- Clickable demo prompts included:
  1. *"Show me 10-acre clean agricultural land near Hyderabad."*
  2. *"Is Plot 4 safe to buy?"*
  3. *"Check whether the upcoming highway claim is verified."*

### Feature B: Broker Claim Checker
- Dedicated verification page (`/claims`).
- Evaluates real estate broker claims (e.g. *"A metro station will be built just 2 km from this land next year"*).
- Compares against statutory infrastructure evidence and classifies claims into:
  - `VERIFIED`
  - `PROPOSED`
  - `UNVERIFIED`
  - `CONTRADICTED`
- Discloses confidence score, documentary basis, and missing government notifications.

### Feature C: Legal Document Analyzer
- Upload PDF or text property documents (`/documents`).
- Extracts text safely and scans for critical red flags:
  - Undischarged mortgages & bank hypothecation
  - Active civil litigation (OS No. suits under Doctrine of Lis Pendens)
  - Missing co-parcener or legal heir signatures
  - Cadastral survey acreage variances
- Includes built-in **1-Click Synthetic Sample Deeds** (`sample_clean_patta_deed.txt` and `sample_disputed_mortgage_deed.txt`).
- Generates tailored questions to ask a licensed property advocate.

### Feature D: Land Growth Insights
- Interactive **Recharts** projection analytics (`/growth`).
- Toggle between **3-Year** and **5-Year** illustrative scenarios.
- Factors in infrastructure catalysts versus encumbrance drag.
- Displays statutory disclaimer distinguishing projections from guaranteed returns.

### Feature E: Side-by-Side Property Comparison
- Compare 2 to 3 properties side-by-side (`/compare`).
- Compares rate per acre, total valuation, legal encumbrance status, infrastructure evidence, and AI growth score.

### Feature F: Downloadable Land Report Dossier
- Generates authentic, print-ready PDF reports (`/api/lands/{land_id}/report`).
- Built with **ReportLab**, featuring valuation tables, legal risk badges, infrastructure checklists, and statutory buyer precautions.
- Prominently watermarked: `"DEMONSTRATION REPORT - SYNTHETIC DATA - NOT AN OFFICIAL LAND CERTIFICATE"`.

---

## 6. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check, Gnani AI stack status, and database stats |
| `GET` | `/api/lands` | Get all lands with optional filters (district, acres, budget, type) |
| `GET` | `/api/lands/{land_id}` | Retrieve individual property dossier |
| `POST` | `/api/lands/compare` | Compare multiple properties side-by-side |
| `GET` | `/api/lands/{land_id}/report` | Download print-ready PDF dossier |
| `POST` | `/api/ai/chat` | Evon v3.3 30B reasoning chat endpoint |
| `POST` | `/api/ai/transcribe` | Prisma v2.5 Speech-to-Text audio transcription |
| `POST` | `/api/ai/speak` | Timbre v2.5 Text-to-Speech audio synthesis |
| `POST` | `/api/claims/check` | Broker statement evidence evaluation |
| `POST` | `/api/documents/analyze` | Safe legal deed PDF/TXT analysis |
| `GET` | `/api/documents/samples` | List built-in synthetic sample documents |
| `GET` | `/api/documents/samples/{id}` | Fetch content and pre-run analysis for a sample |

---

## 7. Running the Project

### Prerequisites
- Python 3.10+ (tested on Python 3.12.10)
- Node.js 18+ (tested on Node.js v24.17.0)

### Quick Start (Single Command)

```bash
# Clone or navigate to the repository
cd bhoomivaani

# Launch both Backend (port 8000) and Frontend (port 5173) concurrently
python start.py
```

*Alternatively on Windows:*
```cmd
run.bat
```

*Alternatively on Linux / GitHub Codespaces:*
```bash
chmod +x run.sh
./run.sh
```

### Manual Individual Commands

**Backend:**
```bash
# Install backend dependencies
python -m pip install -r backend/requirements.txt

# Start FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Localhost URLs
- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 8. Configuration & Environment Variables

Copy `.env.example` to `.env`:

```ini
GNANI_API_KEY=
PRISMA_API_URL=https://api.vachana.ai/stt/v3
EVON_API_URL=https://api.vachana.ai/v1/chat/completions
TIMBRE_API_URL=https://api.vachana.ai/api/v1/tts/inference
MOCK_MODE=true
DEFAULT_LANGUAGE=te
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

- When `MOCK_MODE=true` (or when `GNANI_API_KEY` is empty), the entire platform operates offline in simulation mode with realistic STT, LLM reasoning, and TTS audio synthesis without requiring third-party credentials.
- When `GNANI_API_KEY` is provided, live requests authenticate via the `X-API-Key-ID` header.

---

## 9. Automated Testing Results

The backend contains a full automated **pytest** test suite in `backend/tests/test_api.py`.

Run tests:
```bash
python -m pytest backend/tests/test_api.py -v
```

**Test Execution Summary:**
```
backend/tests/test_api.py::test_health_check PASSED                      [  6%]
backend/tests/test_api.py::test_get_all_lands PASSED                     [ 13%]
backend/tests/test_api.py::test_filter_lands PASSED                      [ 20%]
backend/tests/test_api.py::test_disputed_property_details PASSED         [ 26%]
backend/tests/test_api.py::test_compare_lands PASSED                     [ 33%]
backend/tests/test_api.py::test_pdf_report_generation PASSED             [ 40%]
backend/tests/test_api.py::test_ai_chat_prompt_1_clean_10_acre PASSED    [ 46%]
backend/tests/test_api.py::test_ai_chat_prompt_2_plot_4_safety PASSED    [ 53%]
backend/tests/test_api.py::test_ai_chat_prompt_3_highway_claim PASSED    [ 60%]
backend/tests/test_api.py::test_broker_claim_checker_metro PASSED        [ 66%]
backend/tests/test_api.py::test_broker_claim_checker_guarantee PASSED    [ 73%]
backend/tests/test_api.py::test_document_analysis_clean PASSED           [ 80%]
backend/tests/test_api.py::test_document_analysis_disputed PASSED        [ 86%]
backend/tests/test_api.py::test_text_to_speech PASSED                    [ 93%]
backend/tests/test_api.py::test_speech_to_text PASSED                    [100%]

======================= 15 passed in 14.62s ========================
```

---

## 10. Security & Ethical Safeguards

1. **API Key Isolation:** API credentials reside strictly in backend environment variables and are never bundled into client JavaScript.
2. **Safe PDF & Text Extraction:** Files are treated strictly as passive text data; prompt injection instructions embedded inside uploaded documents are ignored.
3. **Upload Constraints:** File uploads are capped at 10 MB and restricted to `.pdf` and `.txt`.
4. **Deterministic Land Grounding:** The Evon reasoning engine is constrained to select only valid IDs from `lands.json`. It cannot invent properties or fictitious survey numbers.
5. **No False Government Verification:** Every report and UI screen bears a clear disclaimer stating that mock records do not represent official revenue or Sub-Registrar certifications.
