# chat/views.py
from venv import logger
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
import cloudinary.uploader

from chat.models import ChatMessage, ChatRoom
from user_account.models import Candidate, Employer
from chat.api.serializer import ChatMessageSerializer, ChatRoomSerializer

from rest_framework.permissions import AllowAny
class ChatMessagesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, candidate_id, employer_id):
        try:
            # First try to find the chatroom
            chatroom = get_object_or_404(ChatRoom, 
                                      candidate_id=candidate_id,
                                      employer_id=employer_id)
            
            # Then get the messages from that room
            chatmessages = ChatMessage.objects.filter(chatroom=chatroom).order_by('timestamp')
            
            # Update read status
            self.update_unread_messages(request.user.id, candidate_id, employer_id)
            
            serializer = ChatMessageSerializer(chatmessages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    def update_unread_messages(self, user_id, candidate_id, employer_id):
        """
        Mark messages as read when the recipient views them
        """
        try:
            # Determine if the current user is the candidate or employer
            is_candidate = str(user_id) == str(candidate_id)
            
            # Find the chat room
            chatroom = ChatRoom.objects.get(
                candidate_id=candidate_id,
                employer_id=employer_id
            )
            
            # Mark messages as read (only those sent to the current user)
            if is_candidate:
                # If user is candidate, mark employer's messages as read
                ChatMessage.objects.filter(
                    chatroom=chatroom,
                    sendername__isnull=False,  # Message has a sender
                    is_read=False,  # Not already read
                ).exclude(
                    sendername=candidate_id  # Not sent by the candidate
                ).update(is_read=True)
            else:
                # If user is employer, mark candidate's messages as read
                ChatMessage.objects.filter(
                    chatroom=chatroom,
                    sendername__isnull=False,  # Message has a sender
                    is_read=False,  # Not already read
                ).exclude(
                    sendername=employer_id  # Not sent by the employer
                ).update(is_read=True)
                
        except Exception as e:
            print(f"Error updating unread messages: {e}")


class ChatsView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user = request.user
        try:
            candidate = Candidate.objects.get(user=user)
            chatroom = ChatRoom.objects.filter(candidate=candidate)
        except Candidate.DoesNotExist:
            try:
                employer = Employer.objects.get(user=user)
                chatroom = ChatRoom.objects.filter(employer=employer)
            except Employer.DoesNotExist:
                return Response({'error': 'User is neither a candidate nor an employer'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ChatRoomSerializer(chatroom, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)










class MediaUploadView(generics.CreateAPIView):
    """API view to upload media files (images and videos) to Cloudinary."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handle file upload requests and return the uploaded file's URL.

        Args:
            request: HTTP request containing the file to upload.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: JSON response with the file URL or an error message.
        """
        try:
            file = request.FILES.get("file")
            if not file:
                return Response({"error": "No file was submitted"}, status=status.HTTP_400_BAD_REQUEST)

            content_type = file.content_type
            if content_type.startswith('image/'):
                upload_result = cloudinary.uploader.upload(file)
                file_url = upload_result.get('secure_url')
            elif content_type.startswith('video/'):
                upload_result = cloudinary.uploader.upload_large(file, resource_type="video")
                file_url = upload_result.get('secure_url')
            else:
                return Response({"error": "Unsupported file type"}, status=status.HTTP_400_BAD_REQUEST)

            # Return only file_url since media_type isn't in the model
            return Response({"file_url": file_url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to upload media", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# chat/views.py
class NotificationCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.GET.get('user_id')
        if not user_id:
            return Response({'error': 'user_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            try:
                candidate = Candidate.objects.get(id=user_id)
                chatrooms = ChatRoom.objects.filter(candidate=candidate)
                username = candidate.user.get_username()
            except Candidate.DoesNotExist:
                employer = Employer.objects.get(id=user_id)
                chatrooms = ChatRoom.objects.filter(employer=employer)
                username = employer.user.get_username()

            unread_count = ChatMessage.objects.filter(
                chatroom__in=chatrooms,
                is_read=False
            ).exclude(sendername=username).count()

            notifications = ChatMessage.objects.filter(
                chatroom__in=chatrooms,
                is_read=False
            ).exclude(sendername=username).order_by('-timestamp')[:5]

            notification_data = [
                {
                    'id': msg.id,
                    'sendername': msg.sendername,
                    'message': msg.message,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'chatroom': msg.chatroom.id,
                    'is_read': msg.is_read
                } for msg in notifications
            ]

            return Response({
                'unread_count': unread_count,
                'notifications': notification_data
            }, status=status.HTTP_200_OK)

        except (Candidate.DoesNotExist, Employer.DoesNotExist):
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from chat.models import ChatRoom, ChatMessage

class MarkMessagesReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, candidate_id, employer_id):
        try:
            chatroom = ChatRoom.objects.get(candidate_id=candidate_id, employer_id=employer_id)
            ChatMessage.objects.filter(chatroom=chatroom, is_read=False).update(is_read=True)
            return Response({'status': 'success'})
        except ChatRoom.DoesNotExist:
            return Response({'error': 'Chat room not found'}, status=404)


























