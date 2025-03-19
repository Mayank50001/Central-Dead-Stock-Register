from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from .models import CDSR

DEPARTMENT_CHOICES = [
    
    ('Computer Technology', 'Computer Technology'),
    ('Information Technology', 'Information Technology'),
    ('Civil Engineering', 'Civil Engineering'),
    ('Mechanical Engineering', 'Mechanical Engineering'),
    ('Automobile Engineering', 'Automobile Engineering'),
    ('Plastic Engineering', 'Plastic Engineering'),
    ('Electrical Engineering', 'Electrical Engineering'),
    ('Interior Design & Decoration', 'Interior Design & Decoration'),
    ('Electronics & Telecommunication', 'Electronics & Telecommunication'),
    ('Dress Design & Garment Manu', 'Dress Design & Garment Manu'),
    ('Interior Design & Manu', 'Interior Design & Manu'),
    ('Mechatronics engineering', 'Mechatronics engineering'),
    

    
]

class DepartmentUserCreationForm(forms.ModelForm):
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'department']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # Hash password
        if commit:
            user.save()
        return user

class ItemForm(forms.ModelForm):
    class Meta:
        model = CDSR
        fields = "__all__"
        widgets = {
            'date_of_purchase': forms.DateInput(attrs={'type': 'date', 'class': 'form-control standard-size'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.date_of_purchase:
            self.fields['date_of_purchase'].initial = self.instance.date_of_purchase.strftime('%Y-%m-%d')