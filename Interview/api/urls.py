from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.InterviewScheduleView.as_view(), name='schedule'),
    path('cancelApplication/', views.CancelApplicationView.as_view(), name='cancel_application'),  # Fixed typo: cancell -> cancel
    path('schedules/', views.getShedulesView.as_view(), name='schedules'),
    path('interviewCall/', views.InterviewView.as_view(), name='makeInterview'),
    path('status/', views.InterviewStatusView.as_view(), name='status'),
    path('test/', views.testView, name='test'),
]