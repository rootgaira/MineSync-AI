# Phase 2: OCR & Document Processing - Installation & Setup Guide

## What's New in Phase 2

Phase 2 adds full document processing capabilities:
- ✅ PDF text extraction (PyMuPDF)
- ✅ DOCX parsing (python-docx)
- ✅ XLSX parsing (openpyxl)
- ✅ Image OCR (Tesseract + PaddleOCR)
- ✅ Document classification
- ✅ Table detection
- ✅ Extracted text stored in database
- ✅ New API endpoints for page access

## New Files

1. **processor.py** (400+ lines)
   - `DocumentProcessor` class
   - PDF, DOCX, XLSX, Image processing
   - Tesseract + PaddleOCR support
   - Document classification logic
   - Table extraction

2. **processing_service.py** (150+ lines)
   - `ProcessingService` class
   - Orchestrates processing workflow
   - Stores extracted pages in database
   - Error handling

## Installation Steps

### Step 1: Update Python Dependencies

```bash
cd backend

# Activate virtual environment
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install new dependencies
pip install -r requirements.txt
```

This installs:
- `pymupdf` - PDF processing
- `python-docx` - Word document parsing
- `openpyxl` - Excel parsing
- `pillow` - Image handling
- `pytesseract` - Tesseract OCR wrapper
- `paddleocr` - Multilingual OCR
- `pdf2image` - PDF to image conversion

### Step 2: Install Tesseract OCR (Optional but Recommended)

#### Windows
```bash
# Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Or use Chocolatey:
choco install tesseract

# Or use scoop:
scoop install tesseract
```

#### macOS
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr
```

**Note:** Tesseract must be installed separately. The `pytesseract` Python package is just a wrapper.

### Step 3: Verify Installation

```bash
# Test Tesseract installation
tesseract --version

# Test Python imports
python -c "import fitz; print('PyMuPDF OK')"
python -c "import docx; print('python-docx OK')"
python -c "import openpyxl; print('openpyxl OK')"
python -c "import pytesseract; print('pytesseract OK')"
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

### Step 4: Configure Pytesseract Path (if needed)

If Tesseract is not found, add to `processor.py`:

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
# pytesseract.pytesseract.pytesseract_cmd = '/usr/local/bin/tesseract'  # macOS
```

## Testing Phase 2

### 1. Start Backend

```bash
cd backend
python main.py
```

Expected output:
```
✓ Tesseract OCR initialized
✓ PaddleOCR initialized
✓ MineSync AI backend started
```

### 2. Start Frontend (new terminal)

```bash
cd frontend
npm start
```

### 3. Test Document Upload & Processing

**Using Frontend:**
1. Go to http://localhost:3000
2. Click "Documents"
3. Select document type
4. Upload a test PDF or image
5. Click the Process button (🔄) when document appears

**Using API directly:**

```bash
# Upload document
curl -X POST "http://localhost:8000/documents/upload?document_type=production_report" \
  -F "file=@sample.pdf"

# Response will include document_id, e.g. "id": 1

# Process document
curl -X POST "http://localhost:8000/documents/1/process"

# Response:
# {
#   "success": true,
#   "document_id": 1,
#   "pages_extracted": 5,
#   "classification": "production_report",
#   "processing_method": "PyMuPDF + OCR"
# }

# View extracted pages
curl "http://localhost:8000/documents/1/pages"

# View combined text
curl "http://localhost:8000/documents/1/text"
```

### 4. API Documentation

Interactive docs at: http://localhost:8000/docs

New endpoints in Phase 2:
- `POST /documents/{id}/process` - Process document (OCR, extraction)
- `GET /documents/{id}/pages` - Get extracted pages
- `GET /documents/{id}/text` - Get combined text from all pages

## New API Endpoints

### POST /documents/{id}/process

Process a document with OCR and text extraction.

**Request:**
```
POST /documents/1/process
```

**Response:**
```json
{
  "success": true,
  "message": "Document processed successfully",
  "document_id": 1,
  "pages_extracted": 5,
  "classification": "production_report",
  "tables_detected": 2,
  "processing_method": "PyMuPDF + OCR"
}
```

### GET /documents/{id}/pages

Get all extracted pages for a document.

**Request:**
```
GET /documents/1/pages
```

**Response:**
```json
{
  "document_id": 1,
  "pages": [
    {
      "id": 1,
      "page_number": 1,
      "raw_text": "Production Report 2025-26...",
      "extracted_text": null
    },
    {
      "id": 2,
      "page_number": 2,
      "raw_text": "Coal Production: 125.6 MT...",
      "extracted_text": null
    }
  ],
  "total_pages": 2
}
```

### GET /documents/{id}/text

Get combined text from all pages.

**Request:**
```
GET /documents/1/text
```

**Response:**
```json
{
  "document_id": 1,
  "filename": "report.pdf",
  "status": "processed",
  "text": "Page 1:\nProduction Report 2025-26...\n\n---PAGE BREAK---\n\nPage 2:\nCoal Production: 125.6 MT..."
}
```

## Document Classification

Documents are automatically classified based on content:

- **production_report** - Contains production, output, coal, MT keywords
- **geological_report** - Contains geological, mineral, ore, deposit keywords
- **annual_report** - Contains annual, yearly, fiscal year keywords
- **environmental_report** - Contains environmental, impact, pollution keywords
- **project_report** - Contains project, development, construction keywords
- **administrative_document** - Default if no keywords match

## OCR Engines

### Tesseract
- **Pros:** Fast, lightweight, widely used
- **Cons:** Accuracy depends on language, needs separate installation
- **Best for:** English text, scanned documents

### PaddleOCR
- **Pros:** Multilingual, no language dependency, high accuracy
- **Cons:** Slower, larger model (~50MB download on first use)
- **Best for:** Mixed languages, complex documents

**Priority:** System tries PaddleOCR first (better accuracy), falls back to Tesseract.

## File Size & Performance

- **Max file size:** 100MB (configurable in main.py)
- **PDF processing:** ~1-2 seconds per page (with OCR)
- **OCR processing:** ~2-5 seconds per page depending on image quality
- **Total for 10-page PDF:** ~20-40 seconds

## Troubleshooting

### "ModuleNotFoundError: No module named 'fitz'"
```bash
pip install PyMuPDF
```

### "Tesseract is not installed"
- Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Or set path in processor.py

### "PaddleOCR stuck on first run"
- PaddleOCR downloads ~50MB model on first use
- This is normal, will complete in ~1-2 minutes
- Model is cached for future use

### "PDF processing very slow"
- If using OCR, slow is expected (5+ seconds/page)
- Enable PaddleOCR for better performance than Tesseract

### "No text extracted from image"
- Image quality may be poor
- Try uploading higher resolution image
- Ensure text is not too small

## Database Schema Changes

New table: `document_pages`

```sql
CREATE TABLE document_pages (
    id SERIAL PRIMARY KEY,
    document_id INTEGER FOREIGN KEY,
    page_number INTEGER,
    raw_text TEXT,  -- Text extracted by OCR/parsing
    extracted_text TEXT  -- Will be populated by Phase 3 AI extraction
);
```

## Next: Phase 3

Once Phase 2 is working:

**Phase 3: AI Data Extraction**
- Install local LLM (Ollama or llama.cpp)
- Create extraction schema
- Extract structured fields (production, target, subsidiary, etc.)
- Store in `extracted_records` table
- Add confidence scoring

## Quick Start (Summary)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Tesseract (optional)
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# 3. Start backend
python main.py

# 4. Start frontend (new terminal)
cd ../frontend
npm start

# 5. Upload and process a document
# Open http://localhost:3000
# Documents → Upload → Process
```

## Files Modified

- `main.py` - Added real processing endpoint
- `requirements.txt` - Added OCR libraries
- NEW: `processor.py` - Document processing logic
- NEW: `processing_service.py` - Processing workflow

## What's Working Now

✅ PDF text extraction (digital PDFs)
✅ Scanned PDF OCR
✅ DOCX parsing
✅ XLSX parsing
✅ Image OCR
✅ Document classification
✅ Table detection
✅ Page storage in database
✅ Error handling
✅ Fallback OCR engines

## Performance Notes

- First OCR run downloads models (~50MB for PaddleOCR)
- Subsequent runs are faster (models cached)
- Tesseract is faster but less accurate
- PaddleOCR is slower but more accurate

## Success Criteria for Phase 2

✅ Upload PDF → Text is extracted
✅ Upload image → OCR runs
✅ Upload DOCX → Text is parsed
✅ Upload XLSX → Data is extracted
✅ Pages stored in database
✅ Document classified correctly
✅ Process endpoint returns success
✅ New /pages and /text endpoints work

---

**Phase 2 Status:** Ready for testing
**Next Phase:** Phase 3 - AI Data Extraction
