from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

    
# User Login Form
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
