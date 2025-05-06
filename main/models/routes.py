# from django.db import models
# from main.models.managers import RouteMultiDbManager

# class Route(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     route_id = models.IntegerField(blank=True, null=True)
#     route_long_name = models.TextField(blank=True, null=True)
#     agency = models.TextField(blank=True, null=True)
#     stop_details = models.TextField(blank=True, null=True)
#     is_ac = models.IntegerField(blank=True, null=True)
#     fare_matrix = models.TextField(blank=True, null=True)

#     objects = RouteMultiDbManager()

#     class Meta:
#         managed = False
#         db_table = 'all_routes'
#         verbose_name = 'Route'
#         verbose_name_plural = 'Routes'


# class Stop(models.Model):
#     route = models.IntegerField(blank=True, null=True)
#     stop_name = models.CharField(max_length=255, blank=True, null=True)
#     stop_pos = models.IntegerField(blank=True, null=True)

#     def __str__(self):
#         return self.stop_name
