from rest_framework import serializers
from user_account.models import *
from Empjob.models import *
from django.utils import timezone

from rest_framework import serializers
from Empjob.models import Jobs, Question,Answer
from user_account.api.serializer import *



class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type']




class PostJobSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    
    class Meta:
        model = Jobs
        fields = '__all__'
        depth = 1  
    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        employer = self.context['employer']
        job = Jobs.objects.create(employer=employer, **validated_data)
        
        # Create associated questions
        for question_data in questions_data:
            Question.objects.create(job=job, **question_data)
            
        return job
from rest_framework import serializers
from user_account.models import Employer
from Empjob.models import Jobs, Question, ApplyedJobs
from django.contrib.auth import get_user_model

User = get_user_model()

class EmployerSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.CharField(source='user.id', read_only=True)
    profile_pic = serializers.SerializerMethodField()
    
    class Meta:
        model = Employer
        fields = [
            'profile_pic', 'user_id', 'user_email', 'phone', 'id', 'industry',
            'user_full_name', 'headquarters', 'address', 'about', 'website_link'
        ]
    
    def get_profile_pic(self, obj):
        if obj.profile_pic:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return f"http://127.0.0.1:8000{obj.profile_pic.url}"
        return None

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer()
    questions = serializers.SerializerMethodField()
    applications_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    

    class Meta:
        model = Jobs
        fields = '__all__'
    def get_questions(self, obj):
        questions = Question.objects.filter(job=obj)
        return QuestionSerializer(questions, many=True).data

    def get_applications_count(self, obj):
        return ApplyedJobs.objects.filter(job=obj).count()

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request:
            return obj.employer.user == request.user or request.user.is_staff
        return False
   

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'

class CandidateSerializer(serializers.ModelSerializer):
    education = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Candidate
        fields = '__all__'

    def get_education(self, obj):
        educations = Education.objects.filter(user=obj.user)
        return EducationSerializer(educations, many=True).data

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'

class ApplyedForJobsSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer()
    answers = serializers.SerializerMethodField()

    class Meta:
        model = ApplyedJobs
        fields = '__all__'

    def get_answers(self, obj):
        answers = Answer.objects.filter(candidate=obj.candidate, question__job=obj.job)
        return AnswerSerializer(answers, many=True).data

class ApplicationSerializer(serializers.ModelSerializer):
    employer_name = serializers.SerializerMethodField()
    employer_id = serializers.SerializerMethodField()
    applications = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    
    class Meta:
        model = Jobs
        fields = '__all__'

    def get_employer_name(self, obj):
        return obj.employer.user.full_name
    
    def get_employer_id(self, obj):
        return obj.employer.id

    def get_applications(self, obj):
        applications = ApplyedJobs.objects.filter(job=obj)
        serializer = ApplyedForJobsSerializer(applications, many=True)
        return serializer.data
    
    def get_questions(self, obj):
        questions = Question.objects.filter(job=obj)
        return QuestionSerializer(questions, many=True).data

class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer()
    
    class Meta:
        model = SavedJobs
        fields = '__all__'

class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approvals
        fields = ['id', 'candidate', 'employer', 'job', 'is_approved', 'is_rejected']

class ApplyedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer()
    candidate_name = serializers.SerializerMethodField()
   
    class Meta:
        model = ApplyedJobs
        fields = ['id', 'job', 'status', 'candidate', 'applyed_on', 'candidate_name']
    
    
    def get_candidate_name(self, obj):
        candidate = Candidate.objects.get(id=obj.candidate_id)  
        return candidate.user.full_name
    
# 

# serializers.py
from rest_framework import serializers
from Empjob.models import Approvals

class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approvals
        fields = ['id', 'candidate', 'employer', 'job', 'is_requested', 
                 'is_approved', 'is_rejected', 'requested_at']
        



from rest_framework import serializers
from user_account.models import *
from Empjob.models import *

# Question Serializers
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type']

# Answer Serializer with Question Text
class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    
    class Meta:
        model = Answer
        fields = ['id', 'candidate', 'question', 'question_text', 'answer_text']

# Application Serializers
class ApplyedForJobsSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer()
    answers = serializers.SerializerMethodField()

    class Meta:
        model = ApplyedJobs
        fields = '__all__'

    def get_answers(self, obj):
        answers = Answer.objects.filter(candidate=obj.candidate, question__job=obj.job)
        return AnswerSerializer(answers, many=True, context=self.context).data
    






class JobSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jobs
        fields = ['title', 'location', 'jobtype', 'jobmode', 'industry','profile_pic']



from rest_framework import serializers
from Empjob.models import Jobs
from user_account.models import Employer
import os

class EmployerSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Employer
        fields = [
            'id', 'user_full_name', 'profile_pic', 'user_email',
            'phone', 'website_link', 'headquarters', 'industry', 
            'address', 'about'
        ]

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