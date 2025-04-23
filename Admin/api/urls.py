# from django.urls import path
# from .views import *

# urlpatterns = [
    
#     path('home/',HomeView.as_view(),name='home'),
#     path('candidate/<int:id>', CandidateView.as_view(), name='candidate-detail'),
#     path('employer/<int:id>',EmployerView.as_view(),name='employer'),
#     path('clist/',CandidateListView.as_view(),name='candidatelist'),
#     path('elist/',EmployerListView.as_view(),name='employerlist'),
#     path('api/employer/approval/', EmployerApprovalView.as_view(), name='employer-approval'),
#     path('status/', StatusView.as_view(), name='status'), 
    
#     path('admin/jobs/', AdminGetAllJobs.as_view(), name='admin-get-all-jobs'),
#     path('admin/jobs/<int:job_id>/', AdminGetJobDetail.as_view(), name='admin-get-job-detail'),
#     path('admin/jobs/<int:job_id>/moderate/', AdminJobModeration.as_view(), name='admin-job-mode')

   
    

# ]



from django.urls import path
from .views import (HomeView, CandidateView, EmployerView, CandidateListView,
                    EmployerListView, EmployerApprovalView, StatusView,
                    AdminGetAllJobs, AdminGetJobDetail, AdminJobModeration,
                    get_csrf_token)
from views import UserGrowthReportView, JobTrendReportView, ApplicationStatsReportView

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('candidate/<int:id>', CandidateView.as_view(), name='candidate-detail'),
    path('employer/<int:id>', EmployerView.as_view(), name='employer'),
    path('clist/', CandidateListView.as_view(), name='candidatelist'),
    path('elist/', EmployerListView.as_view(), name='employerlist'),
    path('api/employer/approval/', EmployerApprovalView.as_view(), name='employer-approval'),
    path('status/', StatusView.as_view(), name='status'),
    path('admin/jobs/', AdminGetAllJobs.as_view(), name='admin-get-all-jobs'),
    path('admin/jobs/<int:job_id>/', AdminGetJobDetail.as_view(), name='admin-get-job-detail'),
    path('admin/jobs/<int:job_id>/moderate/', AdminJobModeration.as_view(), name='admin-job-mode'),
    path('csrf-token/', get_csrf_token, name='csrf-token'),
    path('reports/user-growth/', UserGrowthReportView.as_view(), name='user-growth-report'),
    path('reports/job-trends/', JobTrendReportView.as_view(), name='job-trends-report'),
    path('reports/application-stats/', ApplicationStatsReportView.as_view(), name='application-stats-report'),
]