from rest_framework import serializers
from Interview.models import *
from Empjob.models import *
from Empjob.api.serializer import JobSerializer

class SheduleInterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewShedule
        fields = ['id','candidate', 'employer', 'job', 'date']
        read_only_fields = ['employer']

    def create(self, validated_data): 
        request = self.context.get('request')
        user = request.user
        employer = Employer.objects.get(user=user)
        validated_data['employer'] = employer
        return super().create(validated_data)


from rest_framework import serializers
from Interview.models import InterviewShedule
from Empjob.models import ApplyedJobs, Jobs
from user_account.models import Candidate, Employer
from Empjob.api.serializer import JobSerializer

# class InterviewSheduleSerializer(serializers.ModelSerializer):
#     employer_name = serializers.SerializerMethodField()
#     candidate_name = serializers.SerializerMethodField()
#     applyDate = serializers.SerializerMethodField()
#     job_title = serializers.SerializerMethodField()
    
#     # Include a simplified job object instead of the full JobSerializer
#     # to avoid performance issues but still provide essential job info
#     job_info = serializers.SerializerMethodField()
    
#     class Meta:
#         model = InterviewShedule
#         fields = [
#             'id', 'candidate', 'employer', 'job', 'date',
#             'active', 'selected', 'status', 'employer_name',
#             'applyDate', 'candidate_name', 'job_title', 'job_info'
#         ]
    
#     def get_employer_name(self, obj):
#         if obj.employer and hasattr(obj.employer, 'user') and hasattr(obj.employer.user, 'full_name'):
#             return obj.employer.user.full_name
#         return "Unknown Employer"
    
#     def get_applyDate(self, obj):
#         try:
#             applied_job = ApplyedJobs.objects.filter(job=obj.job, candidate=obj.candidate).first()
#             if applied_job:
#                 return applied_job.applyed_on
#         except Exception as e:
#             print(f"Error fetching apply date: {e}")
#         return None
    
#     def get_candidate_name(self, obj):
#         if obj.candidate and hasattr(obj.candidate, 'user') and hasattr(obj.candidate.user, 'full_name'):
#             return obj.candidate.user.full_name
#         return "Unknown Candidate"
    
#     def get_job_title(self, obj):
#         if obj.job and hasattr(obj.job, 'title'):
#             return obj.job.title
#         return "Unknown Job"
    
#     def get_job_info(self, obj):
#         if not obj.job:
#             return {
#                 "title": "Unknown Job",
#                 "id": None,
#                 "location": None,
#                 "experience": None,
#                 "lpa": None
#             }
        
#         return {
#             "title": obj.job.title,
#             "id": obj.job.id,
#             "location": getattr(obj.job, 'location', None),
#             "experience": getattr(obj.job, 'experience', None),
#             "lpa": getattr(obj.job, 'lpa', None)
#         }



# from rest_framework import serializers
# from Interview.models import InterviewShedule
# from Empjob.models import ApplyedJobs
# from django.utils import timezone
# from django.core.exceptions import ObjectDoesNotExist

# from user_account.models import Employer

# class SheduleInterviewSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InterviewShedule
#         fields = [
#             'id', 'candidate', 'employer', 'job', 'date',
#             'selected', 'active', 'status', 'notification_read', 'created_at'
#         ]
#         read_only_fields = ['employer', 'notification_read', 'created_at', 'status']

#     def validate_date(self, value):
#         if value <= timezone.now():
#             raise serializers.ValidationError("Interview date must be in the future")
#         return value

#     def create(self, validated_data):
#         request = self.context.get('request')
#         try:
#             employer = Employer.objects.get(user=request.user)
#         except ObjectDoesNotExist:
#             raise serializers.ValidationError("Employer profile not found")

#         validated_data['employer'] = employer
        
#         # Ensure candidate has applied for the job
#         if not ApplyedJobs.objects.filter(
#             job=validated_data['job'],
#             candidate=validated_data['candidate']
#         ).exists():
#             raise serializers.ValidationError("Candidate has not applied for this job")

#         return super().create(validated_data)

# class InterviewSheduleSerializer(serializers.ModelSerializer):
#     employer_name = serializers.SerializerMethodField()
#     candidate_name = serializers.SerializerMethodField()
#     apply_date = serializers.SerializerMethodField()
#     job_title = serializers.SerializerMethodField()
#     job_info = serializers.SerializerMethodField()
#     time_until_interview = serializers.SerializerMethodField()

#     class Meta:
#         model = InterviewShedule
#         fields = [
#             'id', 'candidate', 'employer', 'job', 'date', 'selected',
#             'active', 'status', 'notification_read', 'created_at',
#             'employer_name', 'candidate_name', 'apply_date', 'job_title',
#             'job_info', 'time_until_interview'
#         ]
#         read_only_fields = ['created_at', 'notification_read']

#     def get_employer_name(self, obj):
#         return obj.employer.user.full_name if obj.employer.user else ''

#     def get_apply_date(self, obj):
#         try:
#             return ApplyedJobs.objects.get(
#                 job=obj.job,
#                 candidate=obj.candidate
#             ).applyed_on
#         except ObjectDoesNotExist:
#             return None

#     def get_candidate_name(self, obj):
#         return obj.candidate.user.full_name if obj.candidate.user else ''

#     def get_job_title(self, obj):
#         return obj.job.title if obj.job else ''

#     def get_job_info(self, obj):
#         return {
#             "id": obj.job.id,
#             "title": obj.job.title,
#             "location": obj.job.location,
#             "experience": obj.job.experience,
#             "employment_type": obj.job.employment_type,
#             "lpa": obj.job.lpa
#         } if obj.job else {}

#     def get_time_until_interview(self, obj):
#         if obj.date > timezone.now():
#             delta = obj.date - timezone.now()
#             days = delta.days
#             hours, remainder = divmod(delta.seconds, 3600)
#             minutes = remainder // 60
#             return f"{days}d {hours}h {minutes}m remaining"
#         return "Expired"





class InterviewSheduleSerializer(serializers.ModelSerializer):
    employer_name = serializers.SerializerMethodField()
    candidate_name = serializers.SerializerMethodField()
    apply_date = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    job_info = serializers.SerializerMethodField()

    class Meta:
        model = InterviewShedule
        fields = [
            'id', 'candidate', 'employer', 'job', 'date',
            'active', 'selected', 'status', 'employer_name',
            'apply_date', 'candidate_name', 'job_title', 'job_info'
        ]

    def get_job_info(self, obj):
        job = obj.job
        if not job:
            return {}
            
        return {
            "title": job.title,
            "id": job.id,
            "location": job.location,
            "experience": job.experience,
            "lpa": job.lpa,
            # Remove employment_type if not needed or add to Jobs model
            # "employment_type": job.employment_type  
        }
    
    # Keep other get_* methods the same
    def get_employer_name(self, obj):
        return obj.employer.user.full_name if obj.employer.user else ''
    
    def get_apply_date(self, obj):
        try:
            return ApplyedJobs.objects.get(
                job=obj.job,
                candidate=obj.candidate
            ).applyed_on
        except ApplyedJobs.DoesNotExist:
            return None
    
    def get_candidate_name(self, obj):
        return obj.candidate.user.full_name if obj.candidate.user else ''
    
    def get_job_title(self, obj):
        return obj.job.title if obj.job else ''