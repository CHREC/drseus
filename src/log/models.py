"""
Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""

from django.contrib.postgres.fields import ArrayField
from django.db.models import (BooleanField, BigIntegerField, DateTimeField,
                              FloatField, ForeignKey, IntegerField, Model,
                              NullBooleanField, OneToOneField, SET_NULL,
                              TextField)


class campaign(Model):
    architecture = TextField()
    aux = BooleanField()
    aux_command = TextField(null=True)
    aux_output = TextField(default=str)
    aux_output_file = BooleanField(default=False)
    aux_log_files = ArrayField(TextField(), default=list)
    checkpoints = IntegerField(null=True)
    command = TextField(default=str)
    cycles = BigIntegerField(null=True)
    cycles_between = BigIntegerField(null=True)
    debugger_output = TextField(default=str)
    description = TextField(null=True)
    dut_output = TextField(default=str)
    execution_time = FloatField(null=True)
    kill_dut = BooleanField(default=False)
    kill_aux = BooleanField(default=False)
    log_files = ArrayField(TextField(), default=list)
    output_file = TextField(null=True)
    rsakey = TextField()
    simics = BooleanField()
    caches = BooleanField()
    start_cycle = BigIntegerField(null=True)
    start_time = FloatField(null=True)
    timestamp = DateTimeField(auto_now_add=True)


class result(Model):
    aux_output = TextField(default=str)
    aux_serial_port = TextField(null=True)
    campaign = ForeignKey(campaign)
    returned = NullBooleanField()
    cycles = BigIntegerField(null=True)
    data_diff = FloatField(null=True)
    data_hash = TextField(null=True)
    debugger_output = TextField(default=str)
    detected_errors = IntegerField(null=True)
    dut_dev_serial = TextField(null=True)
    dut_output = TextField(default=str)
    dut_serial_port = TextField(null=True)
    execution_time = FloatField(null=True)
    num_injections = IntegerField(null=True)
    num_register_diffs = IntegerField(null=True)
    num_memory_diffs = IntegerField(null=True)
    outcome = TextField()
    outcome_category = TextField()
    previous_result = OneToOneField('self', null=True,
                                    related_name='next_result',
                                    on_delete=SET_NULL)
    timestamp = DateTimeField(auto_now_add=True)


class event(Model):
    campaign = ForeignKey(campaign, null=True)
    description = TextField(null=True)
    level = TextField()
    result = ForeignKey(result, null=True)
    source = TextField()
    success = NullBooleanField()
    timestamp = DateTimeField(auto_now_add=True)
    type = TextField()


class injection(Model):
    bit = IntegerField(null=True)
    checkpoint = IntegerField(null=True)
    config_object = TextField(null=True)
    field = TextField(null=True)
    gold_value = TextField(null=True)
    injected_value = TextField(null=True)
    processor_mode = TextField(null=True)
    register = TextField(null=True)
    register_access = TextField(null=True)
    register_alias = TextField(null=True)
    register_index = ArrayField(IntegerField(), null=True)
    result = ForeignKey(result)
    success = BooleanField()
    target = TextField(null=True)
    target_index = IntegerField(null=True)
    target_name = TextField(null=True)
    time = FloatField(null=True)
    timestamp = DateTimeField(auto_now_add=True)
    tlb_entry = TextField(null=True)


class simics_register_diff(Model):
    checkpoint = IntegerField()
    config_object = TextField()
    gold_value = TextField()
    monitored_value = TextField()
    register = TextField()
    result = ForeignKey(result)


class simics_memory_diff(Model):
    checkpoint = IntegerField()
    block = TextField()
    image_index = IntegerField()
    result = ForeignKey(result)
