# MineSync AI - Quick Start Guide

## 30-Second Setup

### 1. Ensure PostgreSQL is Running
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT 1"
```

If it fails, start PostgreSQL (varies by OS).

### 2. Start Backend (Terminal 1)
```bash
cd backend
source venv/Scripts/activate  # Windows: venv\Scripts\activate
python main.py
```

**Expected output:**
```
✓ MineSync AI backend started
```

Backend ready at: http://localhost:8000/docs

### 3. Start Frontend (Terminal 2)
```bash
cd frontend
npm start
```

**Expected output:**
```
Compiled successfully!
App running at http://localhost:3000
```

## Test It (2 minutes)

1. **Upload a document:**
   - Click "Documents" in the sidebar
   - Select document type from dropdown
   - Click the upload area and choose any PDF/DOCX/image
   - Click "Upload Document"
   - ✓ Document appears in the table

2. **Check dashboard:**
   - Click "Dashboard"
   - ✓ See document count increased by 1

3. **Explore the API:**
   - Open http://localhost:8000/docs
   - ✓ Try the "GET /documents" endpoint

## What's Ready to Use

| Feature | Status | Location |
|---------|--------|----------|
| Document Upload | ✅ Working | Documents page |
| Dashboard | ✅ Working | Dashboard page |
| API Endpoints | ✅ 9 working | http://localhost:8000/docs |
| Database | ✅ Connected | PostgreSQL local |
| UI Navigation | ✅ Working | Sidebar |

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "Cannot connect to database" | Ensure PostgreSQL is running |
| "Backend not responding" | Restart: `python main.py` |
| "Port 8000 already in use" | Kill process: `lsof -i :8000` or change BACKEND_PORT in .env |
| "npm: command not found" | Install Node.js from nodejs.org |
| "psycopg2 error" | Run: `pip install -r requirements.txt` again |

## Next: Phase 2

When ready to continue:
```bash
# Phase 2: OCR & Document Processing
# See PHASE_1_COMPLETE.md for detailed roadmap
```

## Files to Know

- `README.md` - Full documentation
- `PHASE_1_COMPLETE.md` - Phase 1 summary and next steps
- `backend/main.py` - Backend API
- `frontend/src/App.js` - Frontend entry point
- `backend/.env` - Configuration

## Need Help?

1. Check backend terminal for errors
2. Check browser console (F12) for frontend errors
3. Test API directly: http://localhost:8000/docs
4. Review README.md for detailed setup

---

**Everything working?** Great! You're ready for Phase 2 (OCR & Document Processing).

**Something broken?** Check the terminal output or README.md Troubleshooting section.
