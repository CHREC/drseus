from django.forms import NumberInput, Select, SelectMultiple, Textarea
from django_filters import (BooleanFilter, CharFilter, FilterSet,
                            MultipleChoiceFilter, NumberFilter)
from threading import Thread

from log import fix_sort_list, models

max_select_box_size = 20


class event(FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = kwargs['queryset']

        def type_choices():
            type_choices = self.choices(self.queryset, 'type')
            self.filters['type'].extra.update(choices=type_choices)
            self.filters['type'].widget.attrs['size'] = min(
                len(type_choices), max_select_box_size)

        def level_choices():
            level_choices = self.choices(self.queryset, 'level')
            self.filters['level'].extra.update(choices=level_choices)
            self.filters['level'].widget.attrs['size'] = min(
                len(level_choices), max_select_box_size)

        def source_choices():
            source_choices = self.choices(self.queryset, 'source')
            self.filters['source'].extra.update(choices=source_choices)
            self.filters['source'].widget.attrs['size'] = min(
                len(source_choices), max_select_box_size)

        type_thread = Thread(target=type_choices)
        type_thread.start()
        level_thread = Thread(target=level_choices)
        level_thread.start()
        source_thread = Thread(target=source_choices)
        source_thread.start()
        type_thread.join()
        level_thread.join()
        source_thread.join()

    def choices(self, events, attribute):
        exclude_kwargs = {attribute+'__isnull': True}
        items = events.exclude(**exclude_kwargs).values_list(
            attribute, flat=True).distinct()
        choices = zip(items, items)
        return sorted(choices, key=fix_sort_list)

    description = CharFilter(
        label='Description', lookup_type='icontains',
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
        exclude = ('campaign', 'result')
        model = models.event


class injection(FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = kwargs['queryset']
        bit_choices = self.choices(self.queryset, 'bit')
        self.filters['bit'].extra.update(choices=bit_choices)
        self.filters['bit'].widget.attrs['size'] = min(
            len(bit_choices), max_select_box_size)
        checkpoint_choices = self.choices(self.queryset, 'checkpoint')
        self.filters['checkpoint'].extra.update(choices=checkpoint_choices)
        self.filters['checkpoint'].widget.attrs['size'] = min(
            len(checkpoint_choices), max_select_box_size)
        field_choices = self.choices(self.queryset, 'field')
        self.filters['field'].extra.update(choices=field_choices)
        self.filters['field'].widget.attrs['size'] = min(
            len(field_choices), max_select_box_size)
        processor_mode_choices = self.choices(self.queryset, 'processor_mode')
        self.filters['processor_mode'].extra.update(
            choices=processor_mode_choices)
        self.filters['processor_mode'].widget.attrs['size'] = min(
            len(processor_mode_choices), max_select_box_size)
        register_choices = self.choices(self.queryset, 'register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), max_select_box_size)
        register_access_choices = self.choices(self.queryset, 'register_access')
        self.filters['register_access'].extra.update(
            choices=register_access_choices)
        self.filters['register_access'].widget.attrs['size'] = min(
            len(register_access_choices), max_select_box_size)
        register_alias_choices = self.choices(self.queryset, 'register_alias')
        self.filters['register_alias'].extra.update(
            choices=register_alias_choices)
        self.filters['register_alias'].widget.attrs['size'] = min(
            len(register_alias_choices), max_select_box_size)
        register_index_choices = self.choices(self.queryset, 'register_index')
        self.filters['register_index'].extra.update(
            choices=register_index_choices)
        self.filters['register_index'].widget.attrs['size'] = min(
            len(register_index_choices), max_select_box_size)
        target_choices = self.choices(self.queryset, 'target')
        self.filters['target'].extra.update(choices=target_choices)
        self.filters['target'].widget.attrs['size'] = min(
            len(target_choices), max_select_box_size)
        target_index_choices = self.choices(self.queryset, 'target_index')
        self.filters['target_index'].extra.update(choices=target_index_choices)
        self.filters['target_index'].widget.attrs['size'] = min(
            len(target_index_choices), max_select_box_size)

    def choices(self, injections, attribute):
        choices = []
        exclude_kwargs = {attribute+'__isnull': True}
        for item in injections.exclude(**exclude_kwargs).values_list(
                attribute, flat=True).distinct():
            if isinstance(item, list):
                choices.append(('{'+','.join(map(str, item))+'}',
                                ':'.join(map(str, item))))
            else:
                choices.append((item, item))
        return sorted(choices, key=fix_sort_list)

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
    register_alias = MultipleChoiceFilter(
        label='Register alias',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    register_index = MultipleChoiceFilter(
        label='Register index',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    success = BooleanFilter(
        label='Success',
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')
    target = MultipleChoiceFilter(
        label='Target',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    target_index = MultipleChoiceFilter(
        label='Target index',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    time_gt = NumberFilter(
        name='time', label='Time (>)', lookup_type='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    time_lt = NumberFilter(
        name='time', label='Time (<)', lookup_type='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        exclude = ('config_object', 'gold_value', 'injected_value', 'result',
                   'timestamp')
        model = models.injection


class result(FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = kwargs['queryset']
        events = models.event.objects.filter(
            result_id__in=self.queryset.values('id'))
        injections = models.injection.objects.filter(
            result_id__in=self.queryset.values('id'))

        def event_type_choices():
            type_choices = event.choices(None, events, 'type')
            self.filters['event__type'].extra.update(choices=type_choices)
            self.filters['event__type'].widget.attrs['size'] = min(
                len(type_choices), max_select_box_size)

        def event_level_choices():
            level_choices = event.choices(None, events, 'level')
            self.filters['event__level'].extra.update(choices=level_choices)
            self.filters['event__level'].widget.attrs['size'] = min(
                len(level_choices), max_select_box_size)

        def event_source_choices():
            source_choices = event.choices(None, events, 'source')
            self.filters['event__source'].extra.update(choices=source_choices)
            self.filters['event__source'].widget.attrs['size'] = min(
                len(source_choices), max_select_box_size)

        event_type_thread = Thread(target=event_type_choices)
        event_type_thread.start()
        event_level_thread = Thread(target=event_level_choices)
        event_level_thread.start()
        event_source_thread = Thread(target=event_source_choices)
        event_source_thread.start()

        campaign_id_choices = self.choices(self.queryset, 'campaign_id')
        self.filters['campaign_id'].extra.update(choices=campaign_id_choices)
        self.filters['campaign_id'].widget.attrs['size'] = min(
            len(campaign_id_choices), max_select_box_size)
        dut_serial_port_choices = self.choices(self.queryset, 'dut_serial_port')
        self.filters['dut_serial_port'].extra.update(
            choices=dut_serial_port_choices)
        self.filters['dut_serial_port'].widget.attrs['size'] = min(
            len(dut_serial_port_choices), max_select_box_size)
        bit_choices = injection.choices(None, injections, 'bit')
        self.filters['injection__bit'].extra.update(choices=bit_choices)
        self.filters['injection__bit'].widget.attrs['size'] = min(
            len(bit_choices), max_select_box_size)
        checkpoint_choices = injection.choices(None, injections, 'checkpoint')
        self.filters['injection__checkpoint'].extra.update(
            choices=checkpoint_choices)
        self.filters['injection__checkpoint'].widget.attrs['size'] = min(
            len(checkpoint_choices), max_select_box_size)
        field_choices = injection.choices(None, injections, 'field')
        self.filters['injection__field'].extra.update(choices=field_choices)
        self.filters['injection__field'].widget.attrs['size'] = min(
            len(field_choices), max_select_box_size)
        processor_mode_choices = injection.choices(
            None, injections, 'processor_mode')
        self.filters['injection__processor_mode'].extra.update(
            choices=processor_mode_choices)
        self.filters['injection__processor_mode'].widget.attrs['size'] = min(
            len(processor_mode_choices), max_select_box_size)
        register_choices = injection.choices(None, injections, 'register')
        self.filters['injection__register'].extra.update(
            choices=register_choices)
        self.filters['injection__register'].widget.attrs['size'] = min(
            len(register_choices), max_select_box_size)
        register_access_choices = injection.choices(
            None, injections, 'register_access')
        self.filters['injection__register_access'].extra.update(
            choices=register_access_choices)
        self.filters['injection__register_access'].widget.attrs['size'] = min(
            len(register_access_choices), max_select_box_size)
        register_alias_choices = injection.choices(
            None, injections, 'register_alias')
        self.filters['injection__register_alias'].extra.update(
            choices=register_alias_choices)
        self.filters['injection__register_alias'].widget.attrs['size'] = min(
            len(register_alias_choices), max_select_box_size)
        register_index_choices = injection.choices(
            None, injections, 'register_index')
        self.filters['injection__register_index'].extra.update(
            choices=register_index_choices)
        self.filters['injection__register_index'].widget.attrs['size'] = min(
            len(register_index_choices), max_select_box_size)
        target_choices = injection.choices(None, injections, 'target')
        self.filters['injection__target'].extra.update(choices=target_choices)
        self.filters['injection__target'].widget.attrs['size'] = min(
            len(target_choices), max_select_box_size)
        target_index_choices = injection.choices(
            None, injections, 'target_index')
        self.filters['injection__target_index'].extra.update(
            choices=target_index_choices)
        self.filters['injection__target_index'].widget.attrs['size'] = min(
            len(target_index_choices), max_select_box_size)
        num_injections_choices = self.choices(self.queryset, 'num_injections')
        self.filters['num_injections'].extra.update(
            choices=num_injections_choices)
        self.filters['num_injections'].widget.attrs['size'] = min(
            len(num_injections_choices), max_select_box_size)
        outcome_choices = self.choices(self.queryset, 'outcome')
        self.filters['outcome'].extra.update(choices=outcome_choices)
        self.filters['outcome'].widget.attrs['size'] = min(
            len(outcome_choices), max_select_box_size)
        outcome_category_choices = self.choices(
            self.queryset, 'outcome_category')
        self.filters['outcome_category'].extra.update(
            choices=outcome_category_choices)
        self.filters['outcome_category'].widget.attrs['size'] = min(
            len(outcome_category_choices), max_select_box_size)

        event_type_thread.join()
        event_level_thread.join()
        event_source_thread.join()

    def choices(self, results, attribute):
        exclude_kwargs = {attribute+'__isnull': True}
        items = results.exclude(**exclude_kwargs).values_list(
            attribute, flat=True).distinct()
        choices = zip(items, items)
        return sorted(choices, key=fix_sort_list)

    aux_output = CharFilter(
        label='AUX console output', lookup_type='icontains',
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='')
    campaign_id = MultipleChoiceFilter(
        label='Campaign ID',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
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
    detected_errors_gt = NumberFilter(
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
    execution_time_gt = NumberFilter(
        name='execution_time', label='Execution time (>)', lookup_type='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    execution_time_lt = NumberFilter(
        name='execution_time', label='Execution time (<)', lookup_type='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    event__description = CharFilter(
        label='Description', lookup_type='icontains',
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
    injection__register_alias = MultipleChoiceFilter(
        label='Register alias',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__register_index = MultipleChoiceFilter(
        label='Register index',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__success = BooleanFilter(
        label='Success',
        widget=Select(choices=(('3', 'Unknown'), ('1', 'True'), ('0', 'False')),
                      attrs={'class': 'form-control'}), help_text='')
    injection__target = MultipleChoiceFilter(
        label='Target',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__target_index = MultipleChoiceFilter(
        label='Target index',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    injection__time_gt = NumberFilter(
        name='time', label='Time (>)', lookup_type='gt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    injection__time_lt = NumberFilter(
        name='time', label='Time (<)', lookup_type='lt',
        widget=NumberInput(attrs={'class': 'form-control'}), help_text='')
    num_injections = MultipleChoiceFilter(
        label='Quantity',
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    outcome = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    outcome_category = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        model = models.result
        exclude = ('aux_serial_port', 'campaign', 'cycles', 'data_diff',
                   'detected_errors', 'execution_time', 'returned', 'timestamp')


class simics_register_diff(FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = kwargs['queryset']
        checkpoint_choices = self.choices(self.queryset, 'checkpoint')
        self.filters['checkpoint'].extra.update(choices=checkpoint_choices)
        self.filters['checkpoint'].widget.attrs['size'] = min(
            len(checkpoint_choices), max_select_box_size)
        register_choices = self.choices(self.queryset, 'register')
        self.filters['register'].extra.update(choices=register_choices)
        self.filters['register'].widget.attrs['size'] = min(
            len(register_choices), max_select_box_size)

    def choices(self, simics_register_diffs, attribute):
        exclude_kwargs = {attribute+'__isnull': True}
        items = simics_register_diffs.exclude(**exclude_kwargs).values_list(
            attribute, flat=True).distinct()
        choices = zip(items, items)
        return sorted(choices, key=fix_sort_list)

    checkpoint = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')
    register = MultipleChoiceFilter(
        widget=SelectMultiple(attrs={'class': 'form-control'}), help_text='')

    class Meta:
        model = models.simics_register_diff
        fields = ('checkpoint', 'register')
