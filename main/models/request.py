from django.db import models


class Fulfilment(models.Model):
    type = models.CharField(max_length=100)
    stops = models.TextField(blank=True, null=True)
    vehicle = models.TextField(blank=True, null=True)


class Item(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    descriptor = models.CharField(max_length=100)
    price = models.CharField(max_length=100)
    currency = models.CharField(max_length=100)
    quantity = models.CharField(max_length=100)
    unit = models.CharField(max_length=100)
    images = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    tags = models.CharField(max_length=100)
    metadata = models.CharField(max_length=100)
    fulfillment = models.ForeignKey('Fulfilment', on_delete=models.DO_NOTHING)


class Billing(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)


class Payment(models.Model):
    type = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    collected_by = models.CharField(max_length=100)
    params = models.JSONField(null=True, blank=True)
    billing = models.ForeignKey('Billing', on_delete=models.DO_NOTHING)
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING)


class CancellationTerms(models.Model):
    cancel_by = models.JSONField()
    cancellation_fee = models.JSONField()


class Order(models.Model):
    # order_id = models.CharField(max_length=100)
    items = models.OneToOneField('Item', on_delete=models.DO_NOTHING)
    # provider = models.ForeignKey('Provider', on_delete=models.DO_NOTHING)
    billing = models.ForeignKey('Billing', on_delete=models.DO_NOTHING)
    payments = models.ForeignKey('Payment', on_delete=models.DO_NOTHING)
    cancellation_terms = models.ForeignKey('CancellationTerms',
                                           on_delete=models.DO_NOTHING, null=True,
                                           blank=True)
