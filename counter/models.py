from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User

class WeightEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)  # <-- Updated here

    def __str__(self):
        return f"{self.user.username} - {self.weight} kg on {self.date}"

class UserParametres(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sex = models.IntegerField()  # 1 = Male, 2 = Female
    height = models.FloatField()
    weight = models.FloatField()
    goal = models.IntegerField()
    target_weight = models.FloatField(null=True, blank=True)
    activity = models.IntegerField()
    date_time = models.DateField()
    age = models.IntegerField()


class Food(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    calories = models.FloatField()
    search_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Use Django's built-in User here
    carbohydrates = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    fiber = models.FloatField(default=0)

    def __str__(self):
        return f"{self.name} ({self.calories} cal)"