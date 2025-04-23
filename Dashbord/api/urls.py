

from django.urls import path
from .views import (
    HomeView, CandidateListView, EmployerListView, 
    CandidateView, EmployerView, StatusView, EmployerApprovalView,
    AdminGetAllJobs, AdminGetJobDetail, AdminJobModeration,
    # Add these new report views
    UserGrowthReportView, JobTrendsReportView, ApplicationStatsView
)

urlpatterns = [
    # Existing URLs
    path('home/', HomeView.as_view(), name='home'),
    path('candidate/<int:id>', CandidateView.as_view(), name='candidate-detail'),
    path('employer/<int:id>', EmployerView.as_view(), name='employer'),
    path('clist/', CandidateListView.as_view(), name='candidatelist'),
    path('elist/', EmployerListView.as_view(), name='employerlist'),
    path('api/employer/approval/', EmployerApprovalView.as_view(), name='employer-approval'),
    path('status/', StatusView.as_view(), name='status'),
    path('admin/jobs/', AdminGetAllJobs.as_view(), name='admin-get-all-jobs'),
    
    # New report endpoints
    path('reports/user-growth/', UserGrowthReportView.as_view(), name='user-growth-report'),
    path('reports/job-trends/', JobTrendsReportView.as_view(), name='job-trends-report'),
    path('reports/application-stats/', ApplicationStatsView.as_view(), name='application-stats'),
]