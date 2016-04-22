from . import create_chart


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    group_categories = kwargs['group_categories']
    order = kwargs['order']
    outcomes = kwargs['outcomes']

    chart_id = 'checkpoints_chart'
    injections = injections.exclude(checkpoint__isnull=True)
    checkpoints = list(injections.values_list(
        'checkpoint', flat=True).distinct().order_by('checkpoint'))
    if len(checkpoints) < 1:
        return
    create_chart(chart_list, chart_data, 'Injections Over Time', order,
                 chart_id, injections, 'Injected Checkpoint', 'Checkpoint',
                 'checkpoint', checkpoints, outcomes, group_categories,
                 smooth=True)


def data_diff(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    order = kwargs['order']

    chart_id = 'diff_checkpoints_chart'
    injections = injections.exclude(checkpoint__isnull=True)
    checkpoints = list(injections.values_list(
        'checkpoint', flat=True).distinct().order_by('checkpoint'))
    if len(checkpoints) < 1:
        return
    create_chart(chart_list, chart_data, 'Data Destruction Over Time', order,
                 chart_id, injections, 'Injected Checkpoint', 'Checkpoint',
                 'checkpoint', checkpoints, ['Data Match'],
                 average='result__data_diff')
