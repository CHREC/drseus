from django import forms
import django_filters
from .models import simics_results

register_choices = []
for item in sorted(simics_results.objects.values('register').distinct()):
    register_choices.append((item['register'], item['register']))

register_index_choices = []
for item in sorted(simics_results.objects.values('register_index').distinct()):
    register_index_choices.append(
        (item['register_index'], item['register_index']))

bit_choices = []
for item in sorted(simics_results.objects.values('bit').distinct()):
    bit_choices.append((item['bit'], item['bit']))

outcome_choices = []
for item in sorted(simics_results.objects.values('outcome').distinct()):
    outcome_choices.append((item['outcome'], item['outcome']))


class results_filter(django_filters.FilterSet):
    register = django_filters.MultipleChoiceFilter(
        choices=register_choices,
        widget=forms.SelectMultiple(attrs={
            'size': str(len(register_choices)),
            'style': 'width:100%;'
        })
    )
    register_index = django_filters.MultipleChoiceFilter(
        choices=register_index_choices,
        widget=forms.SelectMultiple(attrs={
            'size': '10',
            'style': 'width:100%;'
        })
    )
    bit = django_filters.MultipleChoiceFilter(
        choices=bit_choices,
        widget=forms.SelectMultiple(attrs={
            'size': '10',
            'style': 'width:100%;'
        })
    )
    outcome = django_filters.MultipleChoiceFilter(
        choices=outcome_choices,
        widget=forms.SelectMultiple(attrs={
            'size': str(len(outcome_choices)),
            'style': 'width:100%;'
        })
    )

    class Meta:
        model = simics_results
        fields = ['register', 'register_index', 'bit', 'outcome']
