# graph_app/views.py
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import matplotlib
matplotlib.use('Agg')
from django.conf import settings
from Saransha.utils import generate_author_summary, generate_publication_summary
from django.core.files.storage import FileSystemStorage


def dynamic_graph(request):
    return render(request, "graph_app/dynamic_graph.html")


def dynamic_graph_view(request):
    """
    Generate dynamic graphs for publication data visualization.
    """
    error_message = None
    graph1 = None
    graph2 = None
    graph3 = None
    
    try:
        fs = FileSystemStorage()
        
        # Try to find the data file
        output_file_path = None
        if fs.exists("output.xlsx"):
            output_file_path = fs.path("output.xlsx")
        elif fs.exists("all_authors_publications.xlsx"):
            output_file_path = fs.path("all_authors_publications.xlsx")
        else:
            error_message = "No data file found. Please upload data or generate a summary first."
            return render(request, 'graph_app/dynamic_graph.html', {
                'error_message': error_message,
                'graph1': graph1,
                'graph2': graph2,
                'graph3': graph3
            })
        
        # Read the data file
        try:
            main = pd.read_excel(output_file_path)
            if main.empty:
                error_message = "The data file is empty. Please upload data first."
                return render(request, 'graph_app/dynamic_graph.html', {
                    'error_message': error_message,
                    'graph1': graph1,
                    'graph2': graph2,
                    'graph3': graph3
                })
        except Exception as e:
            error_message = f"Error reading data file: {str(e)}"
            return render(request, 'graph_app/dynamic_graph.html', {
                'error_message': error_message,
                'graph1': graph1,
                'graph2': graph2,
                'graph3': graph3
            })
        
        # Check required columns
        required_columns = ['Main Author']
        missing_columns = [col for col in required_columns if col not in main.columns]
        if missing_columns:
            error_message = f"Missing required columns in data: {', '.join(missing_columns)}"
            return render(request, 'graph_app/dynamic_graph.html', {
                'error_message': error_message,
                'graph1': graph1,
                'graph2': graph2,
                'graph3': graph3
            })
        
        # Generate summary
        try:
            summary = generate_author_summary(main)
        except Exception as e:
            error_message = f"Error generating summary: {str(e)}"
            return render(request, 'graph_app/dynamic_graph.html', {
                'error_message': error_message,
                'graph1': graph1,
                'graph2': graph2,
                'graph3': graph3
            })
        
        # First Graph: Journal and Conference Count by Author
        try:
            summary1 = summary.drop(columns=["total_citations"])
            df = summary1
            
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            bar_width = 0.35
            index = range(len(df['Main Author']))
            ax1.bar(index, df['journal'], bar_width, label='Journal', color='blue')
            ax1.bar([i + bar_width for i in index], df['publication'], bar_width, label='Conference', color='orange')
            ax1.set_xlabel('Main Author')
            ax1.set_ylabel('Count')
            ax1.set_title('Journal and Conference Count by Author')
            ax1.set_xticks([i + bar_width / 2 for i in index])
            ax1.set_xticklabels(df['Main Author'], rotation=45, ha='right')
            ax1.legend()
            buf1 = io.BytesIO()
            plt.savefig(buf1, format='png', bbox_inches='tight')
            buf1.seek(0)
            graph1 = base64.b64encode(buf1.getvalue()).decode('utf-8')
            buf1.close()
            plt.close(fig1)
        except Exception as e:
            error_message = f"Error creating first graph: {str(e)}"
        
        # Second Graph: Publications by Author Over Time
        try:
            x, y = generate_publication_summary(main)
            years = x
            publications = y
            
            if years and publications:
                fig2, ax2 = plt.subplots(figsize=(12, 6))
                bar_width = 0.25
                index = range(len(years))
                for i, (author, counts) in enumerate(publications.items()):
                    ax2.bar([x + i * bar_width for x in index], counts, bar_width, label=author)
                ax2.set_xlabel('Year')
                ax2.set_ylabel('Number of Publications')
                ax2.set_title('Publications by Author Over Time')
                ax2.set_xticks([x + bar_width for x in index])
                ax2.set_xticklabels(years, rotation=45, ha='right')
                ax2.legend()
                buf2 = io.BytesIO()
                plt.savefig(buf2, format='png', bbox_inches='tight')
                buf2.seek(0)
                graph2 = base64.b64encode(buf2.getvalue()).decode('utf-8')
                buf2.close()
                plt.close(fig2)
        except Exception as e:
            if not error_message:
                error_message = f"Error creating second graph: {str(e)}"
        
        # Third Graph: Publication Count by Author
        try:
            summary2 = summary.drop(columns=["journal", "total_citations"])
            df = summary2
            
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            ax3.bar(df['Main Author'], df['publication'], color='steelblue')
            ax3.set_xlabel('Main Author')
            ax3.set_ylabel('Number of Titles')
            ax3.set_title('Publication Count by Author')
            plt.xticks(rotation=45, ha='right')
            buf3 = io.BytesIO()
            plt.savefig(buf3, format='png', bbox_inches='tight')
            buf3.seek(0)
            image_png = buf3.getvalue()
            buf3.close()
            graph3 = base64.b64encode(image_png).decode('utf-8')
            plt.close(fig3)
        except Exception as e:
            if not error_message:
                error_message = f"Error creating third graph: {str(e)}"
    
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        import traceback
        print(f"Error in dynamic_graph_view: {traceback.format_exc()}")
    
    return render(request, 'graph_app/dynamic_graph.html', {
        'graph1': graph1,
        'graph2': graph2,
        'graph3': graph3,
        'error_message': error_message
    })


@require_POST
def chat_with_researcher(request):
    """
    Handle chat queries about publications.
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        
        # Try to load publications data for context
        fs = FileSystemStorage()
        publications_count = 0
        
        if fs.exists("all_authors_publications.xlsx"):
            try:
                df = pd.read_excel(fs.path("all_authors_publications.xlsx"))
                publications_count = len(df)
            except Exception:
                pass
        
        # Placeholder response - you can integrate with an AI API here
        response_data = {
            'answer': f'You asked: "{query}". I have access to {publications_count} publications. This feature will be enhanced with AI capabilities soon.',
            'citations': []
        }
        
        return JsonResponse(response_data)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)