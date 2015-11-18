from django.forms import SelectMultiple, Textarea
import django_filters
from re import split

from .models import (injection, result, simics_register_diff)


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in split('([0-9]+)', str(string))])


def fix_sort_list(list):
    return fix_sort(list[0])


def injection_choices(campaign, attribute):
    choices = []
    for item in sorted(injection.objects.filter(
            result__campaign_id=campaign).values(attribute).distinct()):
        choices.append((item[attribute], item[attribute]))
    return sorted(choices, key=fix_sort_list)


def result_choices(campaign, attribute):
    choices = []
    for item in sorted(result.objects.filter(
            campaign_id=campaign).values(attribute).distinct()):
        choices.append((item[attribute], item[attribute]))
    return sorted(choices, key=fix_sort_list)


class injection_filter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        campaign = kwargs['campaign']
        del kwargs['campaign']
        super(injection_filter, self).__init__(*args, **kwargs)
        bit_choices = injection_choices(campaign, 'bit')
        self.filters['bit'].extra.update(choices=bit_choices)
        self.filters['bit'].widget.attrs['size'] = min(len(bit_choices), 10)
        checkpoint_number_choices = injection_choices(
            campaign, 'checkpoint_number')
        self.filters['checkpoint_number'].extra.update(
            choices=checkpoint_number_choices)
        self.filters['checkpoint_number'].widget.attrs['size'] = min(
            len(checkpoint_number_choices), 10)
        core_choices = injection_choices(campaign, 'core')
        self.filters['core'].extra.update(choices=core_choices)
        self.filters['core'].widget.attrs['size'] = min(len(core_choices), 10)
        field_choices = injection_choices(campaign, 'field')
        self.filters['field'].extra.update(choices=field_choices)
        self.filters['field'].widget.attrs['size'] = min(len(field_choices), 10)
        num_injections_choices = result_choices(campaign, 'num_injections')
        self.filters['result__num_injections'].extra.update(
            choices=num_injections_choices)
        self.filters['result__num_injections'].widget.attrs['size'] = min(
            len(num_injections_choices), 10)
        outcome_choices = result_choices(campaign, 'outcome')
        self.filters['result__outcome'].extra.update(choices=outcome_choices)
        self.filters['result__outcome'].widget.attrs['size'] = min(
            len(outcome_choices), 10)
        outcome_category_choices = result_choices(campaign, 'outcome_category')
        self.filters['result__outcome_category'].extra.update(
            choices=outcome_category_choices)
        self.filters['result__outcome_category'].widget.attrs['size'] = min(
            len(outcome_category_choices), 10)
        register_choices = injection_choices(campaign, 'register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), 10)
        register_index_choices = injection_choices(campaign, 'register_index')
        self.filters['register_index'].extra.update(
            choices=register_index_choices)
        self.filters['register_index'].widget.attrs['size'] = min(
            len(register_index_choices), 10)
        target_choices = injection_choices(campaign, 'target')
        self.filters['target'].extra.update(choices=target_choices)
        self.filters['target'].widget.attrs['size'] = min(
            len(target_choices), 10)
        target_index_choices = injection_choices(campaign, 'target_index')
        self.filters['target_index'].extra.update(choices=target_index_choices)
        self.filters['target_index'].widget.attrs['size'] = min(
            len(target_index_choices), 10)
        # time_rounded_choices = injection_choices(campaign, 'time_rounded')
        # self.filters['time_rounded'].extra.update(choices=time_rounded_choices)
        # self.filters['time_rounded'].widget.attrs['size'] = min(
        #     len(time_rounded_choices), 10)

    result__aux_output = django_filters.CharFilter(
        label='AUX output',
        lookup_type='icontains',
        widget=Textarea(attrs={'cols': 16, 'rows': 3, 'type': 'search'}),
        help_text='')
    result__debugger_output = django_filters.CharFilter(
        label='Debugger output',
        lookup_type='icontains',
        widget=Textarea(attrs={'cols': 16, 'rows': 3, 'type': 'search'}),
        help_text='')
    result__dut_output = django_filters.CharFilter(
        label='DUT output',
        lookup_type='icontains',
        widget=Textarea(attrs={'cols': 16, 'rows': 3, 'type': 'search'}),
        help_text='')
    result__paramiko_output = django_filters.CharFilter(
        label='SCP output',
        lookup_type='icontains',
        widget=Textarea(attrs={'cols': 16, 'rows': 3, 'type': 'search'}),
        help_text='')
    bit = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    core = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    checkpoint_number = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    field = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    register = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    register_index = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    result__num_injections = django_filters.MultipleChoiceFilter(
        label='Number of injections',
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    result__outcome = django_filters.MultipleChoiceFilter(
        label='Outcome',
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    result__outcome_category = django_filters.MultipleChoiceFilter(
        label='Outcome category',
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    target = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    target_index = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    # time_rounded = django_filters.MultipleChoiceFilter(
    #     widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')

    class Meta:
        model = injection
        exclude = ['config_object', 'config_type', 'gold_value',
                   'injected_value', 'injection_number', 'result', 'time',
                   'timestamp']


class simics_register_diff_filter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        self.campaign = kwargs['campaign']
        del kwargs['campaign']
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
        for item in sorted(self.queryset.filter(
            result__campaign_id=self.campaign
                ).values(attribute).distinct()):
            choices.append((item[attribute], item[attribute]))
        return sorted(choices, key=fix_sort_list)

    checkpoint_number = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')
    register = django_filters.MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'style': 'width:100%;'}), help_text='')

    class Meta:
        model = simics_register_diff
        exclude = ['config_object', 'gold_value', 'monitored_value', 'result']
