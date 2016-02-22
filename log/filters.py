from django.forms import NumberInput, Select, SelectMultiple, Textarea
from django_filters import (BooleanFilter, CharFilter, FilterSet,
                            MultipleChoiceFilter, NumberFilter)
from re import split

from .models import (event, injection, result, simics_register_diff)


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in split('([0-9]+)', str(string))])


def fix_sort_list(list):
    return fix_sort(list[0])


max_select_box_size = 10


class result_filter(FilterSet):
    def __init__(self, *args, **kwargs):
        campaign = kwargs['campaign']
        del kwargs['campaign']
        super().__init__(*args, **kwargs)
        dut_serial_port_choices = self.result_choices(
            campaign, 'dut_serial_port')
        self.filters['dut_serial_port'].extra.update(
            choices=dut_serial_port_choices)
        self.filters['dut_serial_port'].widget.attrs['size'] = min(
            len(dut_serial_port_choices), max_select_box_size)
        event_type_choices = self.event_choices(campaign, 'event_type')
        self.filters['event__event_type'].extra.update(
            choices=event_type_choices)
        self.filters['event__event_type'].widget.attrs['size'] = min(
            len(event_type_choices), max_select_box_size)
        level_choices = self.event_choices(campaign, 'level')
        self.filters['event__level'].extra.update(choices=level_choices)
        self.filters['event__level'].widget.attrs['size'] = min(
            len(level_choices), max_select_box_size)
        source_choices = self.event_choices(campaign, 'source')
        self.filters['event__source'].extra.update(choices=source_choices)
        self.filters['event__source'].widget.attrs['size'] = min(
            len(source_choices), max_select_box_size)
        bit_choices = self.injection_choices(campaign, 'bit')
        self.filters['injection__bit'].extra.update(choices=bit_choices)
        self.filters['injection__bit'].widget.attrs['size'] = min(
            len(bit_choices), max_select_box_size)
        checkpoint_number_choices = self.injection_choices(
            campaign, 'checkpoint_number')
        self.filters['injection__checkpoint_number'].extra.update(
            choices=checkpoint_number_choices)
        self.filters['injection__checkpoint_number'].widget.attrs['size'] = min(
            len(checkpoint_number_choices), max_select_box_size)
        field_choices = self.injection_choices(campaign, 'field')
        self.filters['injection__field'].extra.update(choices=field_choices)
        self.filters['injection__field'].widget.attrs['size'] = min(
            len(field_choices), max_select_box_size)
        processor_mode_choices = self.injection_choices(
            campaign, 'processor_mode')
        self.filters['injection__processor_mode'].extra.update(
            choices=processor_mode_choices)
        self.filters['injection__processor_mode'].widget.attrs['size'] = min(
            len(processor_mode_choices), max_select_box_size)
        register_choices = self.injection_choices(campaign, 'register')
        self.filters['injection__register'].extra.update(
            choices=register_choices)
        self.filters['injection__register'].widget.attrs['size'] = min(
            len(register_choices), max_select_box_size)
        register_index_choices = self.injection_choices(
            campaign, 'register_index')
        self.filters['injection__register_index'].extra.update(
            choices=register_index_choices)
        self.filters['injection__register_index'].widget.attrs['size'] = min(
            len(register_index_choices), max_select_box_size)
        target_choices = self.injection_choices(campaign, 'target')
        self.filters['injection__target'].extra.update(choices=target_choices)
        self.filters['injection__target'].widget.attrs['size'] = min(
            len(target_choices), max_select_box_size)
        target_index_choices = self.injection_choices(campaign, 'target_index')
        self.filters['injection__target_index'].extra.update(
            choices=target_index_choices)
        self.filters['injection__target_index'].widget.attrs['size'] = min(
            len(target_index_choices), max_select_box_size)
        num_injections_choices = self.result_choices(campaign, 'num_injections')
        self.filters['num_injections'].extra.update(
            choices=num_injections_choices)
        self.filters['num_injections'].widget.attrs['size'] = min(
            len(num_injections_choices), max_select_box_size)
        outcome_choices = self.result_choices(campaign, 'outcome')
        self.filters['outcome'].extra.update(choices=outcome_choices)
        self.filters['outcome'].widget.attrs['size'] = min(
            len(outcome_choices), max_select_box_size)
        outcome_category_choices = self.result_choices(
            campaign, 'outcome_category')
        self.filters['outcome_category'].extra.update(
            choices=outcome_category_choices)
        self.filters['outcome_category'].widget.attrs['size'] = min(
            len(outcome_category_choices), max_select_box_size)

    def event_choices(self, campaign, attribute):
        choices = []
        for item in event.objects.filter(
            result__campaign_id=campaign).values_list(
                attribute, flat=True).distinct():
            if item is not None:
                choices.append((item, item))
        return sorted(choices, key=fix_sort_list)

    def injection_choices(self, campaign, attribute):
        choices = []
        for item in injection.objects.filter(
            result__campaign_id=campaign).values_list(
                attribute, flat=True).distinct():
            if item is not None:
                choices.append((item, item))
        return sorted(choices, key=fix_sort_list)

    def result_choices(self, campaign, attribute):
        choices = []
        for item in result.objects.filter(campaign_id=campaign).values_list(
                attribute, flat=True).distinct():
            if item is not None:
                choices.append((item, item))
        return sorted(choices, key=fix_sort_list)

    aux_output = CharFilter(
        label='AUX console output', lookup_type='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    data_diff_gt = NumberFilter(
        name='data_diff', label='Data diff (>)', lookup_type='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    data_diff_lt = NumberFilter(
        name='data_diff', label='Data diff (<)', lookup_type='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    debugger_output = CharFilter(
        lookup_type='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    detected_errors = NumberFilter(
        name='detected_errors', label='Detected errors (>)', lookup_type='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    detected_errors_lt = NumberFilter(
        name='detected_errors', label='Detected errors (<)', lookup_type='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    dut_output = CharFilter(
        label='DUT console output', lookup_type='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    dut_serial_port = MultipleChoiceFilter(
        label='DUT serial port',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    event__description = CharFilter(
        lookup_type='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    event__event_type = MultipleChoiceFilter(
        conjoined=True, label='Event type',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    event__level = MultipleChoiceFilter(
        conjoined=True,
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    event__source = MultipleChoiceFilter(
        conjoined=True,
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    event__success = BooleanFilter(
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')
    injection__bit = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__checkpoint_number = MultipleChoiceFilter(
        label='Checkpoint number',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__field = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__processor_mode = MultipleChoiceFilter(
        label='Processor mode',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__register = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__register_index = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__success = BooleanFilter(
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')
    injection__target = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__target_index = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__time_gt = NumberFilter(
        name='time', label='Injection time (>)', lookup_type='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    injection__time_lt = NumberFilter(
        name='time', label='Injection time (<)', lookup_type='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    num_injections = MultipleChoiceFilter(
        label='Number of injections',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    outcome = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    outcome_category = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        model = result
        exclude = ('aux_serial_port', 'campaign', 'data_diff',
                   'detected_errors', 'timestamp')


class simics_register_diff_filter(FilterSet):
    def __init__(self, *args, **kwargs):
        self.campaign = kwargs['campaign']
        del kwargs['campaign']
        super().__init__(*args, **kwargs)
        self.queryset = kwargs['queryset']
        checkpoint_number_choices = self.simics_register_diff_choices(
            'checkpoint_number')
        self.filters['checkpoint_number'].extra.update(
            choices=checkpoint_number_choices)
        self.filters['checkpoint_number'].widget.attrs['size'] = min(
            len(checkpoint_number_choices), max_select_box_size)
        register_choices = self.simics_register_diff_choices('register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), max_select_box_size)

    def simics_register_diff_choices(self, attribute):
        choices = []
        for item in self.queryset.filter(
            result__campaign_id=self.campaign
                ).values_list(attribute, flat=True).distinct():
            choices.append((item, item))
        return sorted(choices, key=fix_sort_list)

    checkpoint_number = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    register = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        model = simics_register_diff
        fields = ('checkpoint_number', 'register')
