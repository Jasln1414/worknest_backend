from django.db import models
from user_account.models import Employer,Candidate
from django.utils import timezone
# Create your models here.

class Jobs(models.Model):
    title = models.CharField(max_length=60, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    lpa = models.CharField(max_length=20, blank=True, null=True)
    jobtype = models.CharField(max_length=30, blank=True, null=True)
    jobmode = models.CharField(max_length=30, blank=True, null=True)
    experience = models.CharField(max_length=50)
    applyBefore = models.DateField(blank=True, null=True)
    posteDate = models.DateTimeField(auto_now_add=True)  # Tracks job creation
    about = models.TextField(blank=True, null=True)
    responsibility = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    industry = models.CharField(blank=True, null=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="employer_jobs")

    def __str__(self):
        return self.title or f"Job {self.id}"



class SavedJobs(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('candidate', 'job')  # Optional: Prevents duplicate saves

    def __str__(self):
        return f"{self.candidate} saved {self.job}"


class ApplyedJobs(models.Model):
    choice = (
         ("Application Send", "Application Send"),
        ("Application Viewed", "Application Viewed"),
        ("Resume Viewed", "Resume Viewed"),
        ("Pending", "Pending"),
        ("ShortListed", "ShortListed"),
        ("Interview Scheduled", "Interview Scheduled"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
    )
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=choice, default="Application Send")
    applyed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('candidate', 'job')  

    def __str__(self):
        return f"{self.candidate} - {self.job}"
    


    
class Approvals(models.Model):
    candidate= models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="approvals")
    employer= models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="approvals")
    job= models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name="approvals")
    is_approved= models.BooleanField(default=False)
    is_requested = models.BooleanField(default=False)
    is_rejected= models.BooleanField(default=False)
    requested_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.candidate.user.full_name} - {self.employer.user.full_name} - {self.job.id} - {self.is_approved}"




class Question(models.Model):
    QUESTION_TYPES = (
        ('TEXT', 'Text Answer'),
        ('MCQ', 'Multiple Choice'),
        ('CODE', 'Code Answer'),
    )
    
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()  # The question itself
    question_type = models.CharField(max_length=4, choices=QUESTION_TYPES, default='TEXT')
    options = models.JSONField(null=True, blank=True)  # For MCQs, store options as JSON
    
    def __str__(self):
        return self.text[:50]

class Answer(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    question_text = models.TextField(null=True, blank=True)
