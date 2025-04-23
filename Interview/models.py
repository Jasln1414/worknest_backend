# from django.db import models

# # Create your models here.


# from django.db import models
# from user_account.models import *
# from Empjob.models import *
# # Create your models here.

# class InterviewShedule(models.Model):
#     choice={
#         ("Upcoming","Upcoming"),
#         ("Selected","Selected"),
#         ("Canceled","Canceled"),
#         ("Rejected","Rejected"),
#         ("You missed","You missed")
#     }
#     candidate = models.ForeignKey(Candidate, on_delete = models.CASCADE,related_name="candidate")
#     employer = models.ForeignKey(Employer, on_delete = models.CASCADE,related_name="employer")
#     job = models.ForeignKey(Jobs, on_delete = models.CASCADE,related_name="job")
#     date = models.DateTimeField()
#     selected = models.BooleanField(default=False)
#     active = models.BooleanField(default=True)
#     status = models.CharField(max_length=20,choices=choice, default="Upcoming")
# Interview/models.py
from django.db import models
from user_account.models import *
from Empjob.models import *

class InterviewShedule(models.Model):
    STATUS_CHOICES = (
        ("Upcoming","Upcoming"),
        ("Selected","Selected"),
        ("Canceled","Canceled"),
        ("Rejected","Rejected"),
        ("You missed","You missed")
    )
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE)
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE)
    date = models.DateTimeField()
    selected = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Upcoming")
    notification_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.job.title} - {self.candidate.user.email}"