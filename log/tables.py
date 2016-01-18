import django_tables2 as tables

import models


class campaign_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = models.campaign
        exclude = ('aux_output', 'debugger_output', 'dut_output')


class campaigns_table(tables.Table):
    id = tables.TemplateColumn('<a href="/{{ value }}/results">{{ value }}</a>')
    results = tables.Column(empty_values=())
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    def render_results(self, record):
        return str(models.result.objects.filter(campaign=record.id).count())

    class Meta:
        attrs = {"class": "paleblue"}
        model = models.campaign
        exclude = ('application', 'aux_application', 'aux_output',
                   'cycles_between', 'debugger_output', 'dut_output',
                   'kill_dut', 'num_checkpoints', 'output_file', 'use_aux',
                   'use_aux_output')


class result_table(tables.Table):
    outcome = tables.TemplateColumn('{{ form.outcome }}')
    outcome_category = tables.TemplateColumn('{{ form.outcome_category }}')
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')
    edit = tables.TemplateColumn('<input type="submit" name="save" '
                                 'value="Save" onclick="return confirm('
                                 '\'Are you sure you want to edit this '
                                 'result?\')"/>')
    delete = tables.TemplateColumn('<input type="submit" name="delete" '
                                   'value="Delete" onclick="return confirm('
                                   '\'Are you sure you want to delete this '
                                   'result?\')" />')

    class Meta:
        attrs = {"class": "paleblue"}
        model = models.result
        exclude = ('aux_output', 'campaign', 'debugger_output', 'dut_output')


class results_table(tables.Table):
    id = tables.TemplateColumn(  # LinkColumn()
        '<a href="../result/{{ value }}">{{ value }}</a>')
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')
    targets = tables.Column(empty_values=())
    select = tables.TemplateColumn(
        '<input type="checkbox" name="select_box" '
        'value="{{ record.id }}">', orderable=False)

    def render_targets(self, record):
        if record is not None:
            targets = [injection_.target for injection_
                       in models.injection.objects.filter(result=record.id)]
        else:
            targets = []
        for index in xrange(len(targets)):
            if targets[index] is None:
                targets[index] = '-'
        if len(targets) > 0:
            return ', '.join(targets)
        else:
            return '-'

    class Meta:
        attrs = {"class": "paleblue"}
        model = models.result
        exclude = ('aux_output', 'campaign', 'debugger_output', 'dut_output')


class hw_injection_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = models.injection
        exclude = ('config_object', 'config_type', 'checkpoint_number', 'field',
                   'id', 'register_index', 'result')


class simics_injection_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = models.injection
        exclude = ('config_object', 'config_type', 'id', 'result', 'time')


class simics_register_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id', 'result')
        model = models.simics_register_diff


class simics_memory_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id', 'result')
        model = models.simics_memory_diff
