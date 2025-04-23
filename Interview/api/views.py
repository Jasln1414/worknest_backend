from modulefinder import test
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializer import SheduleInterviewSerializer, InterviewSheduleSerializer
from user_account.models import Employer, Candidate
from Interview.models import InterviewShedule
from Empjob.models import Jobs, ApplyedJobs
from rest_framework.permissions import IsAuthenticated, AllowAny
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from Interview.tasks import send_shedule_mail, cancell_shedule_mail
from datetime import datetime

class InterviewScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("InterviewScheduleView: Processing POST request")
        user = request.user
        try:
            employer = Employer.objects.get(user=user)
        except Employer.DoesNotExist:
            return Response({"message": "Employer not found"}, status=status.HTTP_404_NOT_FOUND)

        candidate_id = request.data.get('candidate')
        job_id = request.data.get('job')
        date = request.data.get('date')

        try:
            candidate = Candidate.objects.get(id=candidate_id)
            job = Jobs.objects.get(id=job_id)
            email = candidate.user.email
            title = job.title
            username = employer.user.full_name
            print(f"Email: {email}, Date: {date}, Username: {username}, Title: {title}")
        except Candidate.DoesNotExist:
            print("Candidate not found")
            return Response({"message": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)
        except Jobs.DoesNotExist:
            print("Job not found")
            return Response({"message": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = SheduleInterviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                # Update ApplyedJobs
                try:
                    application = ApplyedJobs.objects.get(candidate_id=candidate_id, job_id=job_id)
                    application.status = 'Interview Scheduled'
                    application.save()
                except ApplyedJobs.DoesNotExist:
                    print("Warning: No matching job application")
                # Queue email
                try:
                    send_shedule_mail.delay(email, date, username, title)
                    print("Email task queued successfully")
                except Exception as e:
                    print(f"Warning: Failed to queue email task: {e}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error saving schedule: {e}")
                return Response({"message": "Failed to save schedule"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CancelApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            employer = Employer.objects.get(user=user)
        except Employer.DoesNotExist:
            return Response({"message": "Employer not found"}, status=status.HTTP_404_NOT_FOUND)

        candidate_id = request.data.get('candidate_id')
        job_id = request.data.get('job_id')

        try:
            job = Jobs.objects.get(id=job_id)
            candidate = Candidate.objects.get(id=candidate_id)
            application = InterviewShedule.objects.get(job=job_id, candidate=candidate_id)
            applyed = ApplyedJobs.objects.get(candidate=candidate_id, job=job_id)
            email = candidate.user.email
            date = application.date
            title = job.title
            username = employer.user.full_name
        except (Jobs.DoesNotExist, Candidate.DoesNotExist, InterviewShedule.DoesNotExist, ApplyedJobs.DoesNotExist) as e:
            print(f"Error: {str(e)}")
            return Response({"message": "Required data not found"}, status=status.HTTP_404_NOT_FOUND)

        application.active = False
        application.status = "Canceled"
        applyed.status = 'Interview Cancelled'
        application.save()
        applyed.save()
        try:
            cancell_shedule_mail.delay(email, date, username, title)
            print("Cancel email task queued successfully")
        except Exception as e:
            print(f"Warning: Failed to queue cancel email task: {e}")
        return Response({"message": "Application cancelled successfully"}, status=status.HTTP_200_OK)

class getShedulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        print(f"getShedulesView: User {user}")
        try:
            try:
                candidate = Candidate.objects.get(user=user)
                shedules = InterviewShedule.objects.filter(candidate=candidate)
            except Candidate.DoesNotExist:
                employer = Employer.objects.get(user=user)
                shedules = InterviewShedule.objects.filter(employer=employer)
        
            print(f"Schedules...........................: {shedules}")
            serializer = InterviewSheduleSerializer(shedules, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (Candidate.DoesNotExist, Employer.DoesNotExist):
            return Response({"message": "User is neither a candidate nor an employer"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error: {e}")
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InterviewView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("InterviewView: Processing POST request", request.data)
        roomId = request.data.get("roomId")
        interviewId = request.data.get("interviewId")
        try:
            interview = InterviewShedule.objects.get(id=interviewId)
            candidate_id = interview.candidate.id
            print(f"Interview: {interview}, Candidate ID: {candidate_id}")
            message = f'Interview call - {roomId} - {interviewId}'
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notification_{candidate_id}',
                {
                    'type': 'notify_message',
                    'message': {
                        'text': message,
                        'sender': "InterviewSystem",
                        'is_read': False,
                        'timestamp': datetime.now().isoformat(),
                        'chat_id': None
                    },
                    'unread_count': 1
                }
            )
            return Response({"message": "Notification sent"}, status=status.HTTP_200_OK)
        except InterviewShedule.DoesNotExist:
            print("Interview not found")
            return Response({"message": "No interview data found"}, status=status.HTTP_404_NOT_FOUND)
class InterviewStatusView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("InterviewStatusView: Processing POST request", request.data)
        interviewId = request.data.get('interviewId')
        jobId = request.data.get('jobId')
        candidateId = request.data.get('candidateId')
        action = request.data.get('action')

        try:
            job = Jobs.objects.get(id=jobId)
            candidate = Candidate.objects.get(id=candidateId)
            interview = InterviewShedule.objects.get(id=interviewId)
            applyedjobs = ApplyedJobs.objects.get(candidate=candidate, job=job)
        except (Jobs.DoesNotExist, Candidate.DoesNotExist, InterviewShedule.DoesNotExist, ApplyedJobs.DoesNotExist):
            print("Required data not found")
            return Response({"message": "Something went wrong"}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            interview.status = 'Selected'
            interview.selected = True
            applyedjobs.status = 'Accepted'
        elif action == 'reject':
            interview.status = 'Rejected'
            interview.selected = True
            applyedjobs.status = 'Rejected'
        else:
            return Response({"message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        interview.save()
        applyedjobs.save()
        return Response({"message": "Status changed"}, status=status.HTTP_200_OK)

def testView(request):
    test.delay()
    return HttpResponse("Done")





# from modulefinder import test
# from django.http import HttpResponse
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .serializer import *
# from user_account.models import *
# from Interview.models import *
# from Empjob.models import *

# from rest_framework.permissions import IsAuthenticated
# from rest_framework.permissions import AllowAny
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from Interview.tasks import send_shedule_mail,cancell_shedule_mail
# from Empjob.api.serializer import *
# from Empjob.models import *

# class InterviewSheduleView(APIView):
#     permission_classes=[IsAuthenticated]
#     def post(self, request):
#         print("step1")
#         user = request.user
#         employer = Employer.objects.get(user=user)
#         candidate_id = request.data.get('candidate')
#         job_id = request.data.get('job')
#         date = request.data.get('date')
       
#         try:
#             candidate=Candidate.objects.get(id=candidate_id)
#             job=Jobs.objects.get(id=job_id)
#             email=candidate.user.email
#             title=job.title
#             username = employer.user.full_name
#             print(email,date,user,title)
#         except Candidate.DoesNotExist:
#             print("error")
        
        
#         print(request.data)
#         serializer = SheduleInterviewSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             send_shedule_mail.delay(email,date,username,title)
#             print(serializer.data)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class CancelApplicationView(APIView):
#     permission_classes=[IsAuthenticated]
#     def post(self,request):
#         user=request.user
#         employer = Employer.objects.get(user=user)
#         candidate_id = request.data.get('candidate_id')
#         job_id = request.data.get('job_id')
#         job=Jobs.objects.get(id=job_id)
#         candidate=Candidate.objects.get(id=candidate_id)
#         application = InterviewShedule.objects.get(job=job_id,candidate=candidate_id)
#         applyed = ApplyedJobs.objects.get(candidate=candidate_id,job=job_id)
#         email=candidate.user.email
#         date=application.date
#         title=job.title
#         username = employer.user.full_name
#         try:
#             if application:
#                 application.active = False
#                 application.status = "Canceled"
#                 applyed.status='Interview Cancelled'
#                 application.save()
#                 applyed.save()
#                 cancell_shedule_mail.delay(email,date,username,title)
                
#                 return Response({"message":"application cancelled sucessfull"},status=status.HTTP_200_OK)
#         except application.DoesNotExist:
#             return Response({"message":"something went wrong"},status=status.HTTP_404_NOT_FOUND)
        
# class getShedulesView(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request):
#         user = request.user
#         print("5cr67vt8by9un0im",user)
#         try:
#             try:
#                 candidate = Candidate.objects.get(user=user)
#                 shedules=InterviewShedule.objects.filter(candidate=candidate)
#             except Candidate.DoesNotExist:
#                 employer = Employer.objects.get(user=user)
#                 shedules=InterviewShedule.objects.filter(employer=employer)
       
#             print(shedules)
#             serializer = InterviewSheduleSerializer(shedules, many=True)
#             if serializer:
#                 return Response (serializer.data,status=status.HTTP_200_OK)
            
#         except (Candidate.DoesNotExist, Employer.DoesNotExist):
#             return Response({"message": "User is neither a candidate nor an employer"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             print(e)
#             return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class InterviewView(APIView):
#     permission_classes=[AllowAny]
#     def post(self,request):
#         print(request.data)
#         roomId = request.data.get("roomId")
#         interviewId = request.data.get("interviewId")
#         try:
#             interview = InterviewShedule.objects.get(id = interviewId)
#             candidate_id =interview.candidate.id 
#             print(interview)
#             print("candidate",candidate_id)
#             message = f'Interview call - {roomId} - {interviewId}'
#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)(
#                     f'notifications_{candidate_id}',  
#                     {
#                         'type': 'send_notification',
#                         'message': message
#                     }
#                 )
#             return Response(status=status.HTTP_200_OK)
            
#         except InterviewShedule.DoesNotExist:
#             return Response({"message":"no interview data found"},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    

# class InterviewStatusView(APIView):
#         permission_classes=[AllowAny]
#         def post(self,request):
#             print(request.data)
#             interviewId = request.data.get('interviewId')
#             jobId =request.data.get('jobId')
#             candidateId = request.data.get('candidateId')
#             action = request.data.get('action')
#             job = Jobs.objects.get(id=jobId)
#             candidate = Candidate.objects.get(id=candidateId)
#             try:
#                 interview = InterviewShedule.objects.get(id=interviewId)
#                 applyedjobs = ApplyedJobs.objects.get(candidate=candidate,job=job)
#             except:
#                 return Response({"message":"something went wrong"},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
#             if action =='accept':
#                 if interview and applyedjobs:
#                     interview.status = 'Selected'
#                     interview.selected = True
#                     applyedjobs.status = 'Accepted'
#                     interview.save()
#                     applyedjobs.save()
#                 else:
#                     return Response({"message":"cannot make a change now"},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
#             if action =='reject':
#                 if interview and applyedjobs:
#                     interview.status = 'Rejected'
#                     interview.selected = True
#                     applyedjobs.status = 'Rejected'
#                     interview.save()
#                     applyedjobs.save()
#                 else:
#                     return Response({"message":"cannot make a change now"},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

#             return Response({"message":"status changeed"},status=status.HTTP_200_OK)

# def testView(request):
#     test.delay()
#     return HttpResponse("Done")
  