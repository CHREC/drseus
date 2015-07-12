from django.db import models


class campaign_data(models.Model):
    application = models.TextField()
    output_file = models.TextField()
    command = models.TextField()
    aux_command = models.TextField()
    use_aux_output = models.BooleanField()
    exec_time = models.FloatField()
    architecture = models.TextField()
    use_simics = models.BooleanField()
    use_aux = models.BooleanField()
    dut_output = models.TextField()
    aux_output = models.TextField()
    debugger_output = models.TextField()
    paramiko_output = models.TextField()
    aux_paramiko_output = models.TextField()
    num_cycles = models.IntegerField()
    num_checkpoints = models.IntegerField()
    cycles_between = models.IntegerField()


class hw_injection(models.Model):
    # commond fields
    injection_number = models.IntegerField(primary_key=True)
    register = models.TextField()
    bit = models.IntegerField()
    gold_value = models.TextField()
    injected_value = models.TextField()
    # hw fields
    time = models.FloatField()
    time_rounded = models.FloatField()
    core = models.IntegerField()


class hw_result(models.Model):
    # common fields
    injection = models.OneToOneField(hw_injection, primary_key=True)
    outcome = models.TextField()
    outcome_category = models.TextField()
    data_diff = models.FloatField()
    detected_errors = models.IntegerField()
    dut_output = models.TextField()
    aux_output = models.TextField()
    debugger_output = models.TextField()
    paramiko_output = models.TextField()
    aux_paramiko_output = models.TextField()


class simics_injection(models.Model):
    # commond fields
    injection_number = models.IntegerField(primary_key=True)
    register = models.TextField()
    bit = models.IntegerField()
    gold_value = models.TextField()
    injected_value = models.TextField()
    # simics fields
    checkpoint_number = models.IntegerField()
    target_index = models.TextField()
    target = models.TextField()
    config_object = models.TextField()
    config_type = models.TextField()
    register_index = models.TextField()
    field = models.TextField()
    # gold_debug_info = models.TextField()


class simics_result(models.Model):
    # common fields
    injection = models.OneToOneField(simics_injection, primary_key=True)
    outcome = models.TextField()
    outcome_category = models.TextField()
    data_diff = models.FloatField()
    detected_errors = models.IntegerField()
    qty = models.IntegerField()
    dut_output = models.TextField()
    aux_output = models.TextField()
    debugger_output = models.TextField()
    paramiko_output = models.TextField()
    aux_paramiko_output = models.TextField()


class simics_register_diff(models.Model):
    injection = models.ForeignKey(simics_result)
    monitored_checkpoint_number = models.IntegerField()
    config_object = models.TextField()
    register = models.TextField()
    gold_value = models.TextField()
    monitored_value = models.TextField()


class simics_memory_diff(models.Model):
    injection = models.ForeignKey(simics_result)
    monitored_checkpoint_number = models.IntegerField()
    image_index = models.IntegerField()
    block = models.TextField()


class supervisor_result(models.Model):
    # TODO: add times
    iteration = models.IntegerField(primary_key=True)
    outcome = models.TextField()
    outcome_category = models.TextField()
    data_diff = models.FloatField()
    detected_errors = models.IntegerField()
    dut_output = models.TextField()
    aux_output = models.TextField()
    paramiko_output = models.TextField()
    aux_paramiko_output = models.TextField()
