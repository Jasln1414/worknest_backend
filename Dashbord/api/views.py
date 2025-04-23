from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from user_account.models import User
from Empjob.models import Candidate, Employer, Jobs
from .serializer import CandidateDetailSerializer, EmployerDetailsSerializer, CandidateSerializer, EmployerSerializer, AdminJobSerializer

import logging

from Empjob.models import Jobs

logger = logging.getLogger(__name__)


from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db import DatabaseError
import logging


logger = logging.getLogger(__name__)


class EmployerApprovalView(APIView):
    permission_classes = [AllowAny]  # Add proper permissions like IsAdminUser in production

    def post(self, request):
        employer_id = request.data.get('id')
        action = request.data.get('action')  # 'approve' or 'reject'

        try:
            employer = Employer.objects.get(id=employer_id)
            if action == 'approve':
                employer.is_approved_by_admin = True
            elif action == 'reject':
                employer.is_approved_by_admin = False
            else:
                return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
            
            employer.save()
            return Response({"message": f"Employer {action}ed successfully!"}, status=status.HTTP_200_OK)
        except Employer.DoesNotExist:
            return Response({"error": "Employer not found"}, status=status.HTTP_404_NOT_FOUND)
class HomeView(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        candidates_count = Candidate.objects.count()
        employers_count = Employer.objects.count()
        jobs_count = Jobs.objects.filter(active=True).count()
        
        data = {
            'candidates_count': candidates_count,
            'employers_count': employers_count,
            'jobs_count': jobs_count,
            
        }
        return Response(data,status=status.HTTP_200_OK)

class CandidateListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        print("CandidateListView: Fetching all candidates...")
        candidates = Candidate.objects.all()
        serializer = CandidateSerializer(candidates, many=True)
        print(f"CandidateListView: Serialized data - {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        print("EmployerListView: Fetching all employers...")
        employers = Employer.objects.all()
        serializer = EmployerSerializer(employers, many=True)
        print(f"EmployerListView: Serialized data - {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)


class CandidateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        print(f"CandidateView: Fetching candidate with id {id}...")
        print(f"Candidate ID: {id}")  # Check if this prints in the terminal
        try:
            candidate = Candidate.objects.get(id=id)
            print(f"CandidateView: Candidate found - {candidate}")
            serializer = CandidateDetailSerializer(candidate)
            print(f"CandidateView: Serialized data - {serializer.data}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Candidate.DoesNotExist:
            logger.error(f"Candidate with id {id} not found")
            print(f"CandidateView: Candidate with id {id} not found")
            return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)


class EmployerView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        print(f"EmployerView: Fetching employer with id {id}...")
        try:
            employer = Employer.objects.get(id=id)
            print(f"EmployerView: Employer found - {employer}")
            serializer = EmployerDetailsSerializer(employer)
            print(f"EmployerView: Serialized data - {serializer.data}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Employer.DoesNotExist:
            logger.error(f"Employer with id {id} not found")
            print(f"EmployerView: Employer with id {id} not found")
            return Response({"error": "Employer not found"}, status=status.HTTP_404_NOT_FOUND)




from rest_framework.permissions import IsAuthenticated, IsAdminUser


class StatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        print("StatusView request data:", request.data)
        id = request.data.get('id')
        action = request.data.get('action')
        entity_type = request.data.get('type')

        if not id or not action or not entity_type:
            return Response({"error": "Missing required fields: id, action, or type"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if entity_type == "candidate":
                candidate = Candidate.objects.get(id=id)
                user = User.objects.get(id=candidate.user.id)
                entity_name = f"Candidate {id}"
            elif entity_type == "employer":
                employer = Employer.objects.get(id=id)
                user = User.objects.get(id=employer.user.id)
                entity_name = f"Employer {id}"
            else:
                return Response({"error": "Invalid type. Use 'candidate' or 'employer'"}, status=status.HTTP_400_BAD_REQUEST)

            print(f"Updating status for {entity_name}, User: {user}")
            if action == 'block':
                user.is_active = False
                user.save()
                print(f"{entity_name} blocked by {request.user}")
            elif action == 'unblock':
                user.is_active = True
                user.save()
                print(f"{entity_name} unblocked by {request.user}")
            else:
                return Response({"error": "Invalid action. Use 'block' or 'unblock'"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": f"{entity_name} status changed successfully"}, status=status.HTTP_200_OK)

        except Candidate.DoesNotExist:
            return Response({"error": f"Candidate with id {id} not found"}, status=status.HTTP_404_NOT_FOUND)
        except Employer.DoesNotExist:
            return Response({"error": f"Employer with id {id} not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "Associated user not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error in StatusView: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminGetAllJobs(APIView):
    permission_classes = [AllowAny]  # Adjust permissions as needed
    
    def get(self, request):
        try:
            # Get all jobs, with optional filters from query params
            jobs = Jobs.objects.all()
            
            # Allow filtering by active status if provided in query params
            active_status = request.query_params.get('active')
            if active_status is not None:
                active_status = active_status.lower() == 'true'
                jobs = jobs.filter(active=active_status)
                
            serializer = AdminJobSerializer(jobs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class AdminGetJobDetail(APIView):
    permission_classes = [AllowAny]  # Adjust permissions as needed
    
    def get(self, request, job_id):
        try:    
            job = Jobs.objects.get(id=job_id)
            serializer = AdminJobSerializer(job)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Jobs.DoesNotExist:
            return Response(
                {"error": "Job not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class AdminJobModeration(APIView):
    permission_classes = [AllowAny]  # Adjust permissions as needed
    
    def post(self, request, job_id):
        action = request.data.get('action')
        reason = request.data.get('reason', '')
        
        if action not in ['deactivate', 'activate', 'delete']:
            return Response(
                {"error": "Invalid action. Use 'activate', 'deactivate', or 'delete'."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            job = Jobs.objects.get(id=job_id)
            
            if action == 'deactivate':
                job.active = False
                job.moderation_note = reason
                job.save()
                message = "Job deactivated successfully"
            elif action == 'activate':
                job.active = True
                job.moderation_note = reason
                job.save()
                message = "Job activated successfully"
            elif action == 'delete':
                job.delete()
                message = "Job deleted successfully"
                
            # Return the updated job details (if not deleted)
            if action != 'delete':
                serializer = AdminJobSerializer(job)
                return Response({"message": message, "job": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"message": message}, status=status.HTTP_200_OK)
                
        except Jobs.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
from user_account.models import User
from Empjob.models import Candidate, Employer, Jobs


class UserGrowthReportView(APIView):
    """
    API to get user growth data over time.
    This returns daily counts of new candidates and employers.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get candidates data with date
        candidates_data = Candidate.objects.filter(
            user__date_joined__gte=start_date,
            user__date_joined__lte=end_date
        ).annotate(
            date=TruncDate('user__date_joined')
        ).values('date').annotate(
            candidate_count=Count('id')
        ).order_by('date')
        
        # Get employers data with date
        employers_data = Employer.objects.filter(
            user__date_joined__gte=start_date,
            user__date_joined__lte=end_date
        ).annotate(
            date=TruncDate('user__date_joined')
        ).values('date').annotate(
            employer_count=Count('id')
        ).order_by('date')
        
        # Create a dictionary for each date within the range
        date_range = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_range[date_str] = {
                'date': date_str,
                'candidate_count': 0,
                'employer_count': 0
            }
            current_date += timedelta(days=1)
        
        # Fill in candidate counts
        for item in candidates_data:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str in date_range:
                date_range[date_str]['candidate_count'] = item['candidate_count']
        
        # Fill in employer counts
        for item in employers_data:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str in date_range:
                date_range[date_str]['employer_count'] = item['employer_count']
        
        # Convert dict to list
        result = list(date_range.values())
        
        return Response(result, status=status.HTTP_200_OK)


class JobTrendsReportView(APIView):
    """
    API to get job posting trends over time.
    This returns daily counts of new jobs posted and active job count.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get job data with date
        jobs_data = Jobs.objects.filter(
            posted_date__gte=start_date,
            posted_date__lte=end_date
        ).annotate(
            date=TruncDate('posted_date')
        ).values('date').annotate(
            job_count=Count('id')
        ).order_by('date')
        
        # Get active job data with date
        active_jobs_data = Jobs.objects.filter(
            posted_date__gte=start_date,
            posted_date__lte=end_date,
            active=True
        ).annotate(
            date=TruncDate('posted_date')
        ).values('date').annotate(
            active_job_count=Count('id')
        ).order_by('date')
        
        # Create a dictionary for each date within the range
        date_range = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_range[date_str] = {
                'date': date_str,
                'job_count': 0,
                'active_job_count': 0
            }
            current_date += timedelta(days=1)
        
        # Fill in job counts
        for item in jobs_data:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str in date_range:
                date_range[date_str]['job_count'] = item['job_count']
        
        # Fill in active job counts
        for item in active_jobs_data:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str in date_range:
                date_range[date_str]['active_job_count'] = item['active_job_count']
        
        # Convert dict to list
        result = list(date_range.values())
        
        return Response(result, status=status.HTTP_200_OK)


class ApplicationStatsView(APIView):
    """
    API to get top jobs by application count.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # Get jobs with application counts
        application_stats = Jobs.objects.annotate(
            application_count=Count('jobapplication')
        ).filter(
            application_count__gt=0
        ).values(
            'id', 'title', 'application_count', 'company_name'
        ).order_by('-application_count')[:10]  # Top 10 jobs by application count
        
        # Rename 'title' to 'job_title' to match frontend expectations
        result = []
        for item in application_stats:
            result.append({
                'job_id': item['id'],
                'job_title': item['title'],
                'company_name': item['company_name'],
                'application_count': item['application_count']
            })
        
        return Response(result, status=status.HTTP_200_OK)