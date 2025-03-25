from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from .models import CDSR

DEPARTMENT_CHOICES = [
    ('Applied Mechanics', 'Applied Mechanics'),
    ('Automobile Engineering', 'Automobile Engineering'),
    ('Civil Engineering', 'Civil Engineering'),
    ('Computer Technology', 'Computer Technology'),
    ('Dress Design and Garment Manufacturing', 'Dress Design and Garment Manufacturing'),
    ('Electrical Engineering', 'Electrical Engineering'),
    ('Electronics and Telecommunication Engineering', 'Electronics and Telecommunication Engineering'),
    ('Exam Section', 'Exam Section'),
    ('Gymkhana', 'Gymkhana'),
    ('Hostel Boys', 'Hostel Boys'),
    ('Hostel Girls', 'Hostel Girls'),
    ('Information Technology', 'Information Technology'),
    ('Interior Design & Decoration', 'Interior Design & Decoration'),
    ('Library', 'Library'),
    ('Mechanical Engineering', 'Mechanical Engineering'),
    ('Mechatronics engineering', 'Mechatronics engineering'),
    ('Office', 'Office'),
    ('Plastic Engineering', 'Plastic Engineering'),
    ('Science (Chemistry)' , 'Science (Chemistry)'),
    ('Science (Physics)' , 'Science (Physics)'),
    ('Workshop', 'Workshop'),

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