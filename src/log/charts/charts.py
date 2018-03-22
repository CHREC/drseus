from django.db.models import Avg, StdDev
from django.db.models import Max
from numpy import linspace

from . import create_chart

overview_order = order = 0


def overview(**kwargs):
    if 'success' not in kwargs or not kwargs['success']:
        kwargs['xaxis_model'] = 'results'
    create_chart(order=overview_order,
                 chart_title='Overview',
                 pie=True,
                 **kwargs)


outcomes_by_target_combined_order = order = order + 1


def outcomes_by_target_combined(**kwargs):
    create_chart(order=outcomes_by_target_combined_order,
                 chart_title='Targets (Combined)',
                 xaxis_title='Injected Target',
                 xaxis_name='Target',
                 xaxis_type='target',
                 log=True,
                 percent=True,
                 **kwargs)


outcomes_by_target_order = order = order + 1


def outcomes_by_target(**kwargs):
    create_chart(order=outcomes_by_target_order,
                 chart_title='Targets',
                 xaxis_title='Injected Target',
                 xaxis_name='Target',
                 xaxis_type='target_name',
                 log=True,
                 percent=True,
                 **kwargs)


data_diff_by_targets_order = order = order + 1


def data_diff_by_targets(**kwargs):
    create_chart(order=data_diff_by_targets_order,
                 chart_title='Data Destruction By Target',
                 xaxis_title='Injected Target',
                 xaxis_name='Target',
                 xaxis_type='target_name',
                 yaxis_items=['Average Data Match'],
                 average='result__data_diff',
                 **kwargs)


execution_time_by_target_order = order = order + 1


def execution_time_by_target(**kwargs):
    kwargs['injections'] = kwargs['injections'].filter(
        result__returned=True).exclude(result__execution_time__isnull=True)
    create_chart(order=execution_time_by_target_order,
                 chart_title='Average Execution Time By Target',
                 xaxis_title='Injected Target',
                 xaxis_name='Target',
                 xaxis_type='target_name',
                 yaxis_items=['Average Execution Time'],
                 average='result__execution_time',
                 **kwargs)


outcomes_by_registers_order = order = order + 1


def outcomes_by_registers(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(target='TLB')
    create_chart(order=outcomes_by_registers_order,
                 chart_title='Registers',
                 xaxis_title='Injected Register',
                 xaxis_name='Register',
                 xaxis_type='register',
                 rotate_labels=True,
                 percent=True,
                 **kwargs)


outcomes_by_register_fields_order = order = order + 1


def outcomes_by_register_fields(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(
        target='TLB').exclude(field__isnull=True)
    create_chart(order=order,
                 chart_title='Register Fields',
                 xaxis_title='Injected Register Field',
                 xaxis_name='Field',
                 xaxis_type='field',
                 rotate_labels=True,
                 percent=True,
                 **kwargs)


outcomes_by_register_bits_order = order = order + 1


def outcomes_by_register_bits(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(target='TLB')
    create_chart(order=outcomes_by_register_bits_order,
                 chart_title='Register Bits',
                 xaxis_title='Injected Bit',
                 xaxis_name='Bit',
                 xaxis_type='bit',
                 percent=True,
                 **kwargs)


outcomes_by_register_access_order = order = order + 1


def outcomes_by_register_access(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(
        target='TLB').exclude(register_access__isnull=True)
    create_chart(order=outcomes_by_register_access_order,
                 chart_title='Register Access',
                 xaxis_title='Injected Register Acces',
                 xaxis_name='Access',
                 xaxis_type='register_access',
                 percent=True,
                 **kwargs)


outcomes_by_tlb_entries_order = order = order + 1


def outcomes_by_tlb_entries(**kwargs):
    kwargs['injections'] = kwargs['injections'].filter(target='TLB')
    create_chart(order=outcomes_by_tlb_entries_order,
                 chart_title='TLB Entries',
                 xaxis_title='Injected TLB Entry',
                 xaxis_name='Entry',
                 xaxis_type='tlb_entry',
                 rotate_labels=True,
                 percent=True,
                 **kwargs)


outcomes_by_tlb_fields_order = order = order + 1


def outcomes_by_tlb_fields(**kwargs):
    kwargs['injections'] = kwargs['injections'].filter(target='TLB')
    create_chart(order=outcomes_by_tlb_fields_order,
                 chart_title='TLB Fields',
                 xaxis_title='Injected TLB Field',
                 xaxis_name='Field',
                 xaxis_type='field',
                 rotate_labels=True,
                 percent=True,
                 **kwargs)


outcomes_by_execution_times_order = order = order + 1


def outcomes_by_execution_times(**kwargs):
    kwargs['results'] = kwargs['results'].filter(returned=True).exclude(
        execution_time__isnull=True)
    avg = kwargs['results'].aggregate(
        Avg('execution_time'))['execution_time__avg']
    std_dev = kwargs['results'].aggregate(
        StdDev('execution_time'))['execution_time__stddev']
    execution_times = linspace(max(0, avg-(std_dev*3)), avg+(std_dev*3), 1000,
                               endpoint=False).tolist()
    create_chart(order=outcomes_by_execution_times_order,
                 chart_title='Execution Times',
                 xaxis_title=(
                    'Execution Time (Seconds) for '
                    '(\u03bc-3\u03c3, \u03bc+3\u03c3), '
                    '\u03bc={:.2f} & \u03c3={:.2f}'.format(avg, std_dev)),
                 xaxis_name='Time',
                 xaxis_model='results',
                 xaxis_type='execution_time',
                 xaxis_items=execution_times,
                 smooth=True,
                 intervals=True,
                 **kwargs)


outcomes_by_injection_times_order = order = order + 1


def outcomes_by_injection_times(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(time__isnull=True)
    if not kwargs['injections'].count():
        return
    times = linspace(0,
                     kwargs['injections'].aggregate(Max('time'))['time__max'],
                     min(kwargs['injections'].count()/25, 1000),
                     endpoint=False).tolist()[1:]
    create_chart(order=outcomes_by_injection_times_order,
                 chart_title='Injections Over Time',
                 xaxis_title='Injection Time (Seconds)',
                 xaxis_name='Time',
                 xaxis_type='time',
                 xaxis_items=times,
                 smooth=True,
                 intervals=True,
                 **kwargs)


data_diff_by_injection_times_order = order = order + 1


def data_diff_by_injection_times(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(time__isnull=True)
    if not kwargs['injections'].count():
        return
    times = linspace(0,
                     kwargs['injections'].aggregate(Max('time'))['time__max'],
                     min(kwargs['injections'].count()/25, 1000),
                     endpoint=False).tolist()[1:]
    create_chart(order=data_diff_by_injection_times_order,
                 chart_title='Data Destruction Over Time',
                 xaxis_title='Injection Time (Seconds)',
                 xaxis_name='Time',
                 xaxis_type='time',
                 xaxis_items=times,
                 yaxis_items=['Average Data Match'],
                 average='result__data_diff',
                 smooth=True,
                 intervals=True,
                 export_wide=True,
                 **kwargs)


outcomes_by_checkpoint_order = order = order + 1


def outcomes_by_checkpoint(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(checkpoint__isnull=True)
    create_chart(order=outcomes_by_checkpoint_order,
                 chart_title='Injections Over Time',
                 xaxis_title='Injected Checkpoint',
                 xaxis_name='Checkpoint',
                 xaxis_type='checkpoint',
                 smooth=True,
                 **kwargs)


data_diff_by_checkpoint_order = order = order + 1


def data_diff_by_checkpoint(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(checkpoint__isnull=True)
    create_chart(order=data_diff_by_checkpoint_order,
                 chart_title='Data Destruction Over Time',
                 xaxis_title='Injected Checkpoint',
                 xaxis_name='Checkpoint',
                 xaxis_type='checkpoint',
                 yaxis_items=['Average Data Match'],
                 average='result__data_diff',
                 smooth=True,
                 **kwargs)


outcomes_by_num_injections_order = order = order + 1


def outcomes_by_num_injections(**kwargs):
    kwargs['results'] = kwargs['results'].exclude(
        num_injections=0).exclude(num_injections__isnull=True)
    create_chart(order=outcomes_by_num_injections_order,
                 chart_title='Injection Quantity',
                 xaxis_title='Injections Per Execution',
                 xaxis_name='Injections',
                 xaxis_model='results',
                 xaxis_type='num_injections',
                 percent=True,
                 **kwargs)


register_propagation_order = order = order + 1


def register_propagation(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(
        result__num_register_diffs__isnull=True)
    create_chart(order=register_propagation_order,
                 chart_title='Fault Propagation (Registers)',
                 xaxis_title='Injection Target',
                 xaxis_name='Target',
                 xaxis_type='target_name',
                 yaxis_items=['Average Registers Affected'],
                 average='result__num_register_diffs',
                 log=True,
                 **kwargs)


memory_propagation_order = order = order + 1


def memory_propagation(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(
        result__num_memory_diffs__isnull=True)
    create_chart(order=order,
                 chart_title='Fault Propagation (Memory Blocks)',
                 xaxis_title='Injection Target',
                 xaxis_name='Target',
                 xaxis_type='target_name',
                 yaxis_items=['Average Memory Blocks Affected'],
                 average='result__num_memory_diffs',
                 log=True,
                 **kwargs)


register_propagation_combined_order = order = order + 1


def register_propagation_combined(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(
        result__num_register_diffs__isnull=True)
    create_chart(order=register_propagation_combined_order,
                 chart_title='Fault Propagation (Registers, Combined Targets)',
                 xaxis_title='Injection Target',
                 xaxis_name='Target',
                 xaxis_type='target',
                 yaxis_items=['Average Registers Affected'],
                 average='result__num_register_diffs',
                 log=True,
                 **kwargs)


memory_propagation_combined_order = order = order + 1


def memory_propagation_combined(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(
        result__num_memory_diffs__isnull=True)
    create_chart(order=memory_propagation_combined_order,
                 chart_title='Fault Propagation '
                             '(Memory Blocks, Combined Targets)',
                 xaxis_title='Injection Target',
                 xaxis_name='Target',
                 xaxis_type='target',
                 yaxis_items=['Avg Memory Blocks Affected'],
                 average='result__num_memory_diffs',
                 log=True,
                 **kwargs)


outcomes_by_device_order = order = order + 1


def outcomes_by_device(**kwargs):
    create_chart(order=outcomes_by_device_order,
                 chart_title='Devices (Serial Numbers)',
                 xaxis_title='Serial Number',
                 xaxis_name='Serial',
                 xaxis_model='results',
                 xaxis_type='dut_dev_serial',
                 percent=True,
                 **kwargs)


outcomes_by_port_order = order = order + 1


def outcomes_by_port(**kwargs):
    create_chart(order=outcomes_by_port_order,
                 chart_title='Devices (Serial Ports)',
                 xaxis_title='Serial Port',
                 xaxis_name='Port',
                 xaxis_model='results',
                 xaxis_type='dut_serial_port',
                 percent=True,
                 **kwargs)


results_by_data_hash_order = order = order + 1


def results_by_data_hash(**kwargs):
    kwargs['injections'] = kwargs['injections'].exclude(checkpoint__isnull=True)
    create_chart(order=results_by_data_hash_order,
                 chart_title='Data Hashes',
                 xaxis_title='Data Hash',
                 xaxis_name='Hash',
                 xaxis_model='results',
                 xaxis_type='data_hash',
                 **kwargs)
