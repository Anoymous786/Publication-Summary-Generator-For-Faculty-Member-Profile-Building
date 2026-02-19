# Saransha/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
import pandas as pd
import openpyxl
import os
import io
from datetime import datetime

from .utils import (
    load_and_filter_excel,
    get_publications_from_profile,
    get_publications_safe,
    process_profiles_from_excel,
    generate_author_summary,
    update_publication_details
)

from graph_app.models import Users_Publication


# =====================================================
# UPLOAD PAGE (EXCEL OR GOOGLE SCHOLAR URL)
# =====================================================

def upload_page(request):
    if "user_email" not in request.session:
        return redirect("login")

    excel_data = []
    publications_data = []
    error_message = None
    success_message = None
    profile_url_value = ""

    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")
        profile_url = request.POST.get("profile_url", "").strip()
        profile_url_value = profile_url

        # Neither provided
        if not excel_file and not profile_url:
            error_message = "Please upload an Excel file OR paste a Google Scholar profile URL."
            return render(request, "auth/upload.html", locals())

        fs = FileSystemStorage()

        # =================================================
        # CASE 1: GOOGLE SCHOLAR URL ONLY
        # =================================================
        if profile_url and not excel_file:
            try:
                print(f"[INFO] Processing single profile URL: {profile_url}")
                publications = get_publications_from_profile(profile_url, timeout=30, max_publications=100)

                if not publications:
                    error_message = "No publications found. Please check the Google Scholar profile URL."
                else:
                    publications_data = publications
                    success_message = f"Fetched {len(publications)} publications from Google Scholar."
                    
                    # Save to file for later use
                    output_file = fs.path("all_authors_publications.xlsx")
                    pd.DataFrame(publications).to_excel(output_file, index=False)
                    print(f"[SUCCESS] Saved to {output_file}")

                return render(request, "auth/upload.html", locals())

            except Exception as e:
                error_message = f"Error fetching Google Scholar data: {str(e)}"
                print(f"[ERROR] {error_message}")
                return render(request, "auth/upload.html", locals())

        # =================================================
        # CASE 2: EXCEL FILE UPLOAD
        # =================================================
        if excel_file:
            ext = os.path.splitext(excel_file.name)[1].lower()
            if ext not in [".xlsx", ".xls"]:
                error_message = "Invalid file type. Please upload an Excel file (.xlsx or .xls)."
                return render(request, "auth/upload.html", locals())

            filename = fs.save(excel_file.name, excel_file)
            file_path = fs.path(filename)

            # Validate Excel structure
            try:
                wb = openpyxl.load_workbook(file_path)
                ws = wb.active
                headers = [cell.value for cell in ws[1]]

                if "Profile URL" not in headers:
                    error_message = "Excel file must contain a 'Profile URL' column."
                    return render(request, "auth/upload.html", locals())

            except Exception as e:
                error_message = f"Invalid Excel file: {str(e)}"
                return render(request, "auth/upload.html", locals())

            # Process Excel
            try:
                output_file = fs.path("all_authors_publications.xlsx")
                process_profiles_from_excel(file_path, output_file)

                if not os.path.exists(output_file):
                    error_message = "Failed to generate output file."
                    return render(request, "auth/upload.html", locals())

                df = pd.read_excel(output_file)
                if df.empty:
                    error_message = "No publications found. Check Profile URLs."
                else:
                    publications_data = df.to_dict(orient="records")
                    success_message = f"Successfully processed {len(publications_data)} publications."

            except Exception as e:
                error_message = str(e)

    return render(request, "auth/upload.html", locals())


# =====================================================
# GENERATE SUMMARY
# =====================================================

def generatesummary(request):
    if "user_email" not in request.session:
        return redirect("login")

    fs = FileSystemStorage()
    output_file_path = fs.path("all_authors_publications.xlsx")

    authors = []
    result_df = pd.DataFrame()
    summary = pd.DataFrame()
    data = ""
    error_message = None

    if not os.path.exists(output_file_path):
        error_message = "Please upload publication data first."
        return render(request, "auth/generatesummary.html", locals())

    try:
        df = pd.read_excel(output_file_path)
        if df.empty or "Main Author" not in df.columns:
            error_message = "Invalid data file. Please upload data again."
            return render(request, "auth/generatesummary.html", locals())

        authors = df["Main Author"].dropna().unique().tolist()
        
        # Show data table by default
        data = df.to_html(classes='table table-striped table-hover', index=False)

    except Exception as e:
        error_message = f"Error reading data file: {str(e)}"
        return render(request, "auth/generatesummary.html", locals())

    if request.method == "POST":
        faculty = request.POST.get("facultySelect", "All")
        start_year = int(request.POST.get("startYear", 0) or 0)
        end_year = int(request.POST.get("endYear", 9999) or 9999)
        sort_by = request.POST.get("sortBy", "")

        try:
            result_df = load_and_filter_excel(
                file_path=output_file_path,
                columns=[
                    "Main Author", "Title", "Journal", "conference",
                    "Publication Type", "Year", "Cited by", "co_author"
                ],
                column_name="Main Author",
                valid_names=authors if faculty == "All" else [faculty],
                year_range=[start_year, end_year],
                cited_by_sort_order=sort_by
            )
            
            if not result_df.empty:
                data = result_df.to_html(classes='table table-striped table-hover', index=False)

        except Exception as e:
            error_message = f"Error filtering data: {str(e)}"

        if "downloadSummary" in request.POST:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                result_df.to_excel(writer, index=False)
            buffer.seek(0)

            response = HttpResponse(
                buffer,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="filtered_summary.xlsx"'
            return response

        if "generateSummary" in request.POST and not result_df.empty:
            try:
                summary = generate_author_summary(result_df)
                data = summary.to_html(classes='table table-striped table-hover', index=False)
            except Exception as e:
                error_message = f"Error generating summary: {str(e)}"

    return render(request, "auth/generatesummary.html", locals())


# =====================================================
# AUTH PAGES
# =====================================================

def home(request):
    return render(request, "auth/index.html" if "user_email" in request.session else "index.html")


def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = Users_Publication.objects.filter(user_email=email).first()
        if user and str(user.user_password) == str(password):
            request.session["user_email"] = email
            return redirect("home")

        return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


def signup(request):
    if request.method == "POST":
        Users_Publication.objects.create(
            user_name=request.POST["username"],
            user_email=request.POST["email"],
            user_password=request.POST["password"],
            user_category=request.POST["category"]
        )
        return redirect("login")

    return render(request, "signup.html")


def logo_view(request):
    request.session.flush()
    return redirect("home")


# =====================================================
# STATIC PAGES
# =====================================================

def settings(request):
    return render(request, 'settings.html')


def help(request):
    return render(request, 'help.html')


def payment(request):
    if "user_email" not in request.session:
        return redirect("login")
    return render(request, 'payment.html')


# =====================================================
# CUST VIEW - Add New Records
# =====================================================

def cust_view(request):
    if "user_email" not in request.session:
        return redirect("login")
    
    success_message = None
    error_message = None
    
    if request.method == "POST":
        try:
            fs = FileSystemStorage()
            output_file = fs.path("all_authors_publications.xlsx")
            
            # Get form data
            main_author = request.POST.get("main_author", "").strip()
            title = request.POST.get("title", "").strip()
            journal = request.POST.get("journal", "").strip() or "N/A"
            conference = request.POST.get("conference", "").strip() or "N/A"
            year = request.POST.get("year", "")
            cited_by = request.POST.get("cited_by", "0")
            
            if not main_author or not title:
                error_message = "Author name and title are required."
            else:
                # Create new record
                new_record = {
                    'Main Author': main_author,
                    'Title': title,
                    'Journal': journal,
                    'conference': conference,
                    'Year': int(year) if year else None,
                    'Publication Type': 'article',
                    'Cited by': int(cited_by) if cited_by else 0,
                    'co_author': main_author,
                    'Last Search Date': datetime.now().strftime("%Y-%m-%d")
                }
                
                # Load existing or create new
                if os.path.exists(output_file):
                    df = pd.read_excel(output_file)
                    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                else:
                    df = pd.DataFrame([new_record])
                
                df.to_excel(output_file, index=False)
                success_message = f"Successfully added publication: {title}"
                
        except Exception as e:
            error_message = f"Error adding record: {str(e)}"
    
    return render(request, 'cust.html', {
        'success_message': success_message,
        'error_message': error_message
    })


# =====================================================
# MISSVAL VIEW - Edit Missing Values
# =====================================================

def missVal_view(request):
    if "user_email" not in request.session:
        return redirect("login")
    
    fs = FileSystemStorage()
    output_file = fs.path("all_authors_publications.xlsx")
    
    authors = []
    Title = []
    selected_author = request.GET.get('author', 'All')
    selected_title = request.GET.get('title', None)
    prefill_data = {'journal_name': '', 'conference_name': '', 'year': ''}
    success_message = None
    error_message = None
    
    # Load data if exists
    if os.path.exists(output_file):
        try:
            df = pd.read_excel(output_file)
            authors = df['Main Author'].dropna().unique().tolist()
            
            # Filter titles by selected author
            if selected_author and selected_author != 'All':
                filtered_df = df[df['Main Author'] == selected_author]
                Title = filtered_df['Title'].dropna().unique().tolist()
            else:
                Title = df['Title'].dropna().unique().tolist()
            
            # Prefill data for selected title
            if selected_title and selected_title != 'None':
                title_row = df[df['Title'] == selected_title]
                if not title_row.empty:
                    row = title_row.iloc[0]
                    prefill_data = {
                        'journal_name': row.get('Journal', '') if row.get('Journal') != 'N/A' else '',
                        'conference_name': row.get('conference', '') if row.get('conference') != 'N/A' else '',
                        'year': str(int(row.get('Year'))) if pd.notna(row.get('Year')) else ''
                    }
                    
        except Exception as e:
            error_message = f"Error loading data: {str(e)}"
    
    # Handle form submission
    if request.method == "POST":
        try:
            journal_name = request.POST.get('journalName', '').strip()
            conference_name = request.POST.get('conferenceName', '').strip()
            year = request.POST.get('year', '').strip()
            
            if selected_title and selected_title != 'None' and os.path.exists(output_file):
                df = pd.read_excel(output_file)
                
                # Update the record
                mask = df['Title'] == selected_title
                if journal_name:
                    df.loc[mask, 'Journal'] = journal_name
                if conference_name:
                    df.loc[mask, 'conference'] = conference_name
                if year:
                    df.loc[mask, 'Year'] = int(year)
                
                df.to_excel(output_file, index=False)
                success_message = f"Successfully updated: {selected_title}"
            else:
                error_message = "Please select a title to update."
                
        except Exception as e:
            error_message = f"Error updating record: {str(e)}"
    
    return render(request, 'missVal.html', {
        'authors': authors,
        'Title': Title,
        'selected_author': selected_author,
        'selected_title': selected_title,
        'prefill_data': prefill_data,
        'success_message': success_message,
        'error_message': error_message
    })


# =====================================================
# UPLOAD REDIRECT
# =====================================================

def upload_redirect(request):
    if "user_email" not in request.session:
        return redirect("login")
    return redirect("upload")