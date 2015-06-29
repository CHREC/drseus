from django import forms
import django_filters
from .models import simics_result, simics_injection, simics_register_diff

target_choices = []
for item in sorted(
        simics_injection.objects.values('target').distinct()):
    target_choices.append((item['target'], item['target']))

target_index_choices = []
for item in sorted(
        simics_injection.objects.values('target_index').distinct()):
    target_index_choices.append(
        (item['target_index'], item['target_index']))

register_choices = []
for item in sorted(
        simics_injection.objects.values('register').distinct()):
    register_choices.append((item['register'], item['register']))

register_index_choices = []
for item in sorted(
        simics_injection.objects.values('register_index').distinct()):
    register_index_choices.append(
        (item['register_index'], item['register_index']))

bit_choices = []
for item in sorted(simics_injection.objects.values('bit').distinct()):
    bit_choices.append((item['bit'], item['bit']))

outcome_choices = []
for item in sorted(simics_result.objects.values('outcome').distinct()):
    outcome_choices.append((item['outcome'], item['outcome']))


class simics_result_filter(django_filters.FilterSet):
    injection__target = django_filters.MultipleChoiceFilter(
        choices=target_choices,
        widget=forms.SelectMultiple(attrs={
            'size': str(len(target_choices)),
            'style': 'width:100%;'
        })
    )
    injection__target_index = django_filters.MultipleChoiceFilter(
        choices=target_index_choices,
        widget=forms.SelectMultiple(attrs={
            'size': str(len(target_index_choices)),
            'style': 'width:100%;'
        })
    )
    injection__register = django_filters.MultipleChoiceFilter(
        choices=register_choices,
        widget=forms.SelectMultiple(attrs={
            'size': str(len(register_choices)),
            'style': 'width:100%;'
        })
    )
    injection__register_index = django_filters.MultipleChoiceFilter(
        choices=register_index_choices,
        widget=forms.SelectMultiple(attrs={
            'size': '10',
            'style': 'width:100%;'
        })
    )
    injection__bit = django_filters.MultipleChoiceFilter(
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
        model = simics_result
        fields = ['injection__target', 'injection__target_index',
                  'injection__register', 'injection__register_index',
                  'injection__bit', 'outcome']

monitored_checkpoint_number_choices = []
for item in sorted(
        simics_register_diff.objects.values(
            'monitored_checkpoint_number').distinct()):
    monitored_checkpoint_number_choices.append(
        (item['monitored_checkpoint_number'],
         item['monitored_checkpoint_number']))

register_diff_choices = []
for item in sorted(
        simics_register_diff.objects.values('register').distinct()):
    register_diff_choices.append((item['register'], item['register']))


class simics_register_diff_filter(django_filters.FilterSet):
    monitored_checkpoint_number = django_filters.MultipleChoiceFilter(
        choices=monitored_checkpoint_number_choices,
        widget=forms.SelectMultiple(attrs={
            'size': str(len(register_diff_choices) if
                        len(register_diff_choices) < 30 else '30'),
            'style': 'width:100%;'
        })
    )

    register = django_filters.MultipleChoiceFilter(
        choices=register_diff_choices,
        widget=forms.SelectMultiple(attrs={
            'size': str(len(register_diff_choices) if
                        len(register_diff_choices) < 30 else '30'),
            'style': 'width:100%;'
        })
    )

    class Meta:
        model = simics_register_diff
        fields = ['monitored_checkpoint_number',  # 'config_object',
                  'register']
