# 📚 Publication Summary Generator for Faculty Profiles

An AI-powered system that automates the extraction, enrichment, and visualization of publication records for faculty profiles. The tool scrapes data from Google Scholar and other academic databases like Scopus and CrossRef, providing customizable outputs in Excel/CSV format along with citation analysis and indexing status.

---

## 🚀 Features

- 🔍 Scrapes and fetches publication data using author profile URLs (Google Scholar, Scopus).
- 📑 Extracts metadata including title, authors, journal, year, citations, and indexing.
- 📊 Provides citation distribution analysis via interactive visualizations.
- 📁 Generates downloadable Excel/CSV reports with selected columns.
- 🔐 Includes login/permission system for secure access.
- 📌 Detects journal/conference indexing (e.g., Scopus) and alerts if data is missing.
- 📈 H-index calculation and customizable filtering (by year, index, author, etc.)

---

## 🛠️ Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap)
- **Backend**: Python, Django
- **Database**: SQLite / PostgreSQL
- **Web Scraping**: Scholarly, Selenium, BeautifulSoup, CrossRef API, Scopus API
- **Visualization**: Matplotlib, Seaborn
- **Others**: Pandas, NumPy, OpenPyXL

---

## 📥 Installation & Setup

### For Windows (PowerShell):
```powershell
# Navigate to the project directory
cd "E:\Publication-Summary-Generator-9\django application\Saransha"

# Create virtual environment (optional, if you want to isolate dependencies)
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# OR if you get execution policy error, use:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirement.txt

# Run migrations (if needed)
python manage.py migrate

# Run the server
python manage.py runserver
```

### Quick Start (Without Virtual Environment):
```powershell
# Navigate to the project directory
cd "E:\Publication-Summary-Generator-9\django application\Saransha"

# Install dependencies (if not already installed)
pip install -r requirement.txt

# Run the server
python manage.py runserver
```

**Note:** If you get an execution policy error when activating venv, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### For Linux/Mac:
```bash
# Navigate to the project directory
cd "django application/Saransha"

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirement.txt

# Run migrations (if needed)
python manage.py migrate

# Run the server
python manage.py runserver
```

---

## 🌐 Access the Application

Once the server is running, open your browser and navigate to:
```
http://localhost:8000
```

---

## 📝 Usage Instructions

1. **Sign Up/Login**: Create an account or login to access the system
2. **Upload Data**: Upload an Excel file (.xlsx or .xls) with a 'Profile URL' column containing Google Scholar profile URLs
3. **Generate Summary**: Filter and generate publication summaries
4. **View Graphs**: Visualize publication data with interactive graphs

---

## ⚠️ Important Notes

- Processing may take several minutes depending on the number of profiles
- Maximum 3 profiles are processed per upload to avoid long waits
- Google Scholar may rate-limit requests - wait 5-10 minutes between large batches
- Ensure Profile URLs are valid Google Scholar profile links
