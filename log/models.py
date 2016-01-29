from django.db.models import (BooleanField, DateTimeField, FloatField,
                              ForeignKey, IntegerField, Model, NullBooleanField,
                              TextField)


class campaign(Model):
    aux = BooleanField()
    architecture = TextField()
    aux_command = TextField(null=True)
    aux_output = TextField(null=True)
    command = TextField()
    cycles_between = IntegerField(null=True)
    debugger_output = TextField(null=True)
    description = TextField(null=True)
    dut_output = TextField(null=True)
    exec_time = FloatField(null=True)
    kill_dut = BooleanField()
    num_checkpoints = IntegerField(null=True)
    num_cycles = IntegerField(null=True)
    output_file = TextField()
    rsakey = TextField()
    sim_time = FloatField(null=True)
    simics = BooleanField()
    timestamp = DateTimeField()
    use_aux_output = BooleanField()


class result(Model):
    aux_output = TextField(null=True)
    aux_serial_port = TextField(null=True)
    campaign = ForeignKey(campaign)
    data_diff = FloatField(null=True)
    debugger_output = TextField(null=True)
    detected_errors = IntegerField(null=True)
    dut_output = TextField(null=True)
    dut_serial_port = TextField(null=True)
    num_injections = IntegerField(null=True)
    outcome = TextField()
    outcome_category = TextField()
    timestamp = DateTimeField()


class event(Model):
    campaign = ForeignKey(campaign, null=True)
    description = TextField(null=True)
    event_type = TextField()
    level = TextField()
    result = ForeignKey(result, null=True)
    source = TextField()
    timestamp = DateTimeField()


class injection(Model):
    bit = IntegerField(null=True)
    checkpoint_number = IntegerField(null=True)
    config_object = TextField(null=True)
    field = TextField(null=True)
    gold_value = TextField(null=True)
    injected_value = TextField(null=True)
    injection_number = IntegerField()
    processor_mode = TextField(null=True)
    register = TextField(null=True)
    register_access = TextField(null=True)
    register_index = TextField(null=True)
    result = ForeignKey(result)
    success = NullBooleanField()
    target = TextField(null=True)
    target_index = TextField(null=True)
    time = FloatField(null=True)
    timestamp = DateTimeField(null=True)


class simics_register_diff(Model):
    checkpoint_number = IntegerField()
    config_object = TextField()
    gold_value = TextField()
    monitored_value = TextField()
    register = TextField()
    result = ForeignKey(result)


class simics_memory_diff(Model):
    checkpoint_number = IntegerField()
    block = TextField()
    image_index = IntegerField()
    result = ForeignKey(result)
