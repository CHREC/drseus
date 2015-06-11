from django.db import models


class campaign_data(models.Model):
    application = models.TextField()
    output_file = models.TextField()
    command = models.TextField()
    exec_time = models.FloatField()
    architecture = models.TextField()
    simics = models.BooleanField()


class simics_campaign_data(models.Model):
    board = models.TextField()
    num_checkpoints = models.IntegerField()
    cycles_between = models.IntegerField()
    dut_output = models.TextField()
    debugger_output = models.TextField()


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
    register_index = models.TextField()
    field = models.TextField()
    # gold_debug_info = models.TextField()


class hw_injection(models.Model):
    # commond fields
    injection_number = models.IntegerField(primary_key=True)
    register = models.TextField()
    bit = models.IntegerField()
    gold_value = models.TextField()
    injected_value = models.TextField()
    # hw fields
    time = models.FloatField()
    core = models.IntegerField()


class simics_register_diff(models.Model):
    injection_number = models.IntegerField()
    monitored_checkpoint_number = models.IntegerField()
    config_object = models.TextField()
    register = models.TextField()
    gold_value = models.TextField()
    monitored_value = models.TextField()


class simics_result(models.Model):
    # common fields
    injection = models.OneToOneField(simics_injection, primary_key=True)
    outcome = models.TextField()
    outcome_category = models.TextField()
    data_diff = models.FloatField()
    detected_errors = models.IntegerField()
    qty = models.IntegerField()
    dut_output = models.TextField()
    debugger_output = models.TextField()


class hw_result(models.Model):
    # common fields
    injection = models.OneToOneField(hw_injection, primary_key=True)
    outcome = models.TextField()
    outcome_category = models.TextField()
    data_diff = models.FloatField()
    detected_errors = models.IntegerField()
    qty = models.IntegerField()
    dut_output = models.TextField()
    debugger_output = models.TextField()
