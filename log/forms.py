from django import forms
from .filters import result_choices


class result_form(forms.Form):
    outcome = forms.CharField(required=False)
    outcome_category = forms.CharField(required=False)


class edit_form(forms.Form):
    def __init__(self, *args, **kwargs):
        campaign = kwargs['campaign']
        del kwargs['campaign']
        super(edit_form, self).__init__(*args, **kwargs)
        outcome_choices = result_choices(campaign, 'outcome')
        self.fields['outcome'].choices = outcome_choices
        outcome_category_choices = result_choices(campaign, 'outcome_category')
        self.fields['outcome_category'].choices = outcome_category_choices

    new_outcome = forms.CharField(required=False)
    new_outcome_category = forms.CharField(required=False)
    outcome = forms.ChoiceField()
    outcome_category = forms.ChoiceField()
