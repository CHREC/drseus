from django.forms import NumberInput, Select, SelectMultiple, Textarea
from django_filters import (BooleanFilter, CharFilter, FilterSet,
                            MultipleChoiceFilter, NumberFilter)
from progressbar import ProgressBar
from progressbar.widgets import Bar, Percentage, SimpleProgress, Timer
from time import perf_counter

from . import fix_sort_list, models


def choices(queryset, attribute):
    choices = []
    exclude_kwargs = {'{}__isnull'.format(attribute): True}
    for item in queryset.exclude(**exclude_kwargs).values_list(
            attribute, flat=True).distinct():
        if isinstance(item, list):
            choice = '{{{}}}'.format(', '.join(map(str, item)))
            choices.append((choice, choice))
        else:
            choices.append((item, item))
    return sorted(choices, key=fix_sort_list)


event_choices = {
    'level': [],
    'source': [],
    'type': []
}
injection_choices = {
    'bit': [],
    'checkpoint': [],
    'field': [],
    'processor_mode': [],
    'register': [],
    'register_access': [],
    'register_index': [],
    'target_name': [],
    'tlb_entry': []
}
result_choices = {
    'campaign_id': [],
    'dut_serial_port': [],
    'num_injections': [],
    'outcome': [],
    'outcome_category': []
}


def update_choices():
    print('generating filter choices...')
    events = models.event.objects.all()
    choice_count = len(event_choices) + len(injection_choices) + \
        len(result_choices)
    progress_bar = ProgressBar(max_value=choice_count, widgets=[
        Percentage(), ' (', SimpleProgress(format='%(value)d/%(max_value)d'),
        ') ', Bar(), ' ', Timer()])
    count = 0
    for attribute in event_choices:
        count += 1
        progress_bar.update(count)
        event_choices[attribute] = choices(events, attribute)
    injections = models.injection.objects.all()
    for attribute in injection_choices:
        count += 1
        progress_bar.update(count)
        injection_choices[attribute] = choices(injections, attribute)
    results = models.result.objects.all()
    for attribute in result_choices:
        count += 1
        progress_bar.update(count)
        result_choices[attribute] = choices(results, attribute)
    print()


class event(FilterSet):
    def __init__(self, *args, **kwargs):
        if not event_choices['level'] and kwargs['queryset'].count():
            update_choices()
        super().__init__(*args, **kwargs)
        for attribute in event_choices:
            self.filters[attribute].extra.update(
                choices=event_choices[attribute])
            self.filters[attribute].widget.attrs['size'] = min(
                len(event_choices[attribute]), 50)

    description = CharFilter(
        label='Description', lookup_expr='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    type = MultipleChoiceFilter(
        label='Type',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    level = MultipleChoiceFilter(
        label='Level',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    source = MultipleChoiceFilter(
        label='Source',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    success = BooleanFilter(
        label='Success',
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')

    class Meta:
        exclude = ('campaign', 'result', 'timestamp')
        model = models.event


class injection(FilterSet):
    def __init__(self, *args, **kwargs):
        if not injection_choices['register'] and kwargs['queryset'].count():
            update_choices()
        super().__init__(*args, **kwargs)
        for attribute in injection_choices:
            self.filters[attribute].extra.update(
                choices=injection_choices[attribute])
            self.filters[attribute].widget.attrs['size'] = min(
                len(injection_choices[attribute]), 25)

    bit = MultipleChoiceFilter(
        label='Bit',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    checkpoint = MultipleChoiceFilter(
        label='Checkpoint number',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    field = MultipleChoiceFilter(
        label='Field',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    processor_mode = MultipleChoiceFilter(
        label='Processor mode',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    register = MultipleChoiceFilter(
        label='Register',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    register_access = MultipleChoiceFilter(
        label='Register access',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    register_index = MultipleChoiceFilter(
        label='Register index',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    success = BooleanFilter(
        label='Success',
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')
    target_name = MultipleChoiceFilter(
        label='Target',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    time_gt = NumberFilter(
        name='time', label='Time (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    time_lt = NumberFilter(
        name='time', label='Time (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    tlb_entry = MultipleChoiceFilter(
        label='TLB entry',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        exclude = ('config_object', 'gold_value', 'injected_value',
                   'register_alias', 'result', 'target', 'target_index', 'time',
                   'timestamp')
        model = models.injection


class result(FilterSet):
    def __init__(self, *args, **kwargs):
        if not result_choices['campaign_id'] and kwargs['queryset'].count():
            update_choices()
        super().__init__(*args, **kwargs)
        for attribute in event_choices:
            self.filters['event__{}'.format(attribute)].extra.update(
                choices=event_choices[attribute])
            self.filters[
                'event__{}'.format(attribute)
            ].widget.attrs['size'] = min(len(event_choices[attribute]), 50)
        for attribute in injection_choices:
            self.filters['injection__{}'.format(attribute)].extra.update(
                choices=injection_choices[attribute])
            self.filters[
                'injection__{}'.format(attribute)
            ].widget.attrs['size'] = min(len(injection_choices[attribute]), 25)
        for attribute in result_choices:
            self.filters[attribute].extra.update(
                choices=result_choices[attribute])
            self.filters[attribute].widget.attrs['size'] = min(
                len(result_choices[attribute]), 50)

    def choices(self, results, attribute):
        exclude_kwargs = {'{}__isnull'.format(attribute): True}
        items = results.exclude(**exclude_kwargs).values_list(
            attribute, flat=True).distinct()
        choices = zip(items, items)
        return sorted(choices, key=fix_sort_list)

    aux_output = CharFilter(
        label='AUX console output', lookup_expr='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    campaign_id = MultipleChoiceFilter(
        label='Campaign ID',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    data_diff_gt = NumberFilter(
        name='data_diff', label='Data diff (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    data_diff_lt = NumberFilter(
        name='data_diff', label='Data diff (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    debugger_output = CharFilter(
        lookup_expr='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    detected_errors_gt = NumberFilter(
        name='detected_errors', label='Detected errors (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    detected_errors_lt = NumberFilter(
        name='detected_errors', label='Detected errors (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    dut_output = CharFilter(
        label='DUT console output', lookup_expr='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    dut_serial_port = MultipleChoiceFilter(
        label='DUT serial port',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    execution_time_gt = NumberFilter(
        name='execution_time', label='Execution time (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    execution_time_lt = NumberFilter(
        name='execution_time', label='Execution time (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    event__description = CharFilter(
        label='Description', lookup_expr='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    event__type = MultipleChoiceFilter(
        conjoined=True, label='Type',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    event__level = MultipleChoiceFilter(
        conjoined=True, label='Level',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    event__source = MultipleChoiceFilter(
        conjoined=True, label='Source',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    event__success = BooleanFilter(
        label='Success',
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')
    id_gt = NumberFilter(
        name='id', label='Result ID (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    id_lt = NumberFilter(
        name='id', label='Result ID (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    injection__bit = MultipleChoiceFilter(
        label='Bit',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__checkpoint = MultipleChoiceFilter(
        label='Checkpoint',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__field = MultipleChoiceFilter(
        label='Field',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__processor_mode = MultipleChoiceFilter(
        label='Processor mode',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__register = MultipleChoiceFilter(
        label='Register',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__register_access = MultipleChoiceFilter(
        label='Register access',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__register_index = MultipleChoiceFilter(
        label='Register index',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__success = BooleanFilter(
        label='Success',
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')
    injection__target_name = MultipleChoiceFilter(
        label='Target',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__time_gt = NumberFilter(
        name='time', label='Time (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    injection__time_lt = NumberFilter(
        name='time', label='Time (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    injection__tlb_entry = MultipleChoiceFilter(
        label='TLB entry',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    num_injections = MultipleChoiceFilter(
        label='Injection quantity',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    num_memory_diffs_gt = NumberFilter(
        name='num_memory_diffs', label='Register diffs (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    num_memory_diffs_lt = NumberFilter(
        name='num_memory_diffs', label='Register diffs (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    num_register_diffs_gt = NumberFilter(
        name='num_register_diffs', label='Memory diffs (>)', lookup_expr='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    num_register_diffs_lt = NumberFilter(
        name='num_register_diffs', label='Memory diffs (<)', lookup_expr='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    outcome = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    outcome_category = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        model = models.result
        exclude = ('aux_serial_port', 'campaign', 'cycles', 'data_diff',
                   'detected_errors', 'execution_time', 'num_memory_diffs',
                   'num_register_diffs', 'returned', 'timestamp')


class simics_register_diff(FilterSet):
    def __init__(self, *args, **kwargs):
        start = perf_counter()
        super().__init__(*args, **kwargs)
        checkpoint_choices = choices(kwargs['queryset'], 'checkpoint')
        self.filters['checkpoint'].extra.update(choices=checkpoint_choices)
        self.filters['checkpoint'].widget.attrs['size'] = min(
            len(checkpoint_choices), 50)
        register_choices = choices(kwargs['queryset'], 'register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), 50)
        print('register diff filter', round(perf_counter()-start, 2), 'seconds')

    checkpoint = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    register = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        model = models.simics_register_diff
        fields = ('checkpoint', 'register')
