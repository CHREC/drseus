from django.contrib.postgres.fields import ArrayField
from django.db.models import (BooleanField, BigIntegerField, DateTimeField,
                              FloatField, ForeignKey, IntegerField, Model,
                              NullBooleanField, TextField)


class campaign(Model):
    aux = BooleanField()
    architecture = TextField()
    aux_command = TextField(null=True)
    aux_output = TextField(null=True)
    checkpoints = IntegerField(null=True)
    command = TextField()
    cycles = BigIntegerField(null=True)
    cycles_between = BigIntegerField(null=True)
    debugger_output = TextField(null=True)
    description = TextField(null=True)
    dut_output = TextField(null=True)
    execution_time = FloatField(null=True)
    kill_dut = BooleanField()
    output_file = TextField()
    rsakey = TextField()
    simics = BooleanField()
    start_cycle = BigIntegerField(null=True)
    start_time = FloatField(null=True)
    timestamp = DateTimeField()
    aux_output_file = BooleanField()


class result(Model):
    aux_output = TextField(null=True)
    aux_serial_port = TextField(null=True)
    campaign = ForeignKey(campaign)
    returned = NullBooleanField()
    cycles = BigIntegerField(null=True)
    data_diff = FloatField(null=True)
    debugger_output = TextField(null=True)
    detected_errors = IntegerField(null=True)
    dut_output = TextField(null=True)
    dut_serial_port = TextField(null=True)
    execution_time = FloatField(null=True)
    num_injections = IntegerField(null=True)
    outcome = TextField()
    outcome_category = TextField()
    timestamp = DateTimeField()


class event(Model):
    campaign = ForeignKey(campaign, null=True)
    description = TextField(null=True)
    level = TextField()
    result = ForeignKey(result, null=True)
    source = TextField()
    success = NullBooleanField()
    timestamp = DateTimeField()
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
    time = FloatField(null=True)
    timestamp = DateTimeField(null=True)


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
