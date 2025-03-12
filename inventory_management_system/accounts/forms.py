from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


# User Registration Form

class DepartmentUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email' , 'password' , 'department']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # Hash password
        if commit:
            user.save()
        return user
    
# User Login Form
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    