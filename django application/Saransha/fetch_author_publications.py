#!/usr/bin/env python
"""
Script to fetch and display publication data for a specific Google Scholar profile
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Saransha.settings')
django.setup()

from Saransha.utils import get_publications_from_profile
import pandas as pd

def fetch_and_display_publications(profile_url, author_name=None):
    """
    Fetch publications from a Google Scholar profile and display in table format
    """
    print(f"\n{'='*80}")
    print(f"Fetching publications for: {author_name or 'Author'}")
    print(f"Profile URL: {profile_url}")
    print(f"{'='*80}\n")
    
    try:
        # Fetch publications (increase max_publications to get more)
        publications = get_publications_from_profile(
            profile_url, 
            timeout=30, 
            max_publications=100  # Get more publications
        )
        
        if not publications:
            print("No publications found for this profile.")
            return
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(publications)
        
        # Display the data
        print(f"\n{'='*80}")
        print(f"Total Publications Found: {len(publications)}")
        print(f"{'='*80}\n")
        
        # Display in table format
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        print(df.to_string(index=False))
        
        # Save to Excel file
        output_file = f"{author_name.replace(' ', '_')}_publications.xlsx" if author_name else "publications.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\n{'='*80}")
        print(f"Data saved to: {output_file}")
        print(f"{'='*80}\n")
        
        return df
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Profile URL for SUSHEELAMMA K H
    profile_url = "https://scholar.google.co.in/citations?hl=en&user=7XFtoVkAAAAJ"
    author_name = "SUSHEELAMMA K H"
    
    fetch_and_display_publications(profile_url, author_name)









