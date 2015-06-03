from django.db import models


class simics_results(models.Model):
    register = models.CharField(max_length=50)
    register_index = models.CharField(max_length=50)
    bit = models.IntegerField()
    outcome = models.CharField(max_length=50)
    qty = models.IntegerField()
