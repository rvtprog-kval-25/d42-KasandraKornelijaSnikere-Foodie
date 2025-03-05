from django.db import models


class Authentication(models.Model):
    ID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40)
    lastname = models.CharField(max_length=40)
    email = models.EmailField(max_length=40)
    password = models.CharField(max_length=50)

    def __str__(self):
        return self.Authentication_text


class User_Parametres(models.Model):
    ParametresID = models.AutoField(primary_key=True)
    Sex = models.IntegerField()  # 1 for Male, 2 for Female
    Height = models.FloatField()
    Weight = models.FloatField()
    Goal = models.IntegerField()  # This could be an enum or choices if there are specific goals
    Activity = models.IntegerField()  # This could also be an enum or choices
    DateTime = models.DateField()
    UserID = models.ForeignKey(Authentication, on_delete=models.CASCADE)


class Food(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    calories = models.FloatField()
    search_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Authentication, on_delete=models.CASCADE)


    def __str__(self):
        return self.Food_text
