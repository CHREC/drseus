import re
from django import forms
import django_filters
from .models import (result, injection, simics_register_diff)


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in re.split('([0-9]+)', str(string[0]))])


def injection_choices(attribute):
    choices = []
    for item in sorted(injection.objects.values(attribute).distinct()):
        choices.append((item[attribute], item[attribute]))
    return sorted(choices, key=fix_sort)


def result_choices(attribute):
    choices = []
    for item in sorted(result.objects.values(attribute).distinct()):
        choices.append((item[attribute], item[attribute]))
    return sorted(choices, key=fix_sort)


class hw_result_filter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(hw_result_filter, self).__init__(*args, **kwargs)

        outcome_category_choices = result_choices('outcome_category')
        self.filters['outcome_category'].extra.update(
            choices=outcome_category_choices)
        self.filters['outcome_category'].widget.attrs['size'] = min(
            len(outcome_category_choices), 10)

        outcome_choices = result_choices('outcome')
        self.filters['outcome'].extra.update(choices=outcome_choices)
        self.filters['outcome'].widget.attrs['size'] = min(
            len(outcome_choices), 10)

        core_choices = injection_choices('core')
        self.filters['injection__core'].extra.update(choices=core_choices)
        self.filters['injection__core'].widget.attrs['size'] = min(
            len(core_choices), 10)

        register_choices = injection_choices('register')
        self.filters['injection__register'].extra.update(
            choices=register_choices)
        self.filters['injection__register'].widget.attrs['size'] = min(
            len(register_choices), 10)

        bit_choices = injection_choices('bit')
        self.filters['injection__bit'].extra.update(choices=bit_choices)
        self.filters['injection__bit'].widget.attrs['size'] = min(
            len(bit_choices), 10)

    outcome_category = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    outcome = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__core = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__register = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__bit = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))

    class Meta:
        model = result
        fields = ['injection__core', 'injection__register',
                  'injection__bit', 'outcome']


class hw_injection_filter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(hw_injection_filter, self).__init__(*args, **kwargs)

        outcome_category_choices = result_choices('outcome_category')
        self.filters['result__outcome_category'].extra.update(
            choices=outcome_category_choices)
        self.filters['result__outcome_category'].widget.attrs['size'] = min(
            len(outcome_category_choices), 10)

        outcome_choices = result_choices('outcome')
        self.filters['result__outcome'].extra.update(choices=outcome_choices)
        self.filters['result__outcome'].widget.attrs['size'] = min(
            len(outcome_choices), 10)

        core_choices = injection_choices('core')
        self.filters['core'].extra.update(choices=core_choices)
        self.filters['core'].widget.attrs['size'] = min(len(core_choices), 10)

        register_choices = injection_choices('register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), 10)

        bit_choices = injection_choices('bit')
        self.filters['bit'].extra.update(choices=bit_choices)
        self.filters['bit'].widget.attrs['size'] = min(len(bit_choices), 10)

    result__outcome_category = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    result__outcome = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    core = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    register = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    bit = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))

    class Meta:
        model = result
        fields = ['result__outcome_category', 'result__outcome', 'core',
                  'register', 'bit']


class simics_result_filter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(simics_result_filter, self).__init__(*args, **kwargs)

        outcome_category_choices = result_choices('outcome_category')
        self.filters['outcome_category'].extra.update(
            choices=outcome_category_choices)
        self.filters['outcome_category'].widget.attrs['size'] = min(
            len(outcome_category_choices), 10)

        outcome_choices = result_choices('outcome')
        self.filters['outcome'].extra.update(choices=outcome_choices)
        self.filters['outcome'].widget.attrs['size'] = min(
            len(outcome_choices), 10)

        target_choices = injection_choices('target')
        self.filters['injection__target'].extra.update(
            choices=target_choices)
        self.filters['injection__target'].widget.attrs['size'] = min(
            len(target_choices), 10)

        target_index_choices = injection_choices('target_index')
        self.filters['injection__target_index'].extra.update(
            choices=target_index_choices)
        self.filters['injection__target_index'].widget.attrs['size'] = min(
            len(target_index_choices), 10)

        register_choices = injection_choices('register')
        self.filters['injection__register'].extra.update(
            choices=register_choices)
        self.filters['injection__register'].widget.attrs['size'] = min(
            len(register_choices), 10)

        register_index_choices = injection_choices('register_index')
        self.filters['injection__register_index'].extra.update(
            choices=register_index_choices)
        self.filters['injection__register_index'].widget.attrs['size'] = min(
            len(register_index_choices), 10)

        bit_choices = injection_choices('bit')
        self.filters['injection__bit'].extra.update(choices=bit_choices)
        self.filters['injection__bit'].widget.attrs['size'] = min(
            len(bit_choices), 10)

        checkpoint_number_choices = injection_choices('checkpoint_number')
        self.filters['injection__checkpoint_number'].extra.update(
            choices=checkpoint_number_choices)
        self.filters['injection__checkpoint_number'].widget.attrs['size'] = min(
            len(checkpoint_number_choices), 10)

    outcome_category = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    outcome = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__target = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__target_index = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__register = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__register_index = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__bit = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    injection__checkpoint_number = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))

    class Meta:
        model = result
        exclude = ['iteration', 'dut_output', 'aux_output', 'debugger_output',
                   'paramiko_output', 'aux_paramiko_output', 'data_diff',
                   'detected_errors']


class simics_injection_filter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(simics_injection_filter, self).__init__(*args, **kwargs)

        outcome_category_choices = result_choices('outcome_category')
        self.filters['result__outcome_category'].extra.update(
            choices=outcome_category_choices)
        self.filters['result__outcome_category'].widget.attrs['size'] = min(
            len(outcome_category_choices), 10)

        outcome_choices = result_choices('outcome')
        self.filters['result__outcome'].extra.update(choices=outcome_choices)
        self.filters['result__outcome'].widget.attrs['size'] = min(
            len(outcome_choices), 10)

        target_choices = injection_choices('target')
        self.filters['target'].extra.update(choices=target_choices)
        self.filters['target'].widget.attrs['size'] = min(
            len(target_choices), 10)

        target_index_choices = injection_choices('target_index')
        self.filters['target_index'].extra.update(choices=target_index_choices)
        self.filters['target_index'].widget.attrs['size'] = min(
            len(target_index_choices), 10)

        register_choices = injection_choices('register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), 10)

        register_index_choices = injection_choices('register_index')
        self.filters['register_index'].extra.update(
            choices=register_index_choices)
        self.filters['register_index'].widget.attrs['size'] = min(
            len(register_index_choices), 10)

        bit_choices = injection_choices('bit')
        self.filters['bit'].extra.update(choices=bit_choices)
        self.filters['bit'].widget.attrs['size'] = min(len(bit_choices), 10)

        checkpoint_number_choices = injection_choices('checkpoint_number')
        self.filters['checkpoint_number'].extra.update(
            choices=checkpoint_number_choices)
        self.filters['checkpoint_number'].widget.attrs['size'] = min(
            len(checkpoint_number_choices), 10)

    result__outcome_category = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    result__outcome = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    target = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    target_index = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    register = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    register_index = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    bit = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))
    checkpoint_number = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))

    class Meta:
        model = injection
        exclude = ['result', 'injection_number', 'gold_value', 'injected_value',
                   'checkpoint_number', 'config_object', 'config_type', 'field',
                   'time', 'time_rounded', 'core']


class simics_register_diff_filter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(simics_register_diff_filter, self).__init__(*args, **kwargs)
        self.queryset = kwargs['queryset']
        checkpoint_number_choices = self.simics_register_diff_choices(
            'checkpoint_number')
        self.filters['checkpoint_number'].extra.update(
            choices=checkpoint_number_choices)
        self.filters['checkpoint_number'].widget.attrs['size'] = min(
            len(checkpoint_number_choices), 10)
        register_choices = self.simics_register_diff_choices('register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), 30)

    def simics_register_diff_choices(self, attribute):
        choices = []
        for item in sorted(
                self.queryset.values(attribute).distinct()):
            choices.append((item[attribute], item[attribute]))
        return sorted(choices, key=fix_sort)

    checkpoint_number = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))

    register = django_filters.MultipleChoiceFilter(
        widget=forms.SelectMultiple(attrs={'style': 'width:100%;'}))

    class Meta:
        model = simics_register_diff
        fields = ['checkpoint_number', 'register']
