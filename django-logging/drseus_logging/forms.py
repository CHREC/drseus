from django import forms


class result_form(forms.Form):
    outcome = forms.CharField(required=False)
    outcome_category = forms.CharField(required=False)
