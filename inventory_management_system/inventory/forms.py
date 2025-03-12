from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from .models import CDSR

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
    
class ItemForm(forms.ModelForm):
    class Meta:
        model = CDSR
        fields = "__all__"  # ✅ Sare fields include honge