from django.db import models
from user_account.models import Candidate, Employer
from Empjob.models import ApplyedJobs

class ChatRoom(models.Model):
    """Represents a chat room between a candidate and an employer."""
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='sender_message',
        help_text="The candidate participating in the chat."
    )
    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text="The employer participating in the chat."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the chat room was created."
    )

    def __str__(self):
        """String representation of the chat room."""
        return f"Chat between {self.candidate} and {self.employer}"

class ChatMessage(models.Model):
    """Represents a single message in a chat room."""
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        help_text="The chat room this message belongs to."
    )
    message = models.TextField(
        default="",
        null=True,
        blank=True,
        help_text="The text content of the message (optional if media is present)."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the message was sent."
    )
    sendername = models.TextField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Name of the sender (e.g., candidate or employer name)."
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Indicates if the message has been read by the recipient."
    )
    is_send = models.BooleanField(
        default=False,
        help_text="Indicates if the message has been successfully sent."
    )
    file_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="URL of any attached media file (e.g., image, video)."
    )
   

    def __str__(self):
        """String representation of the chat message."""
        return f"{self.sendername} in {self.chatroom}: {self.message or 'Media message'}"

















