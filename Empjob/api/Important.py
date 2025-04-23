# # Standard library imports
# import logging

# # Django imports
# from django.http import JsonResponse
# from django.middleware.csrf import get_token
# from django.db.models import Q
# from django.conf import settings
# from django.views.decorators.csrf import ensure_csrf_cookie
# # views.py
# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, permission_classes

# from .serializer import *

# logger = logging.getLogger(__name__)
# # DRF imports
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework import status, generics
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.pagination import PageNumberPagination

# # Third-party imports
# import razorpay
# from django_filters import rest_framework as filters
# from django_filters.rest_framework import DjangoFilterBackend

# # Local imports
# from .serializer import *
# from user_account.models import *
# from Empjob.models import *
# from payment.models import *

# logger = logging.getLogger(__name__)
# razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
# from django.middleware.csrf import get_token
# from django.http import JsonResponse

# def csrf_token_view(request):
#     token = get_token(request)
#     return JsonResponse({'csrfToken': token})

# # Utility Views
# @ensure_csrf_cookie
# def get_csrf_token(request):
#     return JsonResponse({'csrfToken': get_token(request)})



# class PostJob(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         try:
#             user = request.user
#             if user.user_type != 'employer':
#                 return Response({"error": "Only employers can post jobs"}, status=status.HTTP_403_FORBIDDEN)
            
#             employer = Employer.objects.get(user=user)
#             job_count = Jobs.objects.filter(employer=employer).count()
            
#             # Check for active subscription
#             active_subscription = EmployerSubscription.objects.filter(
#                 employer=employer, 
#                 status='active',
#                 end_date__gt=timezone.now()
#             ).first()
            
#             # If no active subscription or job limit reached
#             if not active_subscription:
#                 return Response({
#                     "error": "No active subscription found",
#                     "subscription_required": True,
#                     "message": "Please subscribe to post jobs"
#                 }, status=status.HTTP_402_PAYMENT_REQUIRED)
            
#             # If job limit reached based on subscription plan
#             if job_count >= active_subscription.plan.job_limit:
#                 # For unlimited plans (job_limit = 9999)
#                 if active_subscription.plan.job_limit == 9999:
#                     pass  # Allow posting, no limit
#                 else:
#                     # Check if payment for additional job is provided
#                     if 'razorpay_payment_id' not in request.data:
#                         order = razorpay_client.order.create({
#                             "amount": 200 * 100,  # Additional job posting fee
#                             "currency": "INR",
#                             "payment_capture": 1
#                         })
#                         return Response({
#                             "payment_required": True,
#                             "message": f"You've reached your plan limit of {active_subscription.plan.job_limit} jobs. Payment required for additional job posting.",
#                             "order_id": order['id'],
#                             "amount": order['amount'],
#                             "key": settings.RAZORPAY_KEY_ID
#                         }, status=status.HTTP_402_PAYMENT_REQUIRED)
                    
#                     # Verify the payment
#                     payment_id = request.data['razorpay_payment_id']
#                     if not Payment.objects.filter(
#                         transaction_id=payment_id,
#                         employer=employer,
#                         status='success'
#                     ).exists():
#                         return Response({"error": "Invalid or unverified payment"}, status=status.HTTP_400_BAD_REQUEST)
            
#             # Process the job posting
#             serializer = PostJobSerializer(data=request.data, context={'employer': employer})
#             if serializer.is_valid():
#                 job = serializer.save()
                
#                 # Log the job creation with subscription info
#                 logger.info(f"Job posted by employer {employer.id} with subscription {active_subscription.id if active_subscription else 'None'}")
                
#                 return Response({"message": "Job posted successfully"}, status=status.HTTP_201_CREATED)
            
#             logger.error(f"Serializer errors: {serializer.errors}")
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         except Employer.DoesNotExist:
#             return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Unexpected error in PostJob: {str(e)}")
#             return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# from django.utils import timezone
 

# def get_employer_job_usage(employer):
#     """
#     Get job usage statistics for an employer
    
#     Returns:
#         dict: Contains job count, subscription info, and remaining job slots
#     """
#     # Get current active subscription
#     active_subscription = EmployerSubscription.objects.filter(
#         employer=employer,
#         status='active',
#         end_date__gt=timezone.now()
#     ).first()
    
#     # Count jobs posted by the employer
#     job_count = Jobs.objects.filter(employer=employer).count()
    
#     # Default values if no active subscription
#     remaining_jobs = 0
#     plan_name = None
#     plan_limit = 0
    
#     if active_subscription:
#         plan_name = active_subscription.plan.get_name_display()
#         plan_limit = active_subscription.plan.job_limit
        
#         # Calculate remaining job slots
#         if plan_limit == 9999:  # Unlimited
#             remaining_jobs = "Unlimited"
#         else:
#             remaining_jobs = max(0, plan_limit - job_count)
    
#     return {
#         "job_count": job_count,
#         "has_active_subscription": bool(active_subscription),
#         "subscription_plan": plan_name,
#         "job_limit": plan_limit,
#         "remaining_jobs": remaining_jobs,
#         "subscription_end_date": active_subscription.end_date if active_subscription else None
#     }



# class JobUsageView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         logger.info("JobUsageView endpoint hit!")
#         try:
#             user = request.user
#             if not hasattr(user, 'user_type') or user.user_type != 'employer':
#                 return Response({"error": "Only employers can access this information"}, status=status.HTTP_403_FORBIDDEN)

#             employer = Employer.objects.get(user=user)
#             subscription = EmployerSubscription.objects.filter(
#                 employer=employer, status="active", end_date__gt=timezone.now()
#             ).order_by('-start_date').first()
#             job_count = Jobs.objects.filter(employer=employer, active=True).count()

#             if subscription:
#                 # Use the subscription's job_limit consistently
#                 job_limit = subscription.job_limit
#                 remaining_jobs = "Unlimited" if job_limit == 9999 else max(0, job_limit - job_count)
#                 usage_stats = {
#                     "job_count": job_count,
#                     "has_active_subscription": True,
#                     "subscription_plan": subscription.plan.name,
#                     "job_limit": job_limit,
#                     "remaining_jobs": remaining_jobs,
#                     "subscription_end_date": subscription.end_date.isoformat()
#                 }
#             else:
#                 usage_stats = {
#                     "job_count": job_count,
#                     "has_active_subscription": False,
#                     "subscription_plan": None,
#                     "job_limit": 0,
#                     "remaining_jobs": 0,
#                     "subscription_end_date": None
#                 }

#             logger.info(f"Returning usage stats: {usage_stats}")
#             return Response(usage_stats, status=status.HTTP_200_OK)
#         except Employer.DoesNotExist:
#             return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Error in JobUsageView: {str(e)}")
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# class EditJob(APIView):
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         jobId = request.data.get("jobId")
#         try:
#             job = Jobs.objects.get(id=jobId)
#         except Jobs.DoesNotExist:
#             return Response({"message":"something went wrong"}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        
#         serializer = PostJobSerializer(instance=job, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(status=status.HTTP_400_BAD_REQUEST)

# class ProfileView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         try:
#             candidate = Candidate.objects.get(user=user)
#             serializer = CandidateSerializer(candidate, context={'request': request})
#             return Response({
#                 'user_type': 'candidate',
#                 'data': serializer.data
#             }, status=status.HTTP_200_OK)
#         except Candidate.DoesNotExist:
#             try:
#                 employer = Employer.objects.get(user=user)
#                 serializer = EmployerSerializer(employer, context={'request': request})
#                 return Response({
#                     'user_type': 'employer',
#                     'data': serializer.data
#                 }, status=status.HTTP_200_OK)
#             except Employer.DoesNotExist:
#                 return Response({
#                     "message": "User profile not found",
#                     "detail": "No candidate or employer profile exists for this user"
#                 }, status=status.HTTP_404_NOT_FOUND)

# class GetJob(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         user = request.user
#         try:
#             employer = Employer.objects.get(user=user)
#             jobs = Jobs.objects.filter(employer=employer)
#             serializer = JobSerializer(jobs, many=True)
#             data = {
#                 "data": serializer.data
#             }
#             return Response(data, status=status.HTTP_200_OK)
#         except Employer.DoesNotExist:
#             return Response({"error": "Employer not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class GetAllJob(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             # Check if the user is an employer
#             if request.user.user_type == "employer":
#                 # Fetch the employer instance linked to the user
#                 employer = Employer.objects.get(user=request.user)
#                 # Filter jobs by the employer
#                 jobs = Jobs.objects.filter(employer=employer)
#             else:
#                 # User is a candidate or admin: return all jobs
#                 jobs = Jobs.objects.all()

#             serializer = JobSerializer(jobs, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Employer.DoesNotExist:
#             return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class GetJobDetail(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request, job_id):
#         try:
#             # Get the job with related employer data
#             job = Jobs.objects.select_related('employer', 'employer__user').get(id=job_id)
            
#             # Pass the request to serializer for absolute URLs
#             serializer = JobSerializer(job, context={'request': request})
            
#             return Response(serializer.data, status=status.HTTP_200_OK)
            
#         except Jobs.DoesNotExist:
#             return Response(
#                 {"error": "Job not found"}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             logger.error(f"Error in GetJobDetail: {str(e)}", exc_info=True)
#             return Response(
#                 {"error": "An error occurred while fetching job details"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

# class GetApplyedjob(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         try:
#             candidate = Candidate.objects.get(user=user)
#             applied_jobs = ApplyedJobs.objects.filter(candidate=candidate)
#             serializer = ApplyedJobSerializer(applied_jobs, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Candidate.DoesNotExist:
#             return Response({"message": "Candidate not found"}, status=404)
#         except Exception as e:
#             return Response({"message": str(e)}, status=500)
        
# class ApproveChatRequestView(APIView):
#     # permission_classes = [IsAuthenticated]

#     def post(self, request, approve_id):
#         return Response({"message": "Chat request approved"}, status=status.HTTP_200_OK)

# class GetApplicationjob(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         user = request.user
#         try:
#             employer = Employer.objects.get(user=user)
#             jobs = Jobs.objects.filter(employer=employer, active=True)
#             serializer = ApplicationSerializer(jobs, many=True)
#             return Response({'data': serializer.data}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# from django_filters import rest_framework as filters
# from django.db.models import Q
# from rest_framework import generics
# from rest_framework.pagination import PageNumberPagination
# from Empjob.models import Jobs
# from Empjob.api.serializer import JobSerializer
# from django.utils import timezone
# from datetime import timedelta

# class StandardResultsSetPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100

# class JobFilter(filters.FilterSet):
#     """
#     FilterSet for Jobs model with enhanced filtering capabilities.
    
#     Filtering supported for:
#     - Search: title, about, responsibility, skills
#     - Location: exact match and fuzzy match with priority
#     - Job type: full-time, part-time, etc.
#     - Job mode: remote, on-site, hybrid (prefix-based)
#     - Experience: from internship to senior level
#     - Salary range (LPA): custom ranges with min-max
#     - Active status: only show active listings
#     - Industry: specific industry sectors
#     - Posted date: filter by recency
#     """
#     search = filters.CharFilter(method='filter_search', label='Search')
#     location = filters.CharFilter(method='filter_location', label='Location')
#     jobtype = filters.CharFilter(lookup_expr='iexact', label='Job Type')
#     jobmode = filters.CharFilter(method='filter_jobmode', label='Job Mode')
#     experience = filters.CharFilter(lookup_expr='iexact', label='Experience')
#     lpa = filters.CharFilter(method='filter_lpa', label='Salary Range (e.g., 10-20)')
#     employer = filters.NumberFilter(field_name='employer__id', label='Employer ID')
#     industry = filters.CharFilter(lookup_expr='icontains', label='Industry')
#     active = filters.BooleanFilter(field_name='active', label='Active Jobs Only')
#     recent = filters.CharFilter(method='filter_recent', label='Recent Jobs')
#     skills = filters.CharFilter(method='filter_skills', label='Required Skills')
    
#     class Meta:
#         model = Jobs
#         fields = ['search', 'location', 'jobtype', 'jobmode', 'experience', 
#                  'lpa', 'employer', 'industry', 'active', 'recent', 'skills']
    
#     def filter_search(self, queryset, name, value):
#         """
#         Enhanced search across multiple job fields with keyword relevance.
        
#         Searches title, about, responsibility, and employer name with weighting
#         to prioritize more relevant results.
#         """
#         if not value:
#             return queryset
            
#         # Split search terms for better matching
#         search_terms = value.split()
#         query = Q()
        
#         for term in search_terms:
#             # Build complex query with priority weighting
#             query |= (
#                 Q(title__icontains=term) |  
#                 Q(about__icontains=term) | 
#                 Q(responsibility__icontains=term) | 
#                 Q(employer__name__icontains=term)
#             )
            
#         return queryset.filter(query).distinct()
    
#     def filter_location(self, queryset, name, value):
#         """
#         Intelligent location filtering with multiple fallback mechanisms.
        
#         Implements a cascading match system:
#         1. Exact match (highest priority)
#         2. Case-insensitive exact match
#         3. Word boundary match
#         4. Contains match
#         5. Special handling for "Remote" keyword
#         """
#         if not value:
#             return queryset
        
#         # Normalize the input for comparison
#         value_lower = value.lower().strip()
        
#         # Special case for "remote" - check both location and jobmode
#         if value_lower == "remote":
#             return queryset.filter(
#                 Q(location__iexact="remote") | 
#                 Q(jobmode__iexact="remote")
#             )
        
#         # Try exact match first (highest priority)
#         exact_match = queryset.filter(location__iexact=value)
#         if exact_match.exists():
#             return exact_match
            
#         # Try contains match for partial location names
#         return queryset.filter(location__icontains=value)
    
#     def filter_jobmode(self, queryset, name, value):
#         """
#         Filter jobs by jobmode using a prefix-based approach.
        
#         Uses the first 3 letters of the filter value for prefix matching,
#         e.g., "Rem" matches "Remote", "remote work", etc.
#         """
#         if not value:
#             return queryset
#         # Use the first 3 letters of the filter value for prefix matching
#         prefix = value[:3].lower()
#         return queryset.filter(jobmode__istartswith=prefix)
    
#     def filter_lpa(self, queryset, name, value):
#         """
#         Advanced salary range filtering with custom range support.
        
#         Supports:
#         - Single value: exact match
#         - Range (min-max): inclusive between values
#         - Open-ended ranges: 10+ means ≥10
#         """
#         if not value:
#             return queryset
            
#         try:
#             # Handle open-ended ranges (e.g., "10+")
#             if value.endswith('+'):
#                 min_lpa = float(value.rstrip('+'))  # Use float to handle decimals if needed
#                 return queryset.filter(lpa__gte=min_lpa)
                
#             # Handle ranges (e.g., "10-20")
#             if '-' in value:
#                 min_lpa, max_lpa = map(float, value.split('-'))
#                 # Assuming lpa is stored as a string like "10-20" in the model
#                 return queryset.filter(
#                     Q(lpa__startswith=f"{int(min_lpa)}-") | 
#                     Q(lpa__endswith=f"-{int(max_lpa)}") |
#                     Q(lpa__gte=min_lpa, lpa__lte=max_lpa)
#                 )
                
#             # Handle exact value
#             return queryset.filter(lpa=value)
#         except (ValueError, TypeError):
#             # Graceful fallback if parsing fails
#             return queryset
    
#     def filter_recent(self, queryset, name, value):
#         """
#         Filter jobs by posting recency.
        
#         Supports:
#         - today: Posted today
#         - week: Posted in the last 7 days
#         - month: Posted in the last 30 days
#         """
#         if not value:
#             return queryset
            
#         now = timezone.now()
        
#         if value == 'today' or value == '24h':
#             start_date = now - timedelta(days=1)
#         elif value == 'week' or value == '7d':
#             start_date = now - timedelta(days=7)
#         elif value == 'month' or value == '30d':
#             start_date = now - timedelta(days=30)
#         else:
#             return queryset
            
#         return queryset.filter(posteDate__gte=start_date)
        
#     def filter_skills(self, queryset, name, value):
#         """
#         Filter jobs by required skills.
        
#         Supports comma-separated list of skills.
#         """
#         if not value:
#             return queryset
            
#         skills = [skill.strip().lower() for skill in value.split(',')]
#         query = Q()
        
#         # Check for each skill in job details
#         for skill in skills:
#             if not skill:
#                 continue
                
#             query |= (
#                 Q(title__icontains=skill) |
#                 Q(about__icontains=skill) |
#                 Q(responsibility__icontains=skill)
#             )
            
#         return queryset.filter(query).distinct()

# class JobSearchView(generics.ListAPIView):
#     """
#     Enhanced API view for searching and filtering jobs.
    
#     Features:
#     - Optimized queryset with select_related for employer data
#     - Custom pagination
#     - Comprehensive filtering system
#     - Default ordering by newest first
#     """
#     queryset = Jobs.objects.select_related('employer').filter(active=True).order_by('-posteDate')
#     serializer_class = JobSerializer
#     filter_backends = [filters.DjangoFilterBackend]
#     filterset_class = JobFilter
#     pagination_class = StandardResultsSetPagination






# class GetJobStatus(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, job_id):
#         action = request.data.get('action')
#         try:
#             job = Jobs.objects.get(id=job_id)
            
#             if job.employer.user != request.user and not request.user.is_staff:
#                 return Response(
#                     {"error": "You don't have permission to modify this job"},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
            
#             if action == 'deactivate':
#                 job.active = False
#                 message = "Job deactivated successfully"
#             elif action == 'activate':
#                 job.active = True
#                 message = "Job activated successfully"
#             else:
#                 return Response(
#                     {"error": "Invalid action. Use 'activate' or 'deactivate'"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             job.save()
#             serializer = JobSerializer(job, context={'request': request})
#             return Response({
#                 "message": message,
#                 "job": serializer.data
#             }, status=status.HTTP_200_OK)
            
#         except Jobs.DoesNotExist:
#             return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)


# from django.shortcuts import get_object_or_404



# class SavejobStatus(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, job_id):
#         action = request.data.get('action')
#         user = request.user
        
#         if action not in ['save', 'unsave']:
#             return Response(
#                 {"error": "Invalid action. Use 'save' or 'unsave'"}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
            
#         try:
#             job = get_object_or_404(Jobs, id=job_id)
#             candidate = get_object_or_404(Candidate, user=user)
            
#             if action == 'save':
#                 saved_job, created = SavedJobs.objects.get_or_create(
#                     candidate=candidate, 
#                     job=job
#                 )
#                 return Response(
#                     {"message": "Job saved successfully" if created else "Job already saved"},
#                     status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
#                 )
                
#             elif action == 'unsave':
#                 deleted_count, _ = SavedJobs.objects.filter(
#                     candidate=candidate, 
#                     job=job
#                 ).delete()
#                 if deleted_count > 0:
#                     return Response(
#                         {"message": "Job unsaved successfully"}, 
#                         status=status.HTTP_200_OK
#                     )
#                 return Response(
#                     {"message": "Job was not saved"}, 
#                     status=status.HTTP_200_OK
#                 )
                    
#         except Exception as e:
#             return Response(
#                 {"error": str(e)}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

# class CheckJobSaveStatus(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request, job_id):
#         user = request.user
#         print("...................................",user)
#         try:
#             job = Jobs.objects.get(id=job_id)
#             candidate = Candidate.objects.get(user=user)
#             is_saved = SavedJobs.objects.filter(candidate=candidate, job=job).exists()
#             return Response({"is_saved": is_saved}, status=status.HTTP_200_OK)
#         except Jobs.DoesNotExist:
#             return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Candidate.DoesNotExist:
#             return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class SavedJobsView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         try:
#             candidate = get_object_or_404(Candidate, user=request.user)
#             saved_jobs = SavedJobs.objects.filter(candidate=candidate)
#             serializer = SavedJobSerializer(saved_jobs, many=True)
#             return Response(
#                 {"data": serializer.data}, 
#                 status=status.HTTP_200_OK
#             )
#         except Exception as e:
#             return Response(
#                 {"error": str(e)}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

# class ApplicationStatusView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, job_id):
#         action = request.data.get('action')
#         try:
#             applied_job = ApplyedJobs.objects.get(id=job_id)
#             if applied_job:
#                 applied_job.status = action
#                 applied_job.save()
#                 return Response({"message": "Status changed"}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"message": "No job available"}, status=status.HTTP_204_NO_CONTENT)
#         except ApplyedJobs.DoesNotExist:
#             return Response({"error": "Job application not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# class GetQuestions(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request, job_id):
#         try:
#             questions = Question.objects.filter(job=job_id)
#             serializer = QuestionSerializer(questions, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except:
#             return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        


# class Applyjob(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, job_id):
#         user = request.user
#         try:
#             job = Jobs.objects.get(id=job_id)
#             candidate = Candidate.objects.get(user=user)
#             if ApplyedJobs.objects.filter(candidate=candidate, job=job).exists():
#                 return Response({'message': 'You have already applied for this job.'}, status=status.HTTP_200_OK)
            
#             application = ApplyedJobs.objects.create(candidate=candidate, job=job)
    
#             created = Approvals.objects.create(
#                 candidate=candidate,
#                 employer=job.employer,
#                 job=job,
#                 is_approved=False,
#                 is_rejected=False
#             )
                
#             answers_data = request.data.get('answers', [])
#             for answer in answers_data:
#                 question_id = answer.get('question')
#                 answer_text = answer.get('answer_text')
#                 try:
#                     question = Question.objects.get(id=question_id, job=job)
#                     Answer.objects.create(
#                         candidate=candidate,
#                         question=question,
#                         answer_text=answer_text,
#                         question_text=question.text  # Save the question text here
#                     )
#                 except Question.DoesNotExist:
#                     return Response({'message': f'Question {question_id} not found.'}, status=status.HTTP_400_BAD_REQUEST)

#             return Response({'message': 'You have successfully applied for the job.'}, status=status.HTTP_200_OK)
#         except Jobs.DoesNotExist:
#             return Response({'message': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
#         except Candidate.DoesNotExist:
#             return Response({'message': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# # class Applyjob(APIView):
# #     permission_classes = [IsAuthenticated]
    
# #     def post(self, request, job_id):
# #         user = request.user
# #         try:
# #             job = Jobs.objects.get(id=job_id)
# #             candidate = Candidate.objects.get(user=user)
# #             if ApplyedJobs.objects.filter(candidate=candidate, job=job).exists():
# #                 return Response({'message': 'You have already applied for this job.'}, status=status.HTTP_200_OK)
            
# #             application = ApplyedJobs.objects.create(candidate=candidate, job=job)
    
# #             created = Approvals.objects.create(
# #                 candidate=candidate,
# #                 employer=job.employer,
# #                 job=job,
# #                 is_approved=False,
# #                 is_rejected=False
# #                 )
                
# #             answers_data = request.data.get('answers', [])
# #             for answer in answers_data:
# #                 question_id = answer.get('question')
# #                 answer_text = answer.get('answer_text')
# #                 try:
# #                     question = Question.objects.get(id=question_id, job=job)
# #                     Answer.objects.create(
# #                         candidate=candidate,
# #                         question=question,
# #                         answer_text=answer_text
# #                     )
# #                 except Question.DoesNotExist:
# #                     return Response({'message': f'Question {question_id} not found.'}, status=status.HTTP_400_BAD_REQUEST)

# #             return Response({'message': 'You have successfully applied for the job.'}, status=status.HTTP_200_OK)
# #         except Jobs.DoesNotExist:
# #             return Response({'message': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
# #         except Candidate.DoesNotExist:
# #             return Response({'message': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)
# #         except Exception as e:
# #             return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def check_application(request, job_id):
#     has_applied = ApplyedJobs.objects.filter(job_id=job_id, candidate__user=request.user).exists()
#     return Response({"has_applied": has_applied})




# # # views.py

# # from rest_framework.decorators import api_view, permission_classes
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.response import Response
# # from rest_framework import status
# # from django.shortcuts import get_object_or_404
# # from django.utils import timezone

# # from .serializer import ApprovalSerializer

# # import logging
# # from rest_framework.decorators import api_view, permission_classes
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.response import Response
# # from rest_framework import status
# # from django.shortcuts import get_object_or_404
# # from django.utils import timezone
# # from Empjob.models import Jobs, Approvals, ApplyedJobs  # Assuming ApplyedJobs exists
# # from user_account.models import Candidate, Employer
# # from .serializer import ApprovalSerializer

# # # Configure logger
# # logger = logging.getLogger(__name__)

# # @api_view(['POST'])
# # @permission_classes([IsAuthenticated])
# # def request_chat(request, job_id):
# #     """
# #     Create a chat request from candidate to employer
# #     """
# #     # Get the job
# #     job = get_object_or_404(Jobs, id=job_id)
    
# #     # Get candidate profile for the current user
# #     try:
# #         candidate = Candidate.objects.get(user=request.user)
# #     except Candidate.DoesNotExist:
# #         return Response({"detail": "User is not a candidate."}, status=status.HTTP_400_BAD_REQUEST)
    
# #     # Check if the user has applied for this job
# #     if not ApplyedJobs.objects.filter(job=job, candidate=candidate).exists():
# #         return Response({"detail": "You must apply for this job before requesting a chat."}, status=status.HTTP_400_BAD_REQUEST)
    
# #     # Get employer
# #     employer = job.employer
    
# #     # Check if there's already a request
# #     approval, created = Approvals.objects.get_or_create(
# #         job=job,
# #         candidate=candidate,
# #         employer=employer,
# #         defaults={
# #             'is_requested': True,
# #             'is_approved': False,
# #             'is_rejected': False,
# #             'requested_at': timezone.now()
# #         }
# #     )
    
# #     # If not created, and not already approved or rejected, update it
# #     if not created:
# #         if approval.is_approved:
# #             return Response({"detail": "Chat already approved."}, status=status.HTTP_200_OK)
# #         elif approval.is_rejected:
# #             return Response({"detail": "Chat request was rejected."}, status=status.HTTP_400_BAD_REQUEST)
# #         else:
# #             approval.is_requested = True
# #             approval.requested_at = timezone.now()
# #             approval.save()
# #             return Response({"detail": "Chat request already pending."}, status=status.HTTP_200_OK)
    
# #     return Response({"detail": "Chat request sent successfully."}, status=status.HTTP_201_CREATED)

# # import logging
# # from rest_framework.decorators import api_view, permission_classes
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.response import Response
# # from Empjob.models import Jobs, Approvals
# # from user_account.models import Employer, Candidate

# # logger = logging.getLogger(__name__)



# # @api_view(['GET'])
# # @permission_classes([IsAuthenticated])
# # def check_chat_status(request, job_id):
# #     try:
# #         user = request.user
# #         logger.info(f"Chat status check - User: {user.id} ({user.email}), Job: {job_id}")
        
# #         job = Jobs.objects.select_related('employer__user').get(id=job_id)
# #         approval = Approvals.objects.select_related('candidate__user').filter(job=job).first()

# #         response = {
# #             "system": {
# #                 "status": "success",
# #                 "user_id": user.id,
# #                 "job_id": job.id,
# #                 "is_job_owner": False,
# #                 "is_approved_candidate": False,
# #                 "debug": {
# #                     "job_owner_id": getattr(job.employer, 'user_id', None),
# #                     "approval_candidate_id": getattr(approval, 'candidate.user_id', None) if approval else None,
# #                     "approval_status": getattr(approval, 'is_approved', None),
# #                     "approval_id": getattr(approval, 'id', None)
# #                 }
# #             },
# #             "chat": {
# #                 "exists": False,
# #                 "requested": False,
# #                 "approved": False,
# #                 "rejected": False,
# #                 "pending": False,
# #                 "can_chat": False,
# #                 "unread_count": 0,
# #                 "approval_id": None,
# #                 "last_updated": None
# #             }
# #         }

# #         # Check employer access
# #         if hasattr(user, 'employer') and job.employer.user.id == user.id:
# #             response['system']['is_job_owner'] = True
# #             unread_count = Approvals.objects.filter(
# #                 job=job,
# #                 is_approved=False,
# #                 is_rejected=False
# #             ).count()
            
# #             if approval:
# #                 response['chat'].update({
# #                     "exists": True,
# #                     "requested": True,
# #                     "approved": approval.is_approved,
# #                     "rejected": approval.is_rejected,
# #                     "pending": not approval.is_approved and not approval.is_rejected,
# #                     "can_chat": approval.is_approved,
# #                     "unread_count": unread_count,
# #                     "approval_id": approval.id,
# #                     "last_updated": approval.updated_at.isoformat() if approval.updated_at else None
# #                 })
# #             return Response(response, status=200)

# #         # Check candidate access
# #         if hasattr(user, 'candidate') and approval and approval.candidate.user.id == user.id:
# #             response['system']['is_approved_candidate'] = approval.is_approved
# #             response['chat'].update({
# #                 "exists": True,
# #                 "requested": True,
# #                 "approved": approval.is_approved,
# #                 "rejected": approval.is_rejected,
# #                 "pending": not approval.is_approved and not approval.is_rejected,
# #                 "can_chat": approval.is_approved,
# #                 "approval_id": approval.id,
# #                 "last_updated": approval.updated_at.isoformat() if approval.updated_at else None
# #             })
# #             return Response(response, status=200)

# #         return Response(response, status=200)

# #     except Jobs.DoesNotExist:
# #         logger.error(f"Job not found - JobID: {job_id}")
# #         return Response({
# #             "system": {
# #                 "status": "error",
# #                 "message": "Job not found"
# #             }
# #         }, status=404)
# #     except Exception as e:
# #         logger.error(f"Chat status error: {str(e)}")
# #         return Response({
# #             "system": {
# #                 "status": "error",
# #                 "message": "Internal server error"
# #             }
# #         }, status=500)


# # @api_view(['GET'])
# # @permission_classes([IsAuthenticated])
# # def employer_approvals(request):
# #     """
# #     Get all pending chat requests for an employer
# #     """
# #     # Get employer profile
# #     try:
# #         employer = Employer.objects.get(user=request.user)
# #     except Employer.DoesNotExist:
# #         return Response({"detail": "User is not an employer."}, status=status.HTTP_400_BAD_REQUEST)
    
# #     # Get pending requests (is_requested=True, is_approved=False, is_rejected=False)
# #     pending_requests = Approvals.objects.filter(
# #         employer=employer,
# #         is_requested=True,
# #         is_approved=False,
# #         is_rejected=False
# #     )
    
# #     # Serialize the data
# #     serializer = ApprovalSerializer(pending_requests, many=True)
    
# #     return Response(serializer.data)

# # @api_view(['GET'])
# # @permission_classes([IsAuthenticated])
# # def employer_approvals_count(request):
# #     """
# #     Get count of pending chat requests for an employer
# #     """
# #     # Get employer profile
# #     try:
# #         employer = Employer.objects.get(user=request.user)
# #     except Employer.DoesNotExist:
# #         return Response({"count": 0})
    
# #     # Get count of pending requests
# #     count = Approvals.objects.filter(
# #         employer=employer,
# #         is_requested=True,
# #         is_approved=False,
# #         is_rejected=False
# #     ).count()
    
# #     return Response({"count": count})

# # @api_view(['POST'])
# # @permission_classes([IsAuthenticated])
# # def manage_chat_request(request, approval_id):
# #     """
# #     Approve or reject a chat request
# #     """
# #     # Get employer profile
# #     try:
# #         employer = Employer.objects.get(user=request.user)
# #     except Employer.DoesNotExist:
# #         return Response({"detail": "User is not an employer."}, status=status.HTTP_400_BAD_REQUEST)
    
# #     # Get the approval
# #     approval = get_object_or_404(Approvals, id=approval_id, employer=employer)
    
# #     # Check the action
# #     action = request.data.get('action')
    
# #     if action == 'approve':
# #         approval.is_approved = True
# #         approval.is_rejected = False
# #         approval.save()
# #         return Response({"detail": "Chat request approved."})
    
# #     elif action == 'reject':
# #         approval.is_rejected = True
# #         approval.is_approved = False
# #         approval.save()
# #         return Response({"detail": "Chat request rejected."})
    
# #     else:
# #         return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)


# from rest_framework import serializers
# from user_account.models import *
# from Empjob.models import *
# from django.utils import timezone

# from rest_framework import serializers
# from Empjob.models import Jobs, Question,Answer
# from user_account.api.serializer import *



# class QuestionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Question
#         fields = ['id', 'text', 'question_type']




# class PostJobSerializer(serializers.ModelSerializer):
#     questions = QuestionSerializer(many=True, required=False)
    
#     class Meta:
#         model = Jobs
#         fields = '__all__'
#         depth = 1  
#     def create(self, validated_data):
#         questions_data = validated_data.pop('questions', [])
#         employer = self.context['employer']
#         job = Jobs.objects.create(employer=employer, **validated_data)
        
#         # Create associated questions
#         for question_data in questions_data:
#             Question.objects.create(job=job, **question_data)
            
#         return job
# from rest_framework import serializers
# from user_account.models import Employer
# from Empjob.models import Jobs, Question, ApplyedJobs
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class EmployerSerializer(serializers.ModelSerializer):
#     user_full_name = serializers.CharField(source='user.full_name', read_only=True)
#     user_email = serializers.CharField(source='user.email', read_only=True)
#     user_id = serializers.CharField(source='user.id', read_only=True)
#     profile_pic = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Employer
#         fields = [
#             'profile_pic', 'user_id', 'user_email', 'phone', 'id', 'industry',
#             'user_full_name', 'headquarters', 'address', 'about', 'website_link'
#         ]
    
#     def get_profile_pic(self, obj):
#         if obj.profile_pic:
#             request = self.context.get('request')
#             if request:
#                 return request.build_absolute_uri(obj.profile_pic.url)
#             return obj.profile_pic.url
#         return None

# class QuestionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Question
#         fields = '__all__'

# class JobSerializer(serializers.ModelSerializer):
#     employer = EmployerSerializer()
#     questions = serializers.SerializerMethodField()
#     applications_count = serializers.SerializerMethodField()
#     can_edit = serializers.SerializerMethodField()
    

#     class Meta:
#         model = Jobs
#         fields = '__all__'
#     def get_questions(self, obj):
#         questions = Question.objects.filter(job=obj)
#         return QuestionSerializer(questions, many=True).data

#     def get_applications_count(self, obj):
#         return ApplyedJobs.objects.filter(job=obj).count()

#     def get_can_edit(self, obj):
#         request = self.context.get('request')
#         if request:
#             return obj.employer.user == request.user or request.user.is_staff
#         return False
   

# class EducationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Education
#         fields = '__all__'

# class CandidateSerializer(serializers.ModelSerializer):
#     education = serializers.SerializerMethodField()
#     user_name = serializers.CharField(source='user.full_name', read_only=True)
#     email = serializers.CharField(source='user.email', read_only=True)

#     class Meta:
#         model = Candidate
#         fields = '__all__'

#     def get_education(self, obj):
#         educations = Education.objects.filter(user=obj.user)
#         return EducationSerializer(educations, many=True).data

# class AnswerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Answer
#         fields = '__all__'

# class ApplyedForJobsSerializer(serializers.ModelSerializer):
#     candidate = CandidateSerializer()
#     answers = serializers.SerializerMethodField()

#     class Meta:
#         model = ApplyedJobs
#         fields = '__all__'

#     def get_answers(self, obj):
#         answers = Answer.objects.filter(candidate=obj.candidate, question__job=obj.job)
#         return AnswerSerializer(answers, many=True).data

# class ApplicationSerializer(serializers.ModelSerializer):
#     employer_name = serializers.SerializerMethodField()
#     employer_id = serializers.SerializerMethodField()
#     applications = serializers.SerializerMethodField()
#     questions = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Jobs
#         fields = '__all__'

#     def get_employer_name(self, obj):
#         return obj.employer.user.full_name
    
#     def get_employer_id(self, obj):
#         return obj.employer.id

#     def get_applications(self, obj):
#         applications = ApplyedJobs.objects.filter(job=obj)
#         serializer = ApplyedForJobsSerializer(applications, many=True)
#         return serializer.data
    
#     def get_questions(self, obj):
#         questions = Question.objects.filter(job=obj)
#         return QuestionSerializer(questions, many=True).data

# class SavedJobSerializer(serializers.ModelSerializer):
#     job = JobSerializer()
    
#     class Meta:
#         model = SavedJobs
#         fields = '__all__'

# class ApprovalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Approvals
#         fields = ['id', 'candidate', 'employer', 'job', 'is_approved', 'is_rejected']

# class ApplyedJobSerializer(serializers.ModelSerializer):
#     job = JobSerializer()
#     candidate_name = serializers.SerializerMethodField()
#     approvals = serializers.SerializerMethodField()
    
#     class Meta:
#         model = ApplyedJobs
#         fields = ['id', 'job', 'status', 'candidate', 'applyed_on', 'candidate_name','approvals']
    
#     def get_approvals(self, obj):
#         approvals = Approvals.objects.filter(candidate=obj.candidate, job=obj.job)
#         return ApprovalSerializer(approvals, many=True).data
    
#     def get_candidate_name(self, obj):
#         candidate = Candidate.objects.get(id=obj.candidate_id)  
#         return candidate.user.full_name
    
# # # serializers.py
# # from rest_framework import serializers
# # from Empjob.models import Approvals

# # class ApprovalsSerializer(serializers.ModelSerializer):
# #     candidate_name = serializers.CharField(source='candidate.user.full_name', read_only=True)
# #     employer_name = serializers.CharField(source='employer.user.full_name', read_only=True)
# #     job_id = serializers.CharField(source='job.id', read_only=True)

# #     class Meta:
# #         model = Approvals
# #         fields = ['id', 'candidate', 'employer', 'job', 'is_requested', 'is_approved', 'is_rejected',
# #                   'candidate_name', 'employer_name', 'job_id','requested_at']


# # serializers.py
# from rest_framework import serializers
# from Empjob.models import Approvals

# class ApprovalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Approvals
#         fields = ['id', 'candidate', 'employer', 'job', 'is_requested', 
#                  'is_approved', 'is_rejected', 'requested_at']
        



# from rest_framework import serializers
# from user_account.models import *
# from Empjob.models import *

# # Question Serializers
# class QuestionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Question
#         fields = ['id', 'text', 'question_type']

# # Answer Serializer with Question Text
# class AnswerSerializer(serializers.ModelSerializer):
#     question_text = serializers.CharField(source='question.text', read_only=True)
    
#     class Meta:
#         model = Answer
#         fields = ['id', 'candidate', 'question', 'question_text', 'answer_text']

# # Application Serializers
# class ApplyedForJobsSerializer(serializers.ModelSerializer):
#     candidate = CandidateSerializer()
#     answers = serializers.SerializerMethodField()

#     class Meta:
#         model = ApplyedJobs
#         fields = '__all__'

#     def get_answers(self, obj):
#         answers = Answer.objects.filter(candidate=obj.candidate, question__job=obj.job)
#         return AnswerSerializer(answers, many=True, context=self.context).data

# # from rest_framework import serializers
# # from user_account.models import User, Candidate, Education, Employer
# # from Empjob.models import Jobs, Question, Answer, ApplyedJobs, SavedJobs, Approvals
# # from django.contrib.auth import get_user_model
# # from django.utils import timezone

# # User = get_user_model()

# # # ========== USER ACCOUNT SERIALIZERS ==========
# # class EmployerSerializer(serializers.ModelSerializer):
# #     user_full_name = serializers.CharField(source='user.full_name', read_only=True)
# #     user_email = serializers.CharField(source='user.email', read_only=True)
# #     user_id = serializers.CharField(source='user.id', read_only=True)
# #     profile_pic = serializers.SerializerMethodField()
    
# #     class Meta:
# #         model = Employer
# #         fields = [
# #             'profile_pic', 'user_id', 'user_email', 'phone', 'id', 'industry',
# #             'user_full_name', 'headquarters', 'address', 'about', 'website_link'
# #         ]
    
# #     def get_profile_pic(self, obj):
# #         if obj.profile_pic:
# #             request = self.context.get('request')
# #             return request.build_absolute_uri(obj.profile_pic.url) if request else obj.profile_pic.url
# #         return None

# # class EducationSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Education
# #         fields = '__all__'

# # class CandidateSerializer(serializers.ModelSerializer):
# #     education = serializers.SerializerMethodField()
# #     user_name = serializers.CharField(source='user.full_name', read_only=True)
# #     email = serializers.CharField(source='user.email', read_only=True)

# #     class Meta:
# #         model = Candidate
# #         fields = '__all__'

# #     def get_education(self, obj):
# #         educations = Education.objects.filter(user=obj.user)
# #         return EducationSerializer(educations, many=True).data

# # # ========== JOB SERIALIZERS ==========
# # class PostJobSerializer(serializers.ModelSerializer):
# #     questions = serializers.SerializerMethodField()
    
# #     class Meta:
# #         model = Jobs
# #         fields = '__all__'
# #         depth = 1

# #     def get_questions(self, obj):
# #         questions = Question.objects.filter(job=obj)
# #         return QuestionSerializer(questions, many=True).data

# #     def create(self, validated_data):
# #         questions_data = validated_data.pop('questions', [])
# #         employer = self.context['employer']
# #         job = Jobs.objects.create(employer=employer, **validated_data)
        
# #         for question_data in questions_data:
# #             Question.objects.create(job=job, **question_data)
# #         return job

# # class JobSerializer(serializers.ModelSerializer):
# #     employer = EmployerSerializer()
# #     questions = serializers.SerializerMethodField()
# #     applications_count = serializers.SerializerMethodField()
# #     can_edit = serializers.SerializerMethodField()

# #     class Meta:
# #         model = Jobs
# #         fields = '__all__'

# #     def get_questions(self, obj):
# #         questions = Question.objects.filter(job=obj)
# #         return QuestionSerializer(questions, many=True).data

# #     def get_applications_count(self, obj):
# #         return ApplyedJobs.objects.filter(job=obj).count()

# #     def get_can_edit(self, obj):
# #         request = self.context.get('request')
# #         return obj.employer.user == request.user or request.user.is_staff if request else False

# # # ========== QUESTION/ANSWER SERIALIZERS ==========
# # class QuestionSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Question
# #         fields = ['id', 'text', 'question_type', 'question_text']

# # class AnswerSerializer(serializers.ModelSerializer):
# #     question_text = serializers.CharField(source='question.text', read_only=True)
    
# #     class Meta:
# #         model = Answer
# #         fields = ['id', 'candidate', 'question', 'question_text', 'answer_text']
# #     def __str__(self):
# #         return f"Answer to '{self.question_text[:50]}...' by {self.candidate}"

# # # ========== APPLICATION SERIALIZERS ==========
# # class ApprovalSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Approvals
# #         fields = ['id', 'candidate', 'employer', 'job', 'is_requested', 
# #                  'is_approved', 'is_rejected', 'requested_at']

# # class ApplyedForJobsSerializer(serializers.ModelSerializer):
# #     candidate = CandidateSerializer()
# #     answers = serializers.SerializerMethodField()

# #     class Meta:
# #         model = ApplyedJobs
# #         fields = '__all__'

# #     def get_answers(self, obj):
# #         answers = Answer.objects.filter(candidate=obj.candidate, question__job=obj.job)
# #         return AnswerSerializer(answers, many=True, context=self.context).data

# # class ApplyedJobSerializer(serializers.ModelSerializer):
# #     job = JobSerializer()
# #     candidate_name = serializers.SerializerMethodField()
# #     approvals = serializers.SerializerMethodField()
    
# #     class Meta:
# #         model = ApplyedJobs
# #         fields = ['id', 'job', 'status', 'candidate', 'applyed_on', 'candidate_name', 'approvals']
    
# #     def get_approvals(self, obj):
# #         approvals = Approvals.objects.filter(candidate=obj.candidate, job=obj.job)
# #         return ApprovalSerializer(approvals, many=True).data
    
# #     def get_candidate_name(self, obj):
# #         return obj.candidate.user.full_name if obj.candidate and obj.candidate.user else None

# # class ApplicationSerializer(serializers.ModelSerializer):
# #     employer_name = serializers.SerializerMethodField()
# #     employer_id = serializers.SerializerMethodField()
# #     applications = serializers.SerializerMethodField()
# #     questions = serializers.SerializerMethodField()
    
# #     class Meta:
# #         model = Jobs
# #         fields = '__all__'

# #     def get_employer_name(self, obj):
# #         return obj.employer.user.full_name if obj.employer and obj.employer.user else None
    
# #     def get_employer_id(self, obj):
# #         return obj.employer.id if obj.employer else None

# #     def get_applications(self, obj):
# #         applications = ApplyedJobs.objects.filter(job=obj)
# #         return ApplyedForJobsSerializer(applications, many=True).data
    
# #     def get_questions(self, obj):
# #         questions = Question.objects.filter(job=obj)
# #         return QuestionSerializer(questions, many=True).data

# # # ========== SAVED JOBS SERIALIZER ==========
# # class SavedJobSerializer(serializers.ModelSerializer):
# #     job = JobSerializer()
    
# #     class Meta:
# #         model = SavedJobs
# #         fields = '__all__'





















# Standard library imports
import logging

# Django imports
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.db.models import Q
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
# views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .serializer import *

logger = logging.getLogger(__name__)
# DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination

# Third-party imports
import razorpay
from django_filters import rest_framework as filters # type: ignore
from django_filters.rest_framework import DjangoFilterBackend # type: ignore

# Local imports
from .serializer import *
from user_account.models import *
from Empjob.models import *
from payment.models import *

logger = logging.getLogger(__name__)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
from django.middleware.csrf import get_token
from django.http import JsonResponse

def csrf_token_view(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

# Utility Views
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})



class PostJob(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            if user.user_type != 'employer':
                return Response({"error": "Only employers can post jobs"}, status=status.HTTP_403_FORBIDDEN)
            
            employer = Employer.objects.get(user=user)
            job_count = Jobs.objects.filter(employer=employer).count()
            
            # Check for active subscription
            active_subscription = EmployerSubscription.objects.filter(
                employer=employer, 
                status='active',
                end_date__gt=timezone.now()
            ).first()
            
            # If no active subscription or job limit reached
            if not active_subscription:
                return Response({
                    "error": "No active subscription found",
                    "subscription_required": True,
                    "message": "Please subscribe to post jobs"
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
            
            # If job limit reached based on subscription plan
            if job_count >= active_subscription.plan.job_limit:
                # For unlimited plans (job_limit = 9999)
                if active_subscription.plan.job_limit == 9999:
                    pass  # Allow posting, no limit
                else:
                    # Check if payment for additional job is provided
                    if 'razorpay_payment_id' not in request.data:
                        order = razorpay_client.order.create({
                            "amount": 200 * 100,  # Additional job posting fee
                            "currency": "INR",
                            "payment_capture": 1
                        })
                        return Response({
                            "payment_required": True,
                            "message": f"You've reached your plan limit of {active_subscription.plan.job_limit} jobs. Payment required for additional job posting.",
                            "order_id": order['id'],
                            "amount": order['amount'],
                            "key": settings.RAZORPAY_KEY_ID
                        }, status=status.HTTP_402_PAYMENT_REQUIRED)
                    
                    # Verify the payment
                    payment_id = request.data['razorpay_payment_id']
                    if not Payment.objects.filter(
                        transaction_id=payment_id,
                        employer=employer,
                        status='success'
                    ).exists():
                        return Response({"error": "Invalid or unverified payment"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Process the job posting
            serializer = PostJobSerializer(data=request.data, context={'employer': employer})
            if serializer.is_valid():
                job = serializer.save()
                
                # Log the job creation with subscription info
                logger.info(f"Job posted by employer {employer.id} with subscription {active_subscription.id if active_subscription else 'None'}")
                
                return Response({"message": "Job posted successfully"}, status=status.HTTP_201_CREATED)
            
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Employer.DoesNotExist:
            return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in PostJob: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.utils import timezone
 

def get_employer_job_usage(employer):
    """
    Get job usage statistics for an employer
    
    Returns:
        dict: Contains job count, subscription info, and remaining job slots
    """
    # Get current active subscription
    active_subscription = EmployerSubscription.objects.filter(
        employer=employer,
        status='active',
        end_date__gt=timezone.now()
    ).first()
    
    # Count jobs posted by the employer
    job_count = Jobs.objects.filter(employer=employer).count()
    
    # Default values if no active subscription
    remaining_jobs = 0
    plan_name = None
    plan_limit = 0
    
    if active_subscription:
        plan_name = active_subscription.plan.get_name_display()
        plan_limit = active_subscription.plan.job_limit
        
        # Calculate remaining job slots
        if plan_limit == 9999:  # Unlimited
            remaining_jobs = "Unlimited"
        else:
            remaining_jobs = max(0, plan_limit - job_count)
    
    return {
        "job_count": job_count,
        "has_active_subscription": bool(active_subscription),
        "subscription_plan": plan_name,
        "job_limit": plan_limit,
        "remaining_jobs": remaining_jobs,
        "subscription_end_date": active_subscription.end_date if active_subscription else None
    }



class JobUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info("JobUsageView endpoint hit!")
        try:
            user = request.user
            if not hasattr(user, 'user_type') or user.user_type != 'employer':
                return Response({"error": "Only employers can access this information"}, status=status.HTTP_403_FORBIDDEN)

            employer = Employer.objects.get(user=user)
            subscription = EmployerSubscription.objects.filter(
                employer=employer, status="active", end_date__gt=timezone.now()
            ).order_by('-start_date').first()
            job_count = Jobs.objects.filter(employer=employer, active=True).count()

            if subscription:
                # Use the subscription's job_limit consistently
                job_limit = subscription.job_limit
                remaining_jobs = "Unlimited" if job_limit == 9999 else max(0, job_limit - job_count)
                usage_stats = {
                    "job_count": job_count,
                    "has_active_subscription": True,
                    "subscription_plan": subscription.plan.name,
                    "job_limit": job_limit,
                    "remaining_jobs": remaining_jobs,
                    "subscription_end_date": subscription.end_date.isoformat()
                }
            else:
                usage_stats = {
                    "job_count": job_count,
                    "has_active_subscription": False,
                    "subscription_plan": None,
                    "job_limit": 0,
                    "remaining_jobs": 0,
                    "subscription_end_date": None
                }

            logger.info(f"Returning usage stats: {usage_stats}")
            return Response(usage_stats, status=status.HTTP_200_OK)
        except Employer.DoesNotExist:
            return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in JobUsageView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class EditJob(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        jobId = request.data.get("jobId")
        try:
            job = Jobs.objects.get(id=jobId)
        except Jobs.DoesNotExist:
            return Response({"message":"something went wrong"}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        
        serializer = PostJobSerializer(instance=job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            candidate = Candidate.objects.get(user=user)
            serializer = CandidateSerializer(candidate, context={'request': request})
            return Response({
                'user_type': 'candidate',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Candidate.DoesNotExist:
            try:
                employer = Employer.objects.get(user=user)
                print("............................................................",employer)
                serializer = EmployerSerializer(employer, context={'request': request})
                print("............................................................",serializer)
                return Response({
                    'user_type': 'employer',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except Employer.DoesNotExist:
                return Response({
                    "message": "User profile not found",
                    "detail": "No candidate or employer profile exists for this user"
                }, status=status.HTTP_404_NOT_FOUND)
class GetJob(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        try:
            employer = Employer.objects.get(user=user)
            jobs = Jobs.objects.filter(employer=employer)
            serializer = JobSerializer(jobs, many=True)
            data = {
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        except Employer.DoesNotExist:
            return Response({"error": "Employer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetAllJob(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Check if the user is an employer
            if request.user.user_type == "employer":
                # Fetch the employer instance linked to the user
                employer = Employer.objects.get(user=request.user)
                # Filter jobs by the employer
                jobs = Jobs.objects.filter(employer=employer)
            else:
                # User is a candidate or admin: return all jobs
                jobs = Jobs.objects.all()

            serializer = JobSerializer(jobs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Employer.DoesNotExist:
            return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetJobDetail(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            # Get the job with related employer data
            job = Jobs.objects.select_related('employer', 'employer__user').get(id=job_id)
            
            # Pass the request to serializer for absolute URLs
            serializer = JobSerializer(job, context={'request': request})
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Jobs.DoesNotExist:
            return Response(
                {"error": "Job not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in GetJobDetail: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred while fetching job details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializer import ApplyedJobSerializer



logger = logging.getLogger(__name__)

class GetApplyedjob(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.debug(f"Fetching applied jobs for user: {user.id}")
        try:
            candidate = Candidate.objects.get(user=user)
            logger.debug(f"Found candidate: {candidate.id}")
            applied_jobs = ApplyedJobs.objects.filter(candidate=candidate)
            logger.debug(f"Found {applied_jobs.count()} applied jobs")
            serializer = ApplyedJobSerializer(applied_jobs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Candidate.DoesNotExist:
            logger.warning(f"Candidate not found for user: {user.id}")
            return Response({"message": "Candidate not found"}, status=404)
        except Exception as e:
            logger.error(f"Error in GetApplyedjob: {str(e)}", exc_info=True)
            return Response({"message": "Internal server error", "error": str(e)}, status=500)
        
class ApproveChatRequestView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, approve_id):
        return Response({"message": "Chat request approved"}, status=status.HTTP_200_OK)

class GetApplicationjob(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        try:
            employer = Employer.objects.get(user=user)
            jobs = Jobs.objects.filter(employer=employer, active=True)
            serializer = ApplicationSerializer(jobs, many=True)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









# from django.db.models import Q
# from django.utils import timezone
# from datetime import timedelta
# from django_filters import rest_framework as filters
# from Empjob.models import Jobs  # Make sure this import is correct

# class JobFilter(filters.FilterSet):
#     """
#     FilterSet for Jobs model with enhanced filtering capabilities.
    
#     Filtering supported for:
#     - Search: title, about, responsibility, skills
#     - Location: exact match and fuzzy match with priority
#     - Job type: full-time, part-time, etc.
#     - Job mode: remote, on-site, hybrid (prefix-based)
#     - Experience: from internship to senior level
#     - Salary range (LPA): custom ranges with min-max
#     - Active status: only show active listings
#     - Industry: specific industry sectors
#     - Posted date: filter by recency
#     """
#     search = filters.CharFilter(method='filter_search', label='Search')
#     location = filters.CharFilter(method='filter_location', label='Location')
#     jobtype = filters.CharFilter(lookup_expr='iexact', label='Job Type')
#     jobmode = filters.CharFilter(method='filter_jobmode', label='Job Mode')
#     experience = filters.CharFilter(lookup_expr='iexact', label='Experience')
#     lpa = filters.CharFilter(method='filter_lpa', label='Salary Range (e.g., 10-20)')
#     employer = filters.NumberFilter(field_name='employer__id', label='Employer ID')
#     industry = filters.CharFilter(lookup_expr='icontains', label='Industry')
#     active = filters.BooleanFilter(field_name='active', label='Active Jobs Only')
#     recent = filters.CharFilter(method='filter_recent', label='Recent Jobs')
#     skills = filters.CharFilter(method='filter_skills', label='Required Skills')
    
#     class Meta:
#         model = Jobs
#         fields = ['search', 'location', 'jobtype', 'jobmode', 'experience', 
#                  'lpa', 'employer', 'industry', 'active', 'recent', 'skills']
    
#     def filter_search(self, queryset, name, value):
#         """
#         Enhanced search across multiple job fields with keyword relevance.
        
#         Searches title, about, responsibility, and employer's full_name
#         to prioritize more relevant results.
#         """
#         if not value:
#             return queryset
            
#         # Split search terms for better matching
#         search_terms = value.split()
#         query = Q()
        
#         for term in search_terms:
#             # Build complex query with priority weighting
#             # Using employer__user__full_name as per your model structure
#             query |= (
#                 Q(title__icontains=term) |  
#                 Q(about__icontains=term) | 
#                 Q(responsibility__icontains=term) | 
#                 Q(employer__user__full_name__icontains=term)  # Fixed to match your model structure
#             )
            
#         return queryset.filter(query).distinct()
    
#     def filter_location(self, queryset, name, value):
#         """
#         Intelligent location filtering with multiple fallback mechanisms.
        
#         Implements a cascading match system:
#         1. Exact match (highest priority)
#         2. Case-insensitive exact match
#         3. Word boundary match
#         4. Contains match
#         5. Special handling for "Remote" keyword
#         """
#         if not value:
#             return queryset
        
#         # Normalize the input for comparison
#         value_lower = value.lower().strip()
        
#         # Special case for "remote" - check both location and jobmode
#         if value_lower == "remote":
#             return queryset.filter(
#                 Q(location__iexact="remote") | 
#                 Q(jobmode__iexact="remote")
#             )
        
#         # Try exact match first (highest priority)
#         exact_match = queryset.filter(location__iexact=value)
#         if exact_match.exists():
#             return exact_match
            
#         # Try contains match for partial location names
#         return queryset.filter(location__icontains=value)
    
#     def filter_jobmode(self, queryset, name, value):
#         """
#         Filter jobs by jobmode using a prefix-based approach.
        
#         Uses the first 3 letters of the filter value for prefix matching,
#         e.g., "Rem" matches "Remote", "remote work", etc.
#         """
#         if not value:
#             return queryset
#         # Use the first 3 letters of the filter value for prefix matching
#         prefix = value[:3].lower()
#         return queryset.filter(jobmode__istartswith=prefix)
    
#     def filter_lpa(self, queryset, name, value):
#         """
#         Advanced salary range filtering with custom range support.
        
#         Supports:
#         - Single value: exact match
#         - Range (min-max): inclusive between values
#         - Open-ended ranges: 10+ means ≥10
#         """
#         if not value:
#             return queryset
            
#         try:
#             # Handle open-ended ranges (e.g., "10+")
#             if value.endswith('+'):
#                 min_lpa = float(value.rstrip('+'))  # Use float to handle decimals if needed
#                 return queryset.filter(lpa__gte=min_lpa)
                
#             # Handle ranges (e.g., "10-20")
#             if '-' in value:
#                 min_lpa, max_lpa = map(float, value.split('-'))
#                 # Assuming lpa is stored as a string like "10-20" in the model
#                 return queryset.filter(
#                     Q(lpa__startswith=f"{int(min_lpa)}-") | 
#                     Q(lpa__endswith=f"-{int(max_lpa)}") |
#                     Q(lpa__gte=min_lpa, lpa__lte=max_lpa)
#                 )
                
#             # Handle exact value
#             return queryset.filter(lpa=value)
#         except (ValueError, TypeError):
#             # Graceful fallback if parsing fails
#             return queryset
    
#     def filter_recent(self, queryset, name, value):
#         """
#         Filter jobs by posting recency.
        
#         Supports:
#         - today: Posted today
#         - week: Posted in the last 7 days
#         - month: Posted in the last 30 days
#         """
#         if not value:
#             return queryset
            
#         now = timezone.now()
        
#         if value == 'today' or value == '24h':
#             start_date = now - timedelta(days=1)
#         elif value == 'week' or value == '7d':
#             start_date = now - timedelta(days=7)
#         elif value == 'month' or value == '30d':
#             start_date = now - timedelta(days=30)
#         else:
#             return queryset
            
#         return queryset.filter(posteDate__gte=start_date)
        
#     def filter_skills(self, queryset, name, value):
#         """
#         Filter jobs by required skills.
        
#         Supports comma-separated list of skills.
#         """
#         if not value:
#             return queryset
            
#         skills = [skill.strip().lower() for skill in value.split(',')]
#         query = Q()
        
#         # Check for each skill in job details
#         for skill in skills:
#             if not skill:
#                 continue
                
#             query |= (
#                 Q(title__icontains=skill) |
#                 Q(about__icontains=skill) |
#                 Q(responsibility__icontains=skill)
#             )
            
#         return queryset.filter(query).distinct()



# class StandardResultsSetPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100


# class JobSearchView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     queryset = Jobs.objects.select_related('employer').filter(active=True).order_by('-posteDate')
#     serializer_class = SearchSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = JobFilter
#     pagination_class = StandardResultsSetPagination

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context.update({'request': self.request})
#         return context


# # class StandardResultsSetPagination(PageNumberPagination):
# #     page_size = 10
# #     page_size_query_param = 'page_size'
# #     max_page_size = 100

# # class JobSearchView(generics.ListAPIView):
# #     """
# #     Enhanced API view for searching and filtering jobs.
    
# #     Features:
# #     - Optimized queryset with select_related for employer data
# #     - Custom pagination with configurable page size
# #     - Comprehensive filtering via DjangoFilterBackend
# #     - Authentication required
# #     - Default ordering by newest first
# #     """
# #     permission_classes = [IsAuthenticated]
# #     queryset = Jobs.objects.select_related('employer').filter(active=True).order_by('-posteDate')
# #     serializer_class = JobSerializer
# #     filter_backends = [DjangoFilterBackend]
# #     filterset_class = JobFilter
# #     pagination_class = StandardResultsSetPagination

# class JobAutocompleteView(APIView):
#     def get(self, request):
#         query = request.query_params.get('q', '').strip()
#         if not query:
#             return Response([], status=status.HTTP_200_OK)

#         suggestions = []
#         titles = Jobs.objects.filter(
#             Q(title__icontains=query) & Q(active=True)
#         ).values('title').distinct()[:5]
#         suggestions.extend([{'type': 'title', 'value': t['title']} for t in titles])

#         locations = Jobs.objects.filter(
#             Q(location__icontains=query) & Q(active=True)
#         ).values('location').distinct()[:5]
#         suggestions.extend([{'type': 'location', 'value': l['location']} for l in locations])

#         jobtypes = Jobs.objects.filter(
#             Q(jobtype__icontains=query) & Q(active=True)
#         ).values('jobtype').distinct()[:5]
#         suggestions.extend([{'type': 'jobtype', 'value': j['jobtype']} for j in jobtypes])

#         jobmodes = Jobs.objects.filter(
#             Q(jobmode__icontains=query) & Q(active=True)
#         ).values('jobmode').distinct()[:5]
#         suggestions.extend([{'type': 'jobmode', 'value': j['jobmode']} for j in jobmodes])

#         industries = Jobs.objects.filter(
#             Q(industry__icontains=query) & Q(active=True)
#         ).values('industry').distinct()[:5]
#         suggestions.extend([{'type': 'industry', 'value': i['industry']} for i in industries])

#         suggestions = sorted(suggestions, key=lambda x: x['value'].lower())[:10]
#         return Response(suggestions, status=status.HTTP_200_OK)


# # class JobSearchView(generics.ListAPIView):
# #     """
# #     Enhanced API view for searching and filtering jobs.
    
# #     Features:
# #     - Optimized queryset with select_related for employer data
# #     - Custom pagination with configurable page size
# #     - Comprehensive filtering via DjangoFilterBackend
# #     - Authentication required
# #     - Default ordering by newest first
# #     """
# #     permission_classes = [IsAuthenticated]
# #     queryset = Jobs.objects.select_related('employer').filter(active=True).order_by('-posteDate')
# #     serializer_class = JobSerializer
# #     filter_backends = [DjangoFilterBackend]
# #     filterset_class = JobFilter
# #     pagination_class = StandardResultsSetPagination



# # class JobSearchView(APIView):
# #     def get(self, request):
# #         queryset = Jobs.objects.filter(active=True)
# #         query_params = request.query_params

# #         # Handle specific fields
# #         if 'title' in query_params:
# #             queryset = queryset.filter(title__icontains=query_params['title'])
# #         if 'location' in query_params:
# #             queryset = queryset.filter(location__icontains=query_params['location'])
# #         if 'jobtype' in query_params:
# #             queryset = queryset.filter(jobtype__icontains=query_params['jobtype'])
# #         if 'jobmode' in query_params:
# #             queryset = queryset.filter(jobmode__icontains=query_params['jobmode'])
# #         if 'experience' in query_params:
# #             queryset = queryset.filter(experience__icontains=query_params['experience'])
# #         if 'lpa' in query_params:
# #             queryset = queryset.filter(lpa__icontains=query_params['lpa'])
# #         if 'date_posted' in query_params:
# #             # Implement date filtering logic
# #             pass
# #         if 'salary' in query_params and 'salary_type' in query_params:
# #             # Implement salary filtering logic
# #             pass

# #         # Handle general search
# #         if 'search' in query_params:
# #             search_terms = query_params['search'].split(',')
# #             search_query = Q()
# #             for term in search_terms:
# #                 search_query |= (
# #                     Q(title__icontains=term) |
# #                     Q(location__icontains=term) |
# #                     Q(jobtype__icontains=term) |
# #                     Q(jobmode__icontains=term) |
# #                     Q(industry__icontains=term)
# #                 )
# #             queryset = queryset.filter(search_query)

# #         serializer = JobSerializer(queryset, many=True)
# #         return Response(serializer.data, status=status.HTTP_200_OK)



# from django.db.models import Q
# from django.utils import timezone
# from datetime import timedelta
# from django_filters import rest_framework as filters
# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.pagination import PageNumberPagination
# from Empjob.models import Jobs
# from user_account.models import Employer
# from rest_framework import serializers

# # Pagination Class
# class StandardResultsSetPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100

# # Job Filter
# class JobFilter(filters.FilterSet):
#     """
#     FilterSet for Jobs model with enhanced filtering capabilities.
    
#     Filtering supported for:
#     - Search: title, about, responsibility, skills
#     - Location: exact match and fuzzy match with priority
#     - Job type: full-time, part-time, etc.
#     - Job mode: remote, on-site, hybrid (prefix-based)
#     - Experience: from internship to senior level
#     - Salary range (LPA): custom ranges with min-max
#     - Active status: only show active listings
#     - Industry: specific industry sectors
#     - Posted date: filter by recency
#     """
#     search = filters.CharFilter(method='filter_search', label='Search')
#     location = filters.CharFilter(method='filter_location', label='Location')
#     jobtype = filters.CharFilter(lookup_expr='iexact', label='Job Type')
#     jobmode = filters.CharFilter(method='filter_jobmode', label='Job Mode')
#     experience = filters.CharFilter(lookup_expr='iexact', label='Experience')
#     lpa = filters.CharFilter(method='filter_lpa', label='Salary Range (e.g., 10-20)')
#     employer = filters.NumberFilter(field_name='employer__id', label='Employer ID')
#     industry = filters.CharFilter(lookup_expr='icontains', label='Industry')
#     active = filters.BooleanFilter(field_name='active', label='Active Jobs Only')
#     recent = filters.CharFilter(method='filter_recent', label='Recent Jobs')
#     skills = filters.CharFilter(method='filter_skills', label='Required Skills')
    
#     class Meta:
#         model = Jobs
#         fields = ['search', 'location', 'jobtype', 'jobmode', 'experience', 
#                  'lpa', 'employer', 'industry', 'active', 'recent', 'skills']
    
#     def filter_search(self, queryset, name, value):
#         """
#         Enhanced search across multiple job fields with keyword relevance.
        
#         Searches title, about, responsibility, and employer's full_name
#         to prioritize more relevant results.
#         """
#         if not value:
#             return queryset
            
#         search_terms = value.split()
#         query = Q()
        
#         for term in search_terms:
#             query |= (
#                 Q(title__icontains=term) |  
#                 Q(about__icontains=term) | 
#                 Q(responsibility__icontains=term) | 
#                 Q(employer__user__full_name__icontains=term)
#             )
            
#         return queryset.filter(query).select_related('employer').distinct()
    
#     def filter_location(self, queryset, name, value):
#         if not value:
#             return queryset
        
#         value_lower = value.lower().strip()
        
#         if value_lower == "remote":
#             return queryset.filter(
#                 Q(location__iexact="remote") | 
#                 Q(jobmode__iexact="remote")
#             )
        
#         exact_match = queryset.filter(location__iexact=value)
#         if exact_match.exists():
#             return exact_match
            
#         return queryset.filter(location__icontains=value)
    
#     def filter_jobmode(self, queryset, name, value):
#         if not value:
#             return queryset
#         prefix = value[:3].lower()
#         return queryset.filter(jobmode__istartswith=prefix)
    
#     def filter_lpa(self, queryset, name, value):
#         if not value:
#             return queryset
            
#         try:
#             if value.endswith('+'):
#                 min_lpa = float(value.rstrip('+'))
#                 return queryset.filter(lpa__gte=min_lpa)
                
#             if '-' in value:
#                 min_lpa, max_lpa = map(float, value.split('-'))
#                 return queryset.filter(
#                     Q(lpa__startswith=f"{int(min_lpa)}-") | 
#                     Q(lpa__endswith=f"-{int(max_lpa)}") |
#                     Q(lpa__gte=min_lpa, lpa__lte=max_lpa)
#                 )
                
#             return queryset.filter(lpa=value)
#         except (ValueError, TypeError):
#             return queryset
    
#     def filter_recent(self, queryset, name, value):
#         if not value:
#             return queryset
            
#         now = timezone.now()
        
#         if value == 'today' or value == '24h':
#             start_date = now - timedelta(days=1)
#         elif value == 'week' or value == '7d':
#             start_date = now - timedelta(days=7)
#         elif value == 'month' or value == '30d':
#             start_date = now - timedelta(days=30)
#         else:
#             return queryset
            
#         return queryset.filter(posteDate__gte=start_date)
        
#     def filter_skills(self, queryset, name, value):
#         if not value:
#             return queryset
            
#         skills = [skill.strip().lower() for skill in value.split(',')]
#         query = Q()
        
#         for skill in skills:
#             if not skill:
#                 continue
                
#             query |= (
#                 Q(title__icontains=skill) |
#                 Q(about__icontains=skill) |
#                 Q(responsibility__icontains=skill)
#             )
            
#         return queryset.filter(query).distinct()


# # Job Search View
# class JobSearchView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     queryset = Jobs.objects.select_related('employer').filter(active=True).order_by('-posteDate')
#     serializer_class = SearchSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = JobFilter
#     pagination_class = StandardResultsSetPagination

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context.update({'request': self.request})
#         return context

# # Job Autocomplete View
# class JobAutocompleteView(APIView):
#     def get(self, request):
#         query = request.query_params.get('q', '').strip()
#         if not query:
#             return Response([], status=status.HTTP_200_OK)

#         suggestions = []
#         titles = Jobs.objects.filter(
#             Q(title__icontains=query) & Q(active=True)
#         ).values('title').distinct()[:5]
#         suggestions.extend([{'type': 'title', 'value': t['title']} for t in titles])

#         locations = Jobs.objects.filter(
#             Q(location__icontains=query) & Q(active=True)
#         ).values('location').distinct()[:5]
#         suggestions.extend([{'type': 'location', 'value': l['location']} for l in locations])

#         jobtypes = Jobs.objects.filter(
#             Q(jobtype__icontains=query) & Q(active=True)
#         ).values('jobtype').distinct()[:5]
#         suggestions.extend([{'type': 'jobtype', 'value': j['jobtype']} for j in jobtypes])

#         jobmodes = Jobs.objects.filter(
#             Q(jobmode__icontains=query) & Q(active=True)
#         ).values('jobmode').distinct()[:5]
#         suggestions.extend([{'type': 'jobmode', 'value': j['jobmode']} for j in jobmodes])

#         industries = Jobs.objects.filter(
#             Q(industry__icontains=query) & Q(active=True)
#         ).values('industry').distinct()[:5]
#         suggestions.extend([{'type': 'industry', 'value': i['industry']} for i in industries])

#         suggestions = sorted(suggestions, key=lambda x: x['value'].lower())[:10]
#         return Response(suggestions, status=status.HTTP_200_OK)
































class SearchSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)
    employer_name = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Jobs
        fields = [
            'id', 'title', 'location', 'lpa', 'jobtype', 'jobmode', 'experience',
            'applyBefore', 'posteDate', 'about', 'responsibility', 'active',
            'industry', 'employer', 'employer_name', 'profile_pic',
        ]

    def get_employer_name(self, obj):
        try:
            return obj.employer.user.full_name if obj.employer and obj.employer.user else "Unnamed Employer"
        except Exception as e:
            print(f"[Serializer] Error getting employer_name for job {obj.id}: {str(e)}")
            return "Unnamed Employer"

    def get_profile_pic(self, obj):
        default_url = "http://127.0.0.1:8000/media/company_pic/default.png"
        try:
            if not obj.employer:
                print(f"[Serializer] No employer for job {obj.id}: {obj.title}")
                return default_url
            if obj.employer.profile_pic:
                request = self.context.get('request')
                media_root = self.context.get('settings', {}).get('MEDIA_ROOT', '')
                file_path = os.path.join(media_root, str(obj.employer.profile_pic))
                # Check if file exists
                if media_root and not os.path.exists(file_path):
                    print(f"[Serializer] Image missing for {obj.title}: {file_path}")
                    return default_url
                # Build URL
                if request:
                    url = request.build_absolute_uri(obj.employer.profile_pic.url)
                else:
                    url = f"http://127.0.0.1:8000{obj.employer.profile_pic.url}"
                print(f"[Serializer] Profile pic for {obj.title}: {url}")
                return url
            print(f"[Serializer] No profile_pic for {obj.title}")
            return default_url
        except Exception as e:
            print(f"[Serializer] Error building profile_pic for {obj.title}: {str(e)}")
            return default_url

from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django_filters import rest_framework as filters # type: ignore
from Empjob.models import Jobs

class JobFilter(filters.FilterSet):
    """
    FilterSet for Jobs model with enhanced filtering capabilities.
    """
    search = filters.CharFilter(method='filter_search', label='Search')
    location = filters.CharFilter(method='filter_location', label='Location')
    jobtype = filters.CharFilter(lookup_expr='iexact', label='Job Type')
    jobmode = filters.CharFilter(method='filter_jobmode', label='Job Mode')
    experience = filters.CharFilter(lookup_expr='iexact', label='Experience')
    lpa = filters.CharFilter(method='filter_lpa', label='Salary Range (e.g., 10-20)')
    employer = filters.NumberFilter(field_name='employer__id', label='Employer ID')
    industry = filters.CharFilter(lookup_expr='icontains', label='Industry')
    active = filters.BooleanFilter(field_name='active', label='Active Jobs Only')
    recent = filters.CharFilter(method='filter_recent', label='Recent Jobs')
    skills = filters.CharFilter(method='filter_skills', label='Required Skills')
    
    class Meta:
        model = Jobs
        fields = ['search', 'location', 'jobtype', 'jobmode', 'experience', 
                 'lpa', 'employer', 'industry', 'active', 'recent', 'skills']
    
    def filter_search(self, queryset, name, value):
        """
        Enhanced search across multiple job fields with keyword relevance.
        """
        if not value:
            return queryset
            
        search_terms = value.split()
        query = Q()
        
        for term in search_terms:
            query |= (
                Q(title__icontains=term) |  
                Q(about__icontains=term) | 
                Q(responsibility__icontains=term) | 
                Q(employer__user__full_name__icontains=term)
            )
            
        return queryset.filter(query).select_related('employer').distinct()
    
    def filter_location(self, queryset, name, value):
        if not value:
            return queryset
        
        value_lower = value.lower().strip()
        
        if value_lower == "remote":
            return queryset.filter(
                Q(location__iexact="remote") | 
                Q(jobmode__iexact="remote")
            )
        
        exact_match = queryset.filter(location__iexact=value)
        if exact_match.exists():
            return exact_match
            
        return queryset.filter(location__icontains=value)
    
    def filter_jobmode(self, queryset, name, value):
        if not value:
            return queryset
        prefix = value[:3].lower()
        return queryset.filter(jobmode__istartswith=prefix)
    
    def filter_lpa(self, queryset, name, value):
        if not value:
            return queryset
            
        try:
            if value.endswith('+'):
                min_lpa = float(value.rstrip('+'))
                return queryset.filter(lpa__gte=min_lpa)
                
            if '-' in value:
                min_lpa, max_lpa = map(float, value.split('-'))
                return queryset.filter(
                    Q(lpa__startswith=f"{int(min_lpa)}-") | 
                    Q(lpa__endswith=f"-{int(max_lpa)}") |
                    Q(lpa__gte=min_lpa, lpa__lte=max_lpa)
                )
                
            return queryset.filter(lpa=value)
        except (ValueError, TypeError):
            return queryset
    
    def filter_recent(self, queryset, name, value):
        if not value:
            return queryset
            
        now = timezone.now()
        
        if value == 'today' or value == '24h':
            start_date = now - timedelta(days=1)
        elif value == 'week' or value == '7d':
            start_date = now - timedelta(days=7)
        elif value == 'month' or value == '30d':
            start_date = now - timedelta(days=30)
        else:
            return queryset
            
        return queryset.filter(posteDate__gte=start_date)
        
    def filter_skills(self, queryset, name, value):
        if not value:
            return queryset
            
        skills = [skill.strip().lower() for skill in value.split(',')]
        query = Q()
        
        for skill in skills:
            if not skill:
                continue
                
            query |= (
                Q(title__icontains=skill) |
                Q(about__icontains=skill) |
                Q(responsibility__icontains=skill)
            )
            
        return queryset.filter(query).distinct()
    
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from Empjob.models import Jobs

from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from django.conf import settings
from django.db.models import Q

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Jobs.objects.select_related('employer').filter(active=True).order_by('-posteDate')
    serializer_class = SearchSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobFilter
    pagination_class = StandardResultsSetPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'settings': {'MEDIA_ROOT': settings.MEDIA_ROOT}
        })
        return context

class GetAllJobsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Jobs.objects.select_related('employer').filter(active=True).order_by('-posteDate')
    serializer_class = SearchSerializer
    pagination_class = StandardResultsSetPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'settings': {'MEDIA_ROOT': settings.MEDIA_ROOT}
        })
        return context

class JobAutocompleteView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([], status=status.HTTP_200_OK)
        suggestions = []
        try:
            titles = Jobs.objects.filter(
                Q(title__icontains=query) & Q(active=True)
            ).values('title').distinct()[:5]
            suggestions.extend([{'type': 'title', 'value': t['title']} for t in titles])

            locations = Jobs.objects.filter(
                Q(location__icontains=query) & Q(active=True)
            ).values('location').distinct()[:5]
            suggestions.extend([{'type': 'location', 'value': l['location']} for l in locations])

            jobtypes = Jobs.objects.filter(
                Q(jobtype__icontains=query) & Q(active=True)
            ).values('jobtype').distinct()[:5]
            suggestions.extend([{'type': 'jobtype', 'value': j['jobtype']} for j in jobtypes])

            jobmodes = Jobs.objects.filter(
                Q(jobmode__icontains=query) & Q(active=True)
            ).values('jobmode').distinct()[:5]
            suggestions.extend([{'type': 'jobmode', 'value': j['jobmode']} for j in jobmodes])

            industries = Jobs.objects.filter(
                Q(industry__icontains=query) & Q(active=True)
            ).values('industry').distinct()[:5]
            suggestions.extend([{'type': 'industry', 'value': i['industry']} for i in industries])
        except Exception as e:
            print(f"[Autocomplete] Error fetching suggestions: {str(e)}")

        suggestions = sorted(suggestions, key=lambda x: x['value'].lower())[:10]
        return Response(suggestions, status=status.HTTP_200_OK)


































class GetJobStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        action = request.data.get('action')
        try:
            job = Jobs.objects.get(id=job_id)
            
            if job.employer.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to modify this job"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if action == 'deactivate':
                job.active = False
                message = "Job deactivated successfully"
            elif action == 'activate':
                job.active = True
                message = "Job activated successfully"
            else:
                return Response(
                    {"error": "Invalid action. Use 'activate' or 'deactivate'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            job.save()
            serializer = JobSerializer(job, context={'request': request})
            return Response({
                "message": message,
                "job": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Jobs.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)


from django.shortcuts import get_object_or_404



class SavejobStatus(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        action = request.data.get('action')
        user = request.user
        
        if action not in ['save', 'unsave']:
            return Response(
                {"error": "Invalid action. Use 'save' or 'unsave'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            job = get_object_or_404(Jobs, id=job_id)
            candidate = get_object_or_404(Candidate, user=user)
            
            if action == 'save':
                saved_job, created = SavedJobs.objects.get_or_create(
                    candidate=candidate, 
                    job=job
                )
                return Response(
                    {"message": "Job saved successfully" if created else "Job already saved"},
                    status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
                )
                
            elif action == 'unsave':
                deleted_count, _ = SavedJobs.objects.filter(
                    candidate=candidate, 
                    job=job
                ).delete()
                if deleted_count > 0:
                    return Response(
                        {"message": "Job unsaved successfully"}, 
                        status=status.HTTP_200_OK
                    )
                return Response(
                    {"message": "Job was not saved"}, 
                    status=status.HTTP_200_OK
                )
                    
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CheckJobSaveStatus(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        user = request.user
        print("...................................",user)
        try:
            job = Jobs.objects.get(id=job_id)
            candidate = Candidate.objects.get(user=user)
            is_saved = SavedJobs.objects.filter(candidate=candidate, job=job).exists()
            return Response({"is_saved": is_saved}, status=status.HTTP_200_OK)
        except Jobs.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Candidate.DoesNotExist:
            return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SavedJobsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            candidate = get_object_or_404(Candidate, user=request.user)
            saved_jobs = SavedJobs.objects.filter(candidate=candidate)
            serializer = SavedJobSerializer(saved_jobs, many=True)
            return Response(
                {"data": serializer.data}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ApplicationStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        action = request.data.get('action')
        try:
            applied_job = ApplyedJobs.objects.get(id=job_id)
            if applied_job:
                applied_job.status = action
                applied_job.save()
                return Response({"message": "Status changed"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No job available"}, status=status.HTTP_204_NO_CONTENT)
        except ApplyedJobs.DoesNotExist:
            return Response({"error": "Job application not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class GetQuestions(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            questions = Question.objects.filter(job=job_id)
            serializer = QuestionSerializer(questions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        


class Applyjob(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        user = request.user
        try:
            job = Jobs.objects.get(id=job_id)
            candidate = Candidate.objects.get(user=user)
            if ApplyedJobs.objects.filter(candidate=candidate, job=job).exists():
                return Response({'message': 'You have already applied for this job.'}, status=status.HTTP_200_OK)
            
            application = ApplyedJobs.objects.create(candidate=candidate, job=job)
    
            created = Approvals.objects.create(
                candidate=candidate,
                employer=job.employer,
                job=job,
                is_approved=False,
                is_rejected=False
            )
                
            answers_data = request.data.get('answers', [])
            for answer in answers_data:
                question_id = answer.get('question')
                answer_text = answer.get('answer_text')
                try:
                    question = Question.objects.get(id=question_id, job=job)
                    Answer.objects.create(
                        candidate=candidate,
                        question=question,
                        answer_text=answer_text,
                        question_text=question.text  # Save the question text here
                    )
                except Question.DoesNotExist:
                    return Response({'message': f'Question {question_id} not found.'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'message': 'You have successfully applied for the job.'}, status=status.HTTP_200_OK)
        except Jobs.DoesNotExist:
            return Response({'message': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Candidate.DoesNotExist:
            return Response({'message': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class Applyjob(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, job_id):
#         user = request.user
#         try:
#             job = Jobs.objects.get(id=job_id)
#             candidate = Candidate.objects.get(user=user)
#             if ApplyedJobs.objects.filter(candidate=candidate, job=job).exists():
#                 return Response({'message': 'You have already applied for this job.'}, status=status.HTTP_200_OK)
            
#             application = ApplyedJobs.objects.create(candidate=candidate, job=job)
    
#             created = Approvals.objects.create(
#                 candidate=candidate,
#                 employer=job.employer,
#                 job=job,
#                 is_approved=False,
#                 is_rejected=False
#                 )
                
#             answers_data = request.data.get('answers', [])
#             for answer in answers_data:
#                 question_id = answer.get('question')
#                 answer_text = answer.get('answer_text')
#                 try:
#                     question = Question.objects.get(id=question_id, job=job)
#                     Answer.objects.create(
#                         candidate=candidate,
#                         question=question,
#                         answer_text=answer_text
#                     )
#                 except Question.DoesNotExist:
#                     return Response({'message': f'Question {question_id} not found.'}, status=status.HTTP_400_BAD_REQUEST)

#             return Response({'message': 'You have successfully applied for the job.'}, status=status.HTTP_200_OK)
#         except Jobs.DoesNotExist:
#             return Response({'message': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
#         except Candidate.DoesNotExist:
#             return Response({'message': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_application(request, job_id):
    has_applied = ApplyedJobs.objects.filter(job_id=job_id, candidate__user=request.user).exists()
    return Response({"has_applied": has_applied})




# # views.py

# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from django.utils import timezone

# from .serializer import ApprovalSerializer

# import logging
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from Empjob.models import Jobs, Approvals, ApplyedJobs  # Assuming ApplyedJobs exists
# from user_account.models import Candidate, Employer
# from .serializer import ApprovalSerializer

# # Configure logger
# logger = logging.getLogger(__name__)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def request_chat(request, job_id):
#     """
#     Create a chat request from candidate to employer
#     """
#     # Get the job
#     job = get_object_or_404(Jobs, id=job_id)
    
#     # Get candidate profile for the current user
#     try:
#         candidate = Candidate.objects.get(user=request.user)
#     except Candidate.DoesNotExist:
#         return Response({"detail": "User is not a candidate."}, status=status.HTTP_400_BAD_REQUEST)
    
#     # Check if the user has applied for this job
#     if not ApplyedJobs.objects.filter(job=job, candidate=candidate).exists():
#         return Response({"detail": "You must apply for this job before requesting a chat."}, status=status.HTTP_400_BAD_REQUEST)
    
#     # Get employer
#     employer = job.employer
    
#     # Check if there's already a request
#     approval, created = Approvals.objects.get_or_create(
#         job=job,
#         candidate=candidate,
#         employer=employer,
#         defaults={
#             'is_requested': True,
#             'is_approved': False,
#             'is_rejected': False,
#             'requested_at': timezone.now()
#         }
#     )
    
#     # If not created, and not already approved or rejected, update it
#     if not created:
#         if approval.is_approved:
#             return Response({"detail": "Chat already approved."}, status=status.HTTP_200_OK)
#         elif approval.is_rejected:
#             return Response({"detail": "Chat request was rejected."}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             approval.is_requested = True
#             approval.requested_at = timezone.now()
#             approval.save()
#             return Response({"detail": "Chat request already pending."}, status=status.HTTP_200_OK)
    
#     return Response({"detail": "Chat request sent successfully."}, status=status.HTTP_201_CREATED)

# import logging
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from Empjob.models import Jobs, Approvals
# from user_account.models import Employer, Candidate

# logger = logging.getLogger(__name__)



# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def check_chat_status(request, job_id):
#     try:
#         user = request.user
#         logger.info(f"Chat status check - User: {user.id} ({user.email}), Job: {job_id}")
        
#         job = Jobs.objects.select_related('employer__user').get(id=job_id)
#         approval = Approvals.objects.select_related('candidate__user').filter(job=job).first()

#         response = {
#             "system": {
#                 "status": "success",
#                 "user_id": user.id,
#                 "job_id": job.id,
#                 "is_job_owner": False,
#                 "is_approved_candidate": False,
#                 "debug": {
#                     "job_owner_id": getattr(job.employer, 'user_id', None),
#                     "approval_candidate_id": getattr(approval, 'candidate.user_id', None) if approval else None,
#                     "approval_status": getattr(approval, 'is_approved', None),
#                     "approval_id": getattr(approval, 'id', None)
#                 }
#             },
#             "chat": {
#                 "exists": False,
#                 "requested": False,
#                 "approved": False,
#                 "rejected": False,
#                 "pending": False,
#                 "can_chat": False,
#                 "unread_count": 0,
#                 "approval_id": None,
#                 "last_updated": None
#             }
#         }

#         # Check employer access
#         if hasattr(user, 'employer') and job.employer.user.id == user.id:
#             response['system']['is_job_owner'] = True
#             unread_count = Approvals.objects.filter(
#                 job=job,
#                 is_approved=False,
#                 is_rejected=False
#             ).count()
            
#             if approval:
#                 response['chat'].update({
#                     "exists": True,
#                     "requested": True,
#                     "approved": approval.is_approved,
#                     "rejected": approval.is_rejected,
#                     "pending": not approval.is_approved and not approval.is_rejected,
#                     "can_chat": approval.is_approved,
#                     "unread_count": unread_count,
#                     "approval_id": approval.id,
#                     "last_updated": approval.updated_at.isoformat() if approval.updated_at else None
#                 })
#             return Response(response, status=200)

#         # Check candidate access
#         if hasattr(user, 'candidate') and approval and approval.candidate.user.id == user.id:
#             response['system']['is_approved_candidate'] = approval.is_approved
#             response['chat'].update({
#                 "exists": True,
#                 "requested": True,
#                 "approved": approval.is_approved,
#                 "rejected": approval.is_rejected,
#                 "pending": not approval.is_approved and not approval.is_rejected,
#                 "can_chat": approval.is_approved,
#                 "approval_id": approval.id,
#                 "last_updated": approval.updated_at.isoformat() if approval.updated_at else None
#             })
#             return Response(response, status=200)

#         return Response(response, status=200)

#     except Jobs.DoesNotExist:
#         logger.error(f"Job not found - JobID: {job_id}")
#         return Response({
#             "system": {
#                 "status": "error",
#                 "message": "Job not found"
#             }
#         }, status=404)
#     except Exception as e:
#         logger.error(f"Chat status error: {str(e)}")
#         return Response({
#             "system": {
#                 "status": "error",
#                 "message": "Internal server error"
#             }
#         }, status=500)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def employer_approvals(request):
#     """
#     Get all pending chat requests for an employer
#     """
#     # Get employer profile
#     try:
#         employer = Employer.objects.get(user=request.user)
#     except Employer.DoesNotExist:
#         return Response({"detail": "User is not an employer."}, status=status.HTTP_400_BAD_REQUEST)
    
#     # Get pending requests (is_requested=True, is_approved=False, is_rejected=False)
#     pending_requests = Approvals.objects.filter(
#         employer=employer,
#         is_requested=True,
#         is_approved=False,
#         is_rejected=False
#     )
    
#     # Serialize the data
#     serializer = ApprovalSerializer(pending_requests, many=True)
    
#     return Response(serializer.data)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def employer_approvals_count(request):
#     """
#     Get count of pending chat requests for an employer
#     """
#     # Get employer profile
#     try:
#         employer = Employer.objects.get(user=request.user)
#     except Employer.DoesNotExist:
#         return Response({"count": 0})
    
#     # Get count of pending requests
#     count = Approvals.objects.filter(
#         employer=employer,
#         is_requested=True,
#         is_approved=False,
#         is_rejected=False
#     ).count()
    
#     return Response({"count": count})

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def manage_chat_request(request, approval_id):
#     """
#     Approve or reject a chat request
#     """
#     # Get employer profile
#     try:
#         employer = Employer.objects.get(user=request.user)
#     except Employer.DoesNotExist:
#         return Response({"detail": "User is not an employer."}, status=status.HTTP_400_BAD_REQUEST)
    
#     # Get the approval
#     approval = get_object_or_404(Approvals, id=approval_id, employer=employer)
    
#     # Check the action
#     action = request.data.get('action')
    
#     if action == 'approve':
#         approval.is_approved = True
#         approval.is_rejected = False
#         approval.save()
#         return Response({"detail": "Chat request approved."})
    
#     elif action == 'reject':
#         approval.is_rejected = True
#         approval.is_approved = False
#         approval.save()
#         return Response({"detail": "Chat request rejected."})
    
#     else:
#         return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)