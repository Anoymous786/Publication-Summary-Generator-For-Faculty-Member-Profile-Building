from django import forms
from .models import FacultyProfile


class FacultyProfileForm(forms.ModelForm):
    """Form for faculty profile management"""
    
    class Meta:
        model = FacultyProfile
        fields = [
            'full_name',
            'designation',
            'department',
            'bio',
            'phone',
            'office_location',
            'research_interests',
            'google_scholar_id',
            'orcid_id',
            'profile_picture'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Professor, Associate Professor'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your department'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write a brief biography about yourself'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'office_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your office location'
            }),
            'research_interests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your research interests (comma-separated)'
            }),
            'google_scholar_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your Google Scholar ID or profile URL'
            }),
            'orcid_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your ORCID ID'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field in self.fields:
            self.fields[field].required = False
