"""
Context processors to make user information available to all templates
"""
from graph_app.models import Users_Publication


def user_context(request):
    """
    Add user information to template context
    Checks if logged-in user is a faculty member
    """
    context = {
        'is_faculty': False,
        'current_user': None,
    }
    
    # Check if user is logged in via session
    if "user_email" in request.session:
        try:
            user = Users_Publication.objects.get(user_email=request.session["user_email"])
            context['current_user'] = user
            
            # Check if user is a faculty member
            user_category = user.user_category.lower() if user.user_category else ""
            faculty_categories = ['faculty', 'professor', 'associate professor', 'assistant professor']
            context['is_faculty'] = user_category in faculty_categories
        except Users_Publication.DoesNotExist:
            pass
    
    return context
