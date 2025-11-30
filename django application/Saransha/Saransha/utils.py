# my_app/utils.py

import os
import pandas as pd
import io
from scholarly import scholarly
from datetime import datetime
import time
from openpyxl import load_workbook
import re
from typing import List, Tuple

import requests


# Scopus API details
SCOPUS_URL = "https://api.elsevier.com/content/serial/title"

# Function to check if a journal is indexed in Scopus and return the updated DataFrame
def check_scopus_index_for_df(df, api_key):
    """
    Takes a DataFrame with a 'Journal' column, checks whether each journal is indexed in Scopus,
    and returns the updated DataFrame with a new 'Scopus Indexed' column.

    Parameters:
    df (pd.DataFrame): Input DataFrame with a 'Journal' column containing journal names.
    api_key (str): Your Scopus API key.

    Returns:
    pd.DataFrame: Updated DataFrame with a 'Scopus Indexed' column.
    """
    SCOPUS_URL = "https://api.elsevier.com/content/serial/title"
    
    # Function to initialize API headers with your API key
    def get_headers():
        return {
            'Accept': 'application/json',
            'X-ELS-APIKey': api_key,
        }
    
    # Function to check if a journal is indexed in Scopus
    def check_scopus_index(journal_name):
        headers = get_headers()
        params = {'title': journal_name}
        response = requests.get(SCOPUS_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('serial-metadata-response'):
                return True  # Journal is indexed
            return False  # Journal not indexed
        else:
            return None  # Error occurred (invalid response)

    # Ensure 'Journal' column exists in the DataFrame
    if 'Journal' not in df.columns:
        raise ValueError("The input DataFrame must have a 'Journal' column.")
    
    # Check Scopus indexing status for each journal and add it as a new column
    df['Scopus Indexed'] = df['Journal'].apply(lambda journal: check_scopus_index(journal))
    
    return df



def load_and_filter_excel(file_path, sheet_name='Sheet1', columns=None, column_name=None, valid_names=None, cited_by_sort_order=None, year_range=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist")

    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        raise Exception(f"Failed to load the Excel file: {str(e)}")

    if columns:
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            print(f"Warning: The following columns are not in the sheet: {', '.join(missing_columns)}")
            columns = [col for col in columns if col in df.columns]
        df = df[columns]

    if column_name and valid_names:
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' does not exist in the DataFrame")
        df = df[df[column_name].isin(valid_names)]

    if cited_by_sort_order:
            if cited_by_sort_order == 'Date':
                if 'Year' not in df.columns:
                    raise ValueError("The column 'Year' does not exist in the DataFrame")
                df = df.sort_values(by='Year', ascending=True)  # Sort by Year in ascending order
            elif cited_by_sort_order in ['asc', 'desc'] and 'Cited by' in df.columns:
                df['Cited by'] = pd.to_numeric(df['Cited by'], errors='coerce').fillna(0).astype(int)
                df = df.sort_values(by='Cited by', ascending=(cited_by_sort_order == 'asc'))
        

    if year_range and len(year_range) == 2:
        if 'Year' in df.columns:
            df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
       
        

    return df

def get_publications_from_profile(profile_url, timeout=30, max_publications=20):
    """
    Extract publications from a Google Scholar profile URL.
    
    Args:
        profile_url: Google Scholar profile URL (e.g., https://scholar.google.com/citations?user=...)
        timeout: Maximum time in seconds to wait for each operation (default: 60)
        max_publications: Maximum number of publications to retrieve (default: 100)
    
    Returns:
        List of publication dictionaries
    
    Raises:
        ValueError: If the profile URL is invalid
        Exception: If unable to retrieve publications
    """
    if not profile_url or not isinstance(profile_url, str):
        raise ValueError("Invalid profile URL provided.")
    
    # Extract user ID from URL
    try:
        if "user=" not in profile_url:
            raise ValueError("Invalid Google Scholar profile URL format. URL must contain 'user=' parameter.")
        user_id = profile_url.split("user=")[1].split("&")[0]
        if not user_id:
            raise ValueError("Could not extract user ID from profile URL.")
    except Exception as e:
        raise ValueError(f"Error parsing profile URL: {str(e)}")
    
    try:
        print(f"Fetching author data for user ID: {user_id}")
        
        # Search for author by ID with timeout handling
        try:
            print(f"  - Searching for author...")
            author = scholarly.search_author_id(user_id)
            if not author:
                raise Exception(f"Author with ID '{user_id}' not found.")
            print(f"  - Author found, fetching details...")
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                raise Exception(f"Google Scholar rate limit reached. Please wait a few minutes and try again.")
            raise Exception(f"Error searching for author: {error_msg}")
        
        # Fill author details with timeout
        try:
            scholarly.fill(author)
            print(f"  - Author details fetched successfully")
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                raise Exception(f"Google Scholar rate limit reached. Please wait a few minutes and try again.")
            raise Exception(f"Error fetching author details: {error_msg}. This may be due to rate limiting or network issues.")
        
        if 'name' not in author:
            raise Exception("Author name not found in profile.")
        
        main_author = author['name']
        current_date = datetime.now().strftime("%Y-%m-%d")
        publications_data = []

        # Check if author has publications
        if 'publications' not in author or not author['publications']:
            print(f"Warning: No publications found for author {main_author}")
            return publications_data

        # Limit the number of publications to process
        publications_to_process = author['publications'][:max_publications]
        print(f"Processing {len(publications_to_process)} publications for {main_author}")

        # Process each publication with error handling
        for idx, pub in enumerate(publications_to_process):
            try:
                # Add small delay to avoid rate limiting
                if idx > 0 and idx % 3 == 0:
                    time.sleep(1)  # Wait 1 second every 3 publications
                
                # Skip filling if it takes too long - use basic data only
                try:
                    scholarly.fill(pub)
                except Exception as fill_error:
                    # If fill fails, use basic data from pub
                    print(f"  - Warning: Could not fetch full details for publication {idx + 1}, using basic data")
                    pass  # Continue with basic data
                
                # Safely extract publication details
                pub_bib = pub.get('bib', {})
                publication_details = {
                    'Main Author': main_author,
                    'Title': pub_bib.get('title', 'N/A'),
                    'conference': pub_bib.get('venue', pub_bib.get('conference', 'N/A')),
                    'Journal': pub_bib.get('journal', 'N/A'),
                    'Year': pub_bib.get('pub_year', 'N/A'),
                    'Publication Type': pub_bib.get('ENTRYTYPE', 'article'),
                    'Cited by': pub.get('num_citations', 0),
                    'co_author': ', '.join(pub_bib.get('author', [])) if isinstance(pub_bib.get('author'), list) else pub_bib.get('author', 'N/A'),
                    'Last Search Date': current_date
                }
                publications_data.append(publication_details)
            except Exception as e:
                print(f"Error processing publication {idx + 1} for {main_author}: {str(e)}")
                continue  # Skip this publication and continue with others

        print(f"Successfully processed {len(publications_data)} publications for {main_author}")
        return publications_data
        
    except TimeoutError as e:
        raise Exception(f"Request timed out while fetching data from Google Scholar: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate limit" in error_msg.lower():
            raise Exception(f"Google Scholar rate limit reached. Please wait a few minutes and try again. Error: {error_msg}")
        elif "timeout" in error_msg.lower():
            raise Exception(f"Request timed out. The Google Scholar service may be slow. Please try again later. Error: {error_msg}")
        else:
            raise Exception(f"Failed to retrieve publications from profile URL '{profile_url}': {error_msg}")

def process_profiles_from_excel(file_path, output_file):
    """
    Process Google Scholar profile URLs from an Excel file and extract publications.
    
    Args:
        file_path: Path to the input Excel file
        output_file: Path to save the output Excel file with publications
    
    Raises:
        ValueError: If required columns are missing
        Exception: If file processing fails
    """
    try:
        profiles_df = pd.read_excel(file_path)
    except Exception as e:
        raise Exception(f"Failed to read Excel file: {str(e)}")
    
    # Validate required column exists
    if 'Profile URL' not in profiles_df.columns:
        raise ValueError("The Excel file must contain a 'Profile URL' column.")
    
    # Filter out empty profile URLs
    profiles_df = profiles_df[profiles_df['Profile URL'].notna()]
    
    if profiles_df.empty:
        raise ValueError("No valid Profile URLs found in the Excel file.")
    
    print(f"Found {len(profiles_df)} profile(s) to process")
    
    all_publications = []
    failed_profiles = []
    total_profiles = len(profiles_df)
    
    # Limit processing for testing (remove this in production or make it configurable)
    MAX_PROFILES_TO_PROCESS = 3  # Process max 3 profiles at a time to avoid long waits
    if total_profiles > MAX_PROFILES_TO_PROCESS:
        print(f"Warning: File contains {total_profiles} profiles. Processing first {MAX_PROFILES_TO_PROCESS} profiles.")
        print("To process all profiles, split your file into smaller batches.")
        profiles_df = profiles_df.head(MAX_PROFILES_TO_PROCESS)
        total_profiles = MAX_PROFILES_TO_PROCESS
    
    print(f"Starting to process {total_profiles} profile(s)...")

    for idx, (row_idx, row) in enumerate(profiles_df.iterrows(), 1):
        profile_url = row['Profile URL']
        if pd.isna(profile_url) or not str(profile_url).strip():
            print(f"Skipping empty profile URL at row {idx}")
            continue
        
        # Add delay between profile requests to avoid rate limiting
        if idx > 1:
            delay = 3  # Wait 3 seconds between profiles
            print(f"Waiting {delay} seconds before processing next profile...")
            time.sleep(delay)
            
        try:
            print(f"\n[{idx}/{total_profiles}] Processing profile: {profile_url}")
            publications = get_publications_from_profile(str(profile_url), timeout=30, max_publications=20)
            
            if publications:
                all_publications.extend(publications)
                print(f"[SUCCESS] Successfully retrieved {len(publications)} publications from {profile_url}")
            else:
                print(f"[WARNING] No publications found for {profile_url}")
                failed_profiles.append({'url': profile_url, 'error': 'No publications found'})
                
        except Exception as e:
            error_msg = f"Could not retrieve publications for {profile_url}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            failed_profiles.append({'url': profile_url, 'error': str(e)})
            # Continue processing other profiles even if one fails

    print(f"\nProcessing complete. Total publications retrieved: {len(all_publications)}")
    
    if not all_publications:
        error_msg = "No publications were retrieved from any profile. "
        if failed_profiles:
            error_msg += f"\nFailed profiles ({len(failed_profiles)}):\n"
            for fp in failed_profiles[:5]:  # Show first 5 errors
                error_msg += f"  - {fp['url']}: {fp['error']}\n"
            if len(failed_profiles) > 5:
                error_msg += f"  ... and {len(failed_profiles) - 5} more\n"
            error_msg += "\nPlease check your Profile URLs and ensure they are valid Google Scholar profile URLs."
        raise Exception(error_msg)
    
    if failed_profiles:
        print(f"Warning: {len(failed_profiles)} profile(s) failed to process, but {len(all_publications)} publications were successfully retrieved.")

    try:
        publications_df = pd.DataFrame(all_publications)
        #API_KEY = 'd93d31bed1f4166cb5cda30e1718ea5c'
        # publications_df = check_scopus_index_for_df(publications_df, API_KEY)
        
        publications_df.to_excel(output_file, index=False)
        print(f"All publication details saved to {output_file}")
        
        if failed_profiles:
            print(f"Warning: {len(failed_profiles)} profile(s) failed to process.")
            
    except Exception as e:
        raise Exception(f"Failed to save publications to Excel file: {str(e)}")


def generate_author_summary(df):
    df.columns = df.columns.str.strip()
    summary = df.groupby('Main Author').agg(
        publication=('Title', 'count'),
        journal=('Journal', lambda x: x.notnull().sum()),
        total_citations=('Cited by', 'sum')
        ).reset_index()
    
    summary = summary.sort_values(by='total_citations', ascending=False)
    
  
    return summary


def generate_publication_summary(dataframe):
    """
    Generate publication summary by year for each author.
    
    Args:
        dataframe: DataFrame with 'Main Author' and 'Year' columns
    
    Returns:
        tuple: (years_list, publications_dict) where years_list is list of year strings
               and publications_dict maps author names to lists of publication counts per year
    """
    # Check required columns
    if 'Main Author' not in dataframe.columns:
        raise ValueError("DataFrame must contain 'Main Author' column")
    
    if 'Year' not in dataframe.columns:
        raise ValueError("DataFrame must contain 'Year' column")
    
    if dataframe.empty:
        return [], {}
    
    # Filter out invalid years and convert to numeric
    df = dataframe.copy()
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df[df['Year'].notna()]
    
    if df.empty:
        return [], {}
    
    # Get valid year range
    min_year = int(df['Year'].min())
    max_year = int(df['Year'].max())
    
    if min_year > max_year:
        return [], {}
    
    # Define the range of years
    years = list(range(min_year, max_year + 1))

    # Get a list of unique authors
    authors = df['Main Author'].dropna().unique()

    if len(authors) == 0:
        return [], {}

    # Create an empty dictionary to store publication counts
    publications = {author: [0] * len(years) for author in authors}

    # Count publications for each author by year
    for _, row in df.iterrows():
        author = row['Main Author']
        year = int(row['Year']) if pd.notna(row['Year']) else None
        
        if year is not None and year in years and author in publications:
            year_index = years.index(year)
            publications[author][year_index] += 1

    # Convert years to strings for the final output
    years_str = list(map(str, years))

    return years_str, publications


def update_publication_details(file_path, author, title, new_journal_name, new_conference_name, new_year):
    # Load the workbook
    try:
        workbook = load_workbook(file_path)
    except Exception:
        return "Failed to load the Excel file."

    # Select the active sheet or specify the sheet name
    sheet = workbook.active  # Or use sheet = workbook['SheetName'] to select a specific sheet
    
    # Loop through rows and columns to access and find the matching row
    for row in sheet.iter_rows():
        if row[0].value == author and row[1].value == title:
            # Modify the values in the found row
            row[2].value = new_journal_name  # Example: Update Journal Name in the 3rd column
            row[3].value = new_conference_name  # Example: Update Conference Name in the 4th column
            row[4].value = new_year  # Example: Update Year in the 5th column (adjust the index if necessary)

            # Save the workbook after modification
            try:
                workbook.save(file_path)  # Save changes to the same file
                return "Update successful."
            except Exception:
                return "Failed to save the Excel file."
    
    # If no matching row was found
    return "Row with the given author and title not found."


def _tokenize(text: str) -> List[str]:
    """Basic tokenizer to normalize text for lightweight relevance scoring."""
    if not text:
        return []
    return re.findall(r"[a-z0-9]+", str(text).lower())


def _row_to_text(row: pd.Series) -> str:
    """Combine relevant publication metadata into a searchable string."""
    abstract = (
        row.get("Abstract")
        or row.get("abstract")
        or row.get("Summary")
        or row.get("Description")
        or ""
    )
    elements = [
        row.get("Title", ""),
        row.get("Main Author", ""),
        row.get("co_author", ""),
        row.get("Journal", ""),
        row.get("conference", ""),
        str(row.get("Year", "")),
        abstract,
    ]
    return " ".join([str(item) for item in elements if pd.notna(item)])


def build_publication_context(
    dataframe: pd.DataFrame,
    query: str,
    top_k: int = 5,
    max_chars: int = 6000,
) -> Tuple[str, List[dict]]:
    """
    Build a context string for RAG by selecting the most relevant publications.

    Args:
        dataframe: Publication dataframe.
        query: Natural language question from the user.
        top_k: Max number of publications to include in context.
        max_chars: Max characters allowed in the final context string.

    Returns:
        Tuple of (context_text, references metadata list).
    """
    if dataframe.empty:
        return "", []

    df = dataframe.fillna("").copy()
    try:
        df["Cited by"] = pd.to_numeric(df.get("Cited by", 0), errors="coerce").fillna(0)
    except Exception:
        df["Cited by"] = 0

    query_tokens = _tokenize(query)
    if not query_tokens:
        query_tokens = []

    df["_search_blob"] = df.apply(_row_to_text, axis=1).str.lower()

    def score_row(blob: str) -> int:
        if not blob or not query_tokens:
            return 0
        return sum(blob.count(token) for token in query_tokens)

    df["_score"] = df["_search_blob"].apply(score_row)
    sort_cols = ["_score", "Cited by"]
    df_sorted = df.sort_values(by=sort_cols, ascending=[False, False])

    if df_sorted["_score"].max() == 0:
        df_sorted = df.sort_values(by="Cited by", ascending=False)

    selected_rows = df_sorted.head(top_k)

    snippets: List[str] = []
    references: List[dict] = []

    for _, row in selected_rows.iterrows():
        abstract = (
            row.get("Abstract")
            or row.get("abstract")
            or row.get("Summary")
            or row.get("Description")
            or "No abstract provided."
        )
        snippet = (
            f"Title: {row.get('Title', 'N/A')}\n"
            f"Year: {row.get('Year', 'N/A')}\n"
            f"Authors: {row.get('co_author', row.get('Main Author', 'N/A'))}\n"
            f"Venue: {row.get('Journal') or row.get('conference') or 'N/A'}\n"
            f"Abstract: {abstract}"
        )
        snippets.append(snippet)
        references.append(
            {
                "title": row.get("Title", "N/A"),
                "year": row.get("Year", "N/A"),
                "main_author": row.get("Main Author", "N/A"),
                "venue": row.get("Journal") or row.get("conference", ""),
            }
        )

    context_text = "\n\n---\n\n".join(snippets)
    if len(context_text) > max_chars:
        context_text = context_text[: max_chars - 3] + "..."

    return context_text, references
