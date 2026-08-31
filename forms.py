from django import forms
# from .models import Investor

# class InvestorForm(forms.ModelForm):
    class Meta:
#         model = Investor
        fields = ['name', 'phone', 'wallet_address']
