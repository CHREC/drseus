from django.db import models


class campaign_manager(models.Manager):
    def get_queryset(self):
        return super(campaign_manager, self).get_queryset().annotate(
            results=models.Count('result', distinct=True),
            last_injection=models.Max('result__injection__timestamp'))


class campaign(models.Model):
    campaign_number = models.IntegerField(primary_key=True)
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
    timestamp = models.DateTimeField()
    kill_dut = models.BooleanField()
    objects = campaign_manager()


class result(models.Model):
    campaign = models.ForeignKey(campaign)
    iteration = models.IntegerField()
    num_injections = models.IntegerField()
    outcome = models.TextField()
    outcome_category = models.TextField()
    data_diff = models.FloatField(null=True)
    detected_errors = models.IntegerField(null=True)
    dut_output = models.TextField(null=True)
    aux_output = models.TextField(null=True)
    debugger_output = models.TextField(null=True)
    paramiko_output = models.TextField(null=True)
    aux_paramiko_output = models.TextField(null=True)
    timestamp = models.DateTimeField()


class injection(models.Model):
    # commond fields
    result = models.ForeignKey(result)
    injection_number = models.IntegerField()
    timestamp = models.DateTimeField()
    register = models.TextField(null=True)
    bit = models.IntegerField(null=True)
    gold_value = models.TextField(null=True)
    injected_value = models.TextField(null=True)
    # hw fields
    time = models.FloatField(null=True)
    time_rounded = models.FloatField(null=True)
    core = models.IntegerField(null=True)
    # simics fields
    checkpoint_number = models.IntegerField(null=True)
    target_index = models.TextField(null=True)
    target = models.TextField(null=True)
    config_object = models.TextField(null=True)
    config_type = models.TextField(null=True)
    register_index = models.TextField(null=True)
    field = models.TextField(null=True)
    # gold_debug_info = models.TextField(null=True)


class simics_register_diff(models.Model):
    result = models.ForeignKey(result)
    checkpoint_number = models.IntegerField()
    config_object = models.TextField()
    register = models.TextField()
    gold_value = models.TextField()
    monitored_value = models.TextField()


class simics_memory_diff(models.Model):
    result = models.ForeignKey(result)
    checkpoint_number = models.IntegerField()
    image_index = models.IntegerField()
    block = models.TextField()
