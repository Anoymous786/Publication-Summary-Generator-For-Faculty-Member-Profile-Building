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

```bash
# Clone the repository
git clone https://github.com/yourusername/publication-summary-generator.git
cd publication-summary-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python manage.py runserver
