from .. import fix_sort
from . import create_chart


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    chart_id = 'registers_chart'
    injections = injections.exclude(target='TLB')
    registers = sorted(
        injections.values_list('register', flat=True).distinct(), key=fix_sort)
    if len(registers) < 1:
        return
    create_chart(chart_list, chart_data, 'Registers', order, chart_id,
                 injections, 'Injected Register', 'Register', 'register',
                 registers, outcomes, group_categories, success,
                 rotate_labels=True)


def fields(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    chart_id = 'register_fields_chart'
    injections = injections.exclude(target='TLB').exclude(field__isnull=True)
    fields = list(injections.values_list(
        'field', flat=True).distinct().order_by('field'))
    if len(fields) < 1:
        return
    create_chart(chart_list, chart_data, 'Register Fields', order, chart_id,
                 injections, 'Injected Register Field', 'Field', 'field',
                 fields, outcomes, group_categories, success,
                 rotate_labels=True)


def bits(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    chart_id = 'register_bits_chart'
    injections = injections.exclude(target='TLB')
    bits = list(
        injections.values_list('bit', flat=True).distinct().order_by('-bit'))
    if len(bits) < 1:
        return
    create_chart(chart_list, chart_data, 'Register Bits', order, chart_id,
                 injections,
                 'Injected Bit (MSB={})'.format(31 if max(bits) < 32 else 63),
                 'Bit', 'bit', bits, outcomes, group_categories, success)


def access(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    chart_id = 'register_accesses_chart'
    injections = injections.exclude(target='TLB').exclude(
        register_access__isnull=True)
    register_accesses = list(injections.values_list(
        'register_access', flat=True).distinct().order_by('register_access'))
    if len(register_accesses) < 1:
        return
    create_chart(chart_list, chart_data, 'Register Access', order, chart_id,
                 injections, 'Injected Register Access', 'Access',
                 'register_access', register_accesses, outcomes,
                 group_categories, success)
