from django.db import models


class campaign(models.Model):
    architecture = models.TextField()
    aux_command = models.TextField(null=True)
    aux_output = models.TextField(null=True)
    command = models.TextField()
    cycles_between = models.IntegerField(null=True)
    debugger_output = models.TextField(null=True)
    description = models.TextField(null=True)
    dut_output = models.TextField(null=True)
    exec_time = models.FloatField(null=True)
    kill_dut = models.BooleanField()
    num_checkpoints = models.IntegerField(null=True)
    num_cycles = models.IntegerField(null=True)
    output_file = models.TextField()
    rsakey = models.TextField()
    sim_time = models.FloatField(null=True)
    timestamp = models.DateTimeField()
    use_aux = models.BooleanField()
    use_aux_output = models.BooleanField()
    use_simics = models.BooleanField()


class result(models.Model):
    aux_output = models.TextField(null=True)
    aux_serial_port = models.TextField(null=True)
    campaign = models.ForeignKey(campaign)
    data_diff = models.FloatField(null=True)
    debugger_output = models.TextField(null=True)
    detected_errors = models.IntegerField(null=True)
    dut_output = models.TextField(null=True)
    dut_serial_port = models.TextField(null=True)
    num_injections = models.IntegerField()
    outcome = models.TextField()
    outcome_category = models.TextField()
    timestamp = models.DateTimeField()


class event(models.Model):
    campaign = models.ForeignKey(campaign, null=True)
    description = models.TextField(null=True)
    event_type = models.TextField()
    level = models.TextField()
    result = models.ForeignKey(result, null=True)
    source = models.TextField()
    timestamp = models.DateTimeField()


class injection(models.Model):
    bit = models.IntegerField(null=True)
    checkpoint_number = models.IntegerField(null=True)
    config_object = models.TextField(null=True)
    field = models.TextField(null=True)
    gold_value = models.TextField(null=True)
    injected_value = models.TextField(null=True)
    injection_number = models.IntegerField()
    register = models.TextField(null=True)
    register_index = models.TextField(null=True)
    result = models.ForeignKey(result)
    success = models.NullBooleanField()
    target = models.TextField(null=True)
    target_index = models.TextField(null=True)
    time = models.FloatField(null=True)
    timestamp = models.DateTimeField(null=True)


class simics_register_diff(models.Model):
    checkpoint_number = models.IntegerField()
    config_object = models.TextField()
    gold_value = models.TextField()
    monitored_value = models.TextField()
    register = models.TextField()
    result = models.ForeignKey(result)


class simics_memory_diff(models.Model):
    checkpoint_number = models.IntegerField()
    block = models.TextField()
    image_index = models.IntegerField()
    result = models.ForeignKey(result)
