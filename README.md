# MineSync AI - MVP

**AI-Powered Geological, Mining & Production Intelligence Platform**

An enterprise-grade web application that processes mining and geological documents, extracts structured data, enables AI-powered querying, and generates parliamentary responses with complete source traceability. Built with React, FastAPI, and PostgreSQL—designed for on-premise deployment with offline AI capabilities.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+ and npm
- PostgreSQL 12+
- Git

### 1. Database Setup

Create a PostgreSQL database:

```bash
psql -U postgres
CREATE DATABASE minesync_ai;
\q
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create `.env` file in `backend/`:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/minesync_ai
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
```

Start the backend:

```bash
python main.py
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

In a new terminal:

```bash
cd frontend
npm install
npm start
```

The frontend will open at `http://localhost:3000`

## Project Structure

```
minesync-ai-mvp/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Sidebar.js
│   │   │   ├── Dashboard.js
│   │   │   ├── Documents.js
│   │   │   ├── AIQuery.js
│   │   │   ├── ParliamentaryQuery.js
│   │   │   └── Analytics.js
│   │   ├── App.js
│   │   └── App.css
│   ├── package.json
│   └── ...
│
├── backend/                  # FastAPI application
│   ├── main.py             # FastAPI app & endpoints
│   ├── models.py           # SQLAlchemy ORM models
│   ├── database.py         # Database connection
│   ├── schemas.py          # Pydantic schemas
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
│
└── docs/                    # Documentation

```

## Architecture

### Frontend (React)

**Pages:**
- **Dashboard** - KPI cards, system status
- **Documents** - Upload documents, view processing status
- **AI Query** - Natural language Q&A (Phase 5+)
- **Parliamentary Query** - Structured official responses (Phase 6+)
- **Analytics** - System metrics and performance data

**Design:**
- Professional government/enterprise appearance
- Navy/blue primary color scheme
- Responsive grid-based layout
- Status badges and loading states

### Backend (FastAPI)

**Core Endpoints:**

Document Management:
- `POST /documents/upload` - Upload a document
- `GET /documents` - List documents
- `GET /documents/{id}` - Get document details
- `POST /documents/{id}/process` - Trigger processing

Extraction:
- `GET /documents/{id}/extraction` - Get extracted records

Queries:
- `POST /query` - Create standard query
- `POST /parliamentary-query` - Create parliamentary query

Reports:
- `POST /reports/generate` - Generate report

Analytics:
- `GET /analytics` - Get dashboard metrics

### Database (PostgreSQL)

**Tables:**
- `documents` - Uploaded documents with status
- `document_pages` - Page-level text and metadata
- `extracted_records` - Structured extracted data
- `validation_results` - Validation checks and flags
- `queries` - Query history
- `query_sources` - Query to source document mapping
- `reports` - Generated reports
- `topics` - Topic/keyword analysis
- `audit_logs` - Complete audit trail

## Phase 1: Current Status ✓

**Completed:**
- ✓ React project with sidebar navigation
- ✓ FastAPI backend with CORS support
- ✓ PostgreSQL models and database connection
- ✓ Document upload functionality
- ✓ Basic dashboard with KPI cards
- ✓ Document list view
- ✓ Placeholder pages for all main features

**What's Working:**
1. Upload documents (PDF, DOCX, XLSX, PNG, JPG)
2. View uploaded documents in the UI
3. See system analytics dashboard
4. Navigate between different application pages
5. API documentation at `/docs`

**How to Test:**

1. Go to http://localhost:3000
2. Click "Documents" in the sidebar
3. Select document type and upload a test file
4. Document appears in the list
5. Check Dashboard for updated metrics

## Development Phases

### Phase 2: OCR & Document Processing
- Tesseract OCR integration
- PaddleOCR for multilingual support
- PyMuPDF for PDF processing
- Text extraction from DOCX, XLSX
- Document classification
- Table detection

### Phase 3: AI Data Extraction
- Structured data extraction schema
- Local LLM integration (Ollama/llama.cpp)
- JSON storage of extracted fields
- Confidence scoring
- Database persistence

### Phase 4: Validation & Standardization
- Unit normalization (MT, tons, etc.)
- Cross-document comparison
- Anomaly detection
- Duplicate detection
- Human verification workflow

### Phase 5: Semantic Search & RAG
- Embeddings with Sentence Transformers
- FAISS/ChromaDB vector database
- Retrieval-Augmented Generation
- Source citation
- Multi-source synthesis

### Phase 6: Parliamentary Query Assistant
- Structured query understanding
- Evidence table generation
- Draft response generation
- Human review and approval workflow
- Export as official document

### Phase 7: Reports & Analytics
- Report generation with filters
- Production trend charts
- Target vs actual analysis
- Word cloud and topic identification
- Analytics dashboard

### Phase 8: Security, Deployment & Polish
- Authentication and RBAC
- Error handling
- UI polish and loading states
- Docker containerization
- Demo dataset
- Testing

## Environment Variables

**Backend (.env)**
```
DATABASE_URL=postgresql://user:password@localhost:5432/minesync_ai
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
```

**Frontend (.env.local - optional)**
```
REACT_APP_API_URL=http://localhost:8000
```

## Technology Stack

**Frontend:**
- React 18+
- CSS3 (no external CSS framework for Phase 1)

**Backend:**
- Python 3.10+
- FastAPI
- SQLAlchemy ORM
- Pydantic

**Database:**
- PostgreSQL 12+

**Future (Phases 2-8):**
- OCR: Tesseract, PaddleOCR
- NLP: spaCy, NLTK, Transformers
- Embeddings: Sentence Transformers
- Vector DB: FAISS or ChromaDB
- Local LLM: Ollama or llama.cpp
- Deployment: Docker, Docker Compose

## API Documentation

Interactive API docs available at: `http://localhost:8000/docs`

### Example: Upload a Document

```bash
curl -X POST "http://localhost:8000/documents/upload?document_type=production_report" \
  -F "file=@sample.pdf"
```

### Example: List Documents

```bash
curl "http://localhost:8000/documents?skip=0&limit=10"
```

### Example: Get Analytics

```bash
curl "http://localhost:8000/analytics"
```

## File Upload Support

Supported formats:
- PDF (.pdf)
- Word (.docx)
- Excel (.xlsx)
- Images (.png, .jpg, .jpeg)

Maximum file size: 100MB (configurable)

## Data Privacy & Security

**Phase 1 - MVP:**
- Documents stored locally in `uploads/` directory
- Database access via localhost
- No external API calls
- Environment variables for secrets

**Production Considerations (Phase 8+):**
- User authentication and role-based access
- Encrypted storage
- Audit logging
- Network isolation
- Data retention policies
- Secure API key management

## Troubleshooting

### Backend won't start
- Ensure PostgreSQL is running: `psql -U postgres`
- Check `.env` file has correct DATABASE_URL
- Verify port 8000 is not in use

### Frontend can't reach backend
- Ensure backend is running on http://localhost:8000
- Check CORS is enabled (it is by default)
- Try clearing browser cache

### Database connection error
- Verify PostgreSQL is running
- Check username/password in DATABASE_URL
- Ensure database `minesync_ai` exists
- Run: `psql -U postgres -d minesync_ai -c "\dt"` to verify tables

### Port conflicts
- Backend: Change `BACKEND_PORT` in `.env`
- Frontend: `npm start` will prompt for alternate port

## Next Steps

1. **Test Phase 1:** Upload a document and verify it appears in the UI
2. **Phase 2:** Implement OCR and document processing
3. **Phase 3:** Add AI extraction with local LLM
4. **Continue through Phases 4-8**

## Documentation Files

- `CLAUDE.md` - AI coding agent instructions and patterns
- `API.md` - Detailed API endpoint documentation (Phase 2+)
- `DEPLOYMENT.md` - Docker and on-premise deployment guide (Phase 8)

## Support

For issues or questions, refer to the specification document:
`MineSync_AI_Build_Specification_Offline_Updated.txt`

## License

Internal use only - Mining industry application

---

**Status:** Phase 1 MVP - Document Management & Basic UI
**Last Updated:** 2026-09-08
**Next Phase:** OCR & Document Processing (Phase 2)
