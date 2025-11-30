# my_app/views.py

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.conf import settings
import pandas as pd
import openpyxl
import io
import os
import json
from datetime import datetime
from openpyxl import Workbook
import requests
from .utils import (
    load_and_filter_excel,
    get_publications_from_profile,
    process_profiles_from_excel,
    generate_author_summary,
    update_publication_details,
    build_publication_context,
)
from graph_app.models import Users_Publication

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_CHAT_MODEL = getattr(settings, "CHAT_WITH_RESEARCHER_MODEL", "gpt-4o-mini")
DEFAULT_CHAT_TOP_K = getattr(settings, "CHAT_WITH_RESEARCHER_TOP_K", 4)
CHAT_SYSTEM_PROMPT = (
    "You are ResearchRadar's 'Chat with the Researcher' assistant. "
    "Answer questions strictly using the publication excerpts that are provided. "
    "If the answer is not present in the supplied context, reply with "
    "'I could not find that in the provided publications.'"
)
#------------------------------------------------------------------------------------------------------------------------------------------
def upload_page(request):
    if "user_email" in request.session:
        excel_data = []
        publications_data = []
        error_message = None
        success_message = None
        
        if request.method == "POST":
            profile_url = request.POST.get('profile_url', '').strip()

            if profile_url:
                try:
                    publications_data = get_publications_from_profile(profile_url, timeout=30, max_publications=20)
                    if publications_data:
                        success_message = f"Successfully retrieved {len(publications_data)} publications from the provided profile URL!"

                        # Save output for downstream pages (optional quality-of-life)
                        try:
                            fs = FileSystemStorage()
                            single_profile_output = fs.path("single_profile_publications.xlsx")
                            pd.DataFrame(publications_data).to_excel(single_profile_output, index=False)
                        except Exception as save_err:
                            print(f"Warning: Could not save single profile output file: {save_err}")
                    else:
                        error_message = "No publications were found for the provided profile URL. Please check that it is a valid Google Scholar profile."
                except Exception as e:
                    error_message = f"Could not fetch publications for the provided profile URL: {str(e)}"

                return render(request, 'auth/upload.html', {
                    'excel_data': excel_data, 
                    'publications_data': publications_data,
                    'error_message': error_message,
                    'success_message': success_message,
                    'profile_url_value': profile_url
                })

            # Check if file was uploaded (fallback to legacy Excel processing)
            if 'excel_file' not in request.FILES:
                error_message = "Please upload an Excel file or provide a Google Scholar profile URL."
                return render(request, 'auth/upload.html', {
                    'excel_data': excel_data, 
                    'publications_data': publications_data,
                    'error_message': error_message,
                    'profile_url_value': profile_url
                })
            
            excel_file = request.FILES['excel_file']
            
            # Validate file extension
            allowed_extensions = ['.xlsx', '.xls', '.bib']
            file_extension = os.path.splitext(excel_file.name)[1].lower()
            if file_extension not in allowed_extensions:
                error_message = f"Invalid file type. Please upload an Excel file (.xlsx, .xls) or BibTeX file (.bib)."
                return render(request, 'auth/upload.html', {
                    'excel_data': excel_data, 
                    'publications_data': publications_data,
                    'error_message': error_message,
                    'profile_url_value': profile_url
                })
            
            try:
                fs = FileSystemStorage()
                filename = fs.save(excel_file.name, excel_file)
                file_path = fs.path(filename)

                # Check if file is BibTeX format
                if file_extension == '.bib':
                    error_message = "BibTeX file support is coming soon. Please upload an Excel file with 'Profile URL' column."
                    return render(request, 'auth/upload.html', {
                        'excel_data': excel_data, 
                        'publications_data': publications_data,
                        'error_message': error_message
                    })

                # Validate Excel file structure
                try:
                    workbook = openpyxl.load_workbook(file_path)
                    worksheet = workbook.active
                    
                    # Check if 'Profile URL' column exists
                    headers = [cell.value for cell in worksheet[1]]
                    if 'Profile URL' not in headers:
                        error_message = "The Excel file must contain a 'Profile URL' column. Please check your file format."
                        return render(request, 'auth/upload.html', {
                            'excel_data': excel_data, 
                            'publications_data': publications_data,
                            'error_message': error_message
                        })
                    
                    # Read excel data for display
                    for row in worksheet.iter_rows():
                        row_data = [cell.value for cell in row]
                        excel_data.append(row_data)
                except Exception as e:
                    error_message = f"Error reading Excel file: {str(e)}. Please ensure the file is a valid Excel file."
                    return render(request, 'auth/upload.html', {
                        'excel_data': excel_data, 
                        'publications_data': publications_data,
                        'error_message': error_message
                    })

                # Process the file
                output_file = fs.path("all_authors_publications.xlsx")
                try:
                    print(f"Starting to process file: {file_path}")
                    print("This may take several minutes depending on the number of profiles...")
                    
                    # Process profiles from Excel
                    process_profiles_from_excel(file_path, output_file)
                    
                    print("Processing completed. Checking output file...")
                    
                    # Check if output file was created successfully
                    if os.path.exists(output_file):
                        try:
                            output_df = pd.read_excel(output_file)
                            if not output_df.empty:
                                publications_data = output_df.to_dict(orient='records')
                                success_message = f"Successfully processed {len(publications_data)} publications from your file!"
                                print(f"Success: {len(publications_data)} publications processed")
                            else:
                                error_message = "No publications were found. Please check your Profile URLs and ensure they are valid Google Scholar profile URLs."
                                print("Warning: Output file is empty")
                        except Exception as e:
                            error_message = f"Error reading output file: {str(e)}"
                            print(f"Error reading output: {str(e)}")
                    else:
                        error_message = "Failed to generate output file. The processing may have encountered an error. Please check the console for details."
                        print("Error: Output file was not created")
                        
                except ValueError as e:
                    # Handle validation errors
                    error_message = f"Validation error: {str(e)}"
                    print(f"Validation error: {str(e)}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                except KeyboardInterrupt:
                    error_message = "Processing was interrupted. Please try again."
                    print("Processing interrupted by user")
                except Exception as e:
                    # Handle other errors - make sure error is displayed
                    error_message = f"Error processing file: {str(e)}"
                    print(f"Error in process_profiles_from_excel: {str(e)}")
                    import traceback
                    full_traceback = traceback.format_exc()
                    print(f"Full traceback: {full_traceback}")
                    
                    # Provide more helpful error messages
                    error_str = str(e).lower()
                    if "rate limit" in error_str or "429" in error_str:
                        error_message = "Google Scholar is rate-limiting requests. Please wait 5-10 minutes and try again with fewer profiles (max 2-3 profiles at a time)."
                    elif "timeout" in error_str or "timed out" in error_str:
                        error_message = "The request timed out. Google Scholar may be slow or blocking requests. Please try again later or use fewer profiles."
                    elif "no publications" in error_str:
                        error_message = f"No publications were retrieved. {str(e)}. Please verify that your Profile URLs are correct and accessible."
                    elif "not found" in error_str:
                        error_message = f"Profile not found. {str(e)}. Please check that your Profile URLs are correct."
                    else:
                        # Show the actual error message
                        error_message = f"Error: {str(e)}. Please check the console for more details."

            except Exception as e:
                error_message = f"An error occurred while uploading the file: {str(e)}"
                import traceback
                print(f"Upload error: {traceback.format_exc()}")

        return render(request, 'auth/upload.html', {
            'excel_data': excel_data, 
            'publications_data': publications_data,
            'error_message': error_message,
            'success_message': success_message,
            'profile_url_value': request.POST.get('profile_url', '') if request.method == "POST" else ""
        })
    else:
        return upload_redirect(request)

def upload_redirect(request):
    context = {'warning_message': "Login required to access this page."}
    return render(request, 'upload.html', context)
   #messages.warning(request, "Login required to access this page.")
   #return render(request, 'upload.html')
#------------------------------------------------------------------------------------------------------------------------------------------

def generatesummary(request):
    authors = []
    result_df = pd.DataFrame()
    summary = pd.DataFrame()
    faculty_member = ""
    start_year = None
    end_year = None
    sort_by = ""
    error_message = None
    
    if "user_email" in request.session:
        if request.method == 'POST':
            faculty_member = request.POST.get('facultySelect', "")
            start_year = request.POST.get('startYear')
            end_year = request.POST.get('endYear')
            sort_by = request.POST.get('sortBy', "")

            try:
                start_year = int(start_year) if start_year else 0
                end_year = int(end_year) if end_year else 0
            except ValueError:
                start_year = 0
                end_year = 2025

        fs = FileSystemStorage()
        output_file_path = fs.path("all_authors_publications.xlsx")

        if not fs.exists(output_file_path):
            error_message = "No data file found. Please upload data first."
            return render(request, "auth/generatesummary.html", {
                'authors': authors,
                'result_df': result_df.to_dict(orient='records'),
                'summary': summary.to_dict(orient='records'),
                'error_message': error_message
            })
        
        try:
            df = pd.read_excel(output_file_path)
            if df.empty:
                error_message = "The data file is empty. Please upload data first."
                return render(request, "auth/generatesummary.html", {
                    'authors': authors,
                    'result_df': result_df.to_dict(orient='records'),
                    'summary': summary.to_dict(orient='records'),
                    'error_message': error_message
                })
            
            if 'Main Author' not in df.columns:
                error_message = "The data file is missing required columns. Please upload a valid file."
                return render(request, "auth/generatesummary.html", {
                    'authors': authors,
                    'result_df': result_df.to_dict(orient='records'),
                    'summary': summary.to_dict(orient='records'),
                    'error_message': error_message
                })
            
            authors = df['Main Author'].dropna().unique().tolist()

            result_df = load_and_filter_excel(
                file_path=output_file_path,
                columns=['Main Author', 'Title', 'Journal', 'conference', 'Publication Type', "Year", "Cited by", "co_author"],
                column_name='Main Author',
                valid_names=[faculty_member] if faculty_member != "All" else authors,
                year_range=[start_year, end_year],
                cited_by_sort_order=sort_by,
            )

            if "downloadSummary" in request.POST:
                if result_df.empty:
                    error_message = "No data matches your filter criteria."
                    return render(request, "auth/generatesummary.html", {
                        'authors': authors,
                        'result_df': result_df.to_dict(orient='records'),
                        'summary': summary.to_dict(orient='records'),
                        'error_message': error_message
                    })
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    result_df.to_excel(writer, index=False, sheet_name='Summary')
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="filtered_summary.xlsx"'
                return response
            
            if "generateSummary" in request.POST:
                if result_df.empty:
                    error_message = "No data matches your filter criteria."
                    return render(request, "auth/generatesummary.html", {
                        'authors': authors,
                        'result_df': result_df.to_dict(orient='records'),
                        'summary': summary.to_dict(orient='records'),
                        'error_message': error_message
                    })
                
                # Save filtered results to output.xlsx for graph generation
                output_file = fs.path("output.xlsx")
                result_df.to_excel(output_file, index=False)
                
                data = generate_author_summary(result_df)
                data0 = data.to_html(classes='table table-striped', index=False)
                data0 = data0.replace('<tr style="text-align: right;">', '<tr style="text-align: left;">')

                data1 = data.to_dict(orient='records')
            
                return render(request, "auth/generatesummary.html", {
                    'authors': authors,
                    'result_df': result_df.to_dict(orient='records'),
                    'summary': summary.to_dict(orient='records'),
                    'data': data0,
                    'data1': data1
                })

        except Exception as e:
            error_message = f"Error processing data: {str(e)}"
            import traceback
            print(f"Error in generatesummary: {traceback.format_exc()}")

        return render(request, "auth/generatesummary.html", {
            'authors': authors,
            'result_df': result_df.to_dict(orient='records'),
            'summary': summary.to_dict(orient='records'),
            'error_message': error_message
        })   
    else:
        return render(request, "generatesummary.html")
#------------------------------------------------------------------------------------------------------------------------------
def home(request):
    if "user_email" in request.session:
        return render(request,'auth/index.html')
    else:
        return render(request,'index.html')

def settings(request):
    if "user_email" in request.session:
         return render(request,'auth/settings.html')
    else:
         return render(request,'settings.html')
   

def help(request):
    if "user_email" in request.session:
         return render(request,'auth/help.html')
    else:
         return render(request,'help.html')

def payment(request):
    if "user_email" in request.session:
         return render(request,'auth/payment.html')
    else:
         return render(request,'payment.html')
        

def login(request):
    if request.method == "POST":
        uemail = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not uemail or not password:
            return render(request, 'login.html', {'error': 'Please provide both email and password.'})
        
        try:
            USER = Users_Publication.objects.filter(user_email=uemail).first()
            if not USER:
                return render(request, 'login.html', {'error': 'Invalid Email or Password'})
            
            # Handle both string and numeric passwords for backward compatibility
            org_pass = str(USER.user_password)
            password_str = str(password)
            
            # Also try numeric comparison for backward compatibility
            try:
                if password_str == org_pass or int(password) == int(org_pass):
                    match = True
                else:
                    match = False
            except (ValueError, TypeError):
                match = (password_str == org_pass)
            
            if match:
                # Set session data
                request.session["user_email"] = uemail
                return render(request, 'auth/index.html', {"m": "Login successful"})
            else:
                return render(request, 'login.html', {'error': 'Invalid credentials. Please enter correct credentials.'})
        except Exception as e:
            return render(request, 'login.html', {'error': f'An error occurred: {str(e)}'})
    else:
        return render(request, 'login.html')



def signup(request):
    if request.method == "POST":
        uname = request.POST.get('username', '').strip()
        uemail = request.POST.get('email', '').strip()
        ucategory = request.POST.get('category', '').strip()
        upassword = request.POST.get('password', '').strip()

        # Validate input
        if not uname or not uemail or not ucategory or not upassword:
            return render(request, 'signup.html', {'error': 'Please fill all fields.'})
        
        # Check if email already exists
        if Users_Publication.objects.filter(user_email=uemail).exists():
            return render(request, 'signup.html', {'error': 'Email already registered. Please use a different email or login.'})
        
        try:
            # Store password as string (not int) for better security and flexibility
            obj = Users_Publication(
                user_name=uname,
                user_email=uemail,
                user_password=upassword,
                user_category=ucategory
            )
            obj.save()
            messages.success(request, "User registered successfully. Please login.")
            return redirect('login')
        except Exception as e:
            return render(request, 'signup.html', {'error': f'Error creating account: {str(e)}'})
    else:
        return render(request, 'signup.html', {'error': 'Please fill the form'})
    
def logo_view(request):
    # Clear the session to log the user out
    request.session.flush()
    return render(request, 'index.html', {"m": "logout successfully"})

  
def cust_view(request):
    if request:
        pass

    return render(request, 'auth/cust.html')

def missVal_view(request):
    authors = []
    filtered_data = []
    selected_author = request.GET.get('author', 'All')  # Default to 'All'
    selected_title = request.GET.get('title', None)  # Selected title
    prefill_data = {}  # Dictionary to hold prefilled values

    # Path to the Excel file
    fs = FileSystemStorage()
    output_file_path = fs.path("all_authors_publications.xlsx")

    try:
        # Check if file exists
        if os.path.exists(output_file_path):
            # Load the Excel file into a DataFrame
            df = pd.read_excel(output_file_path)

        # Ensure the required columns exist in the DataFrame
        if 'Main Author' in df.columns and 'Title' in df.columns:
            authors = df['Main Author'].dropna().unique().tolist()

            # Filter data by author
            if selected_author != 'All':
                titles_df = df[df['Main Author'] == selected_author]
                if 'conference' in df.columns and 'Journal' in df.columns:
                    titles_df = titles_df[titles_df['conference'].isnull() & titles_df['Journal'].isnull()]
                filtered_data = titles_df['Title'].dropna().tolist()

            # Prefill data if a title is selected
            if selected_title:
                row = df[(df['Main Author'] == selected_author) & (df['Title'] == selected_title)]
                if not row.empty:
                    prefill_data = {
                        'journal_name': row.iloc[0].get('Journal', ''),
                        'conference_name': row.iloc[0].get('conference', ''),
                        'year': row.iloc[0].get('Year', '')
                    }
        else:
            print(f"Warning: File {output_file_path} does not exist")

    except Exception as e:
        print(f"Error reading Excel file: {e}")

    # Handle form submission
    if request.method == 'POST':
        
        journal_name = request.POST.get('journalName', 'N/A')
        conference_name = request.POST.get('conferenceName', 'N/A')
        year = request.POST.get('year', 'N/A')
        if selected_author != "N/A" and selected_title != "N/A" and journal_name != "N/A" and conference_name != "N/A" and year != "N/A":
            update_publication_details(output_file_path, selected_author, selected_title, journal_name, conference_name, year)

        print(f"Selected Author: {selected_author}")
        print(f"Title: {selected_title}")
        print(f"Journal Name: {journal_name}")
        print(f"Conference Name: {conference_name}")
        print(f"Year: {year}")
        return render(request, 'auth/missVal.html', {
        'authors': authors,
        'Title': filtered_data,
        'selected_author': selected_author,
        'selected_title': selected_title,
        'prefill_data': prefill_data,
    })

    # Render the template with the required context
    return render(request, 'auth/missVal.html', {
        'authors': authors,
        'Title': filtered_data,
        'selected_author': selected_author,
        'selected_title': selected_title,
        'prefill_data': prefill_data,
    })


def publication_form(request):
    if request.method == 'POST':
        # Get form data
        main_author = request.POST.get('main_author')
        title = request.POST.get('title')
        journal = request.POST.get('journal', '')
        conference = request.POST.get('conference', '')
        year = request.POST.get('year')
        cited_by = request.POST.get('cited_by', 0)
        coauther="N/A"
        Last_Search_Date=datetime.now().strftime("%Y-%m-%d")

        # Path to the Excel file
        fs = FileSystemStorage()
        output_file_path = fs.path("all_authors_publications.xlsx")

        # Check if the file already exists
        if os.path.exists(output_file_path):
            from openpyxl import load_workbook
            workbook = load_workbook(output_file_path)
            sheet = workbook.active
        else:
            # Create a new workbook
            workbook = Workbook()
            sheet = workbook.active
            # Add header row
            sheet.append(["Main Author", "Title", "Journal", "Conference", "Year", "Cited By"])

        # Append data
        sheet.append([main_author, title, journal, conference, year, cited_by])

        # Save the file
        workbook.save(output_file_path)

        return HttpResponse("Publication saved successfully!")

    return render(request, 'publication_form.html')


def _call_chat_completion(query_text, context_text, model_name=DEFAULT_CHAT_MODEL):
    """Call the OpenAI chat completion endpoint."""
    api_key = getattr(settings, "OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI API key is not configured. Set OPENAI_API_KEY in your environment or Django settings.")

    payload = {
        "model": model_name,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {query_text}\n\nAvailable publications:\n{context_text}",
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(OPENAI_CHAT_URL, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Unable to reach OpenAI: {exc}") from exc

    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise RuntimeError("OpenAI response did not include any choices.")

    message = choices[0].get("message", {}).get("content", "").strip()
    if not message:
        raise RuntimeError("OpenAI response was empty.")

    return message


@require_POST
def chat_with_researcher(request):
    """API endpoint that powers the floating chat widget."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    query = payload.get("query", "").strip()
    if not query:
        return JsonResponse({"error": "Query is required."}, status=400)

    top_k = payload.get("top_k") or DEFAULT_CHAT_TOP_K
    try:
        top_k = max(1, int(top_k))
    except (TypeError, ValueError):
        top_k = DEFAULT_CHAT_TOP_K

    fs = FileSystemStorage()
    data_file = fs.path("all_authors_publications.xlsx")

    if not os.path.exists(data_file):
        return JsonResponse(
            {"error": "Publication data not found. Please upload data first."},
            status=404,
        )

    try:
        df = pd.read_excel(data_file)
    except Exception as exc:
        return JsonResponse({"error": f"Unable to read publication data: {exc}"}, status=500)

    if df.empty:
        return JsonResponse(
            {"error": "Publication data is empty. Generate summaries first."},
            status=400,
        )

    context_text, references = build_publication_context(df, query, top_k=top_k)
    if not context_text:
        return JsonResponse(
            {
                "answer": "I could not find that in the provided publications.",
                "citations": [],
            }
        )

    try:
        answer = _call_chat_completion(query, context_text)
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"answer": answer, "citations": references})
