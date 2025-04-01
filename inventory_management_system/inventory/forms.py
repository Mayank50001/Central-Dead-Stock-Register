from django import forms
from .models import CDSR

# Register Choices
REGISTER_CHOICES = [
    ('C/S DSR/M&E', 'C/S DSR/M&E'),
    ('C/S DSR/Furniture', 'C/S DSR/Furniture'),
    ('C/S DSR/CC/Furniture', 'C/S DSR/CC/Furniture'),
    ('C/S DSR/UPSBTY/SCR', 'C/S DSR/UPSBTY/SCR'),
    ('C/S DSR/Semi C R', 'C/S DSR/Semi C R'),
    ('C/S DSR/M&E/World Bank', 'C/S DSR/M&E/World Bank'),
    ('C/S DSR/CC', 'C/S DSR/CC'),
    ('C/S DSR/PRU/WB', 'C/S DSR/PRU/WB'),
]



class ItemForm(forms.ModelForm):
    class Meta:
        model = CDSR
        fields = '__all__'
        widgets = {
            'date_of_purchase': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.date_of_purchase:
            self.fields['date_of_purchase'].initial = self.instance.date_of_purchase.strftime('%Y-%m-%d')
        
        # Get all unique register names from the database
        register_names = CDSR.objects.values_list('cdsr_name', flat=True).distinct()
        register_choices = [(name, name) for name in register_names if name]
        
        # Initialize cdsr_name field with choices
        self.fields['cdsr_name'] = forms.ChoiceField(
            choices=[('', 'Select Register')] + register_choices,
            widget=forms.Select(attrs={'class': 'form-control'})
        )