from django.conf import settings
from django.db import models


class FAQ(models.Model):
    class Category(models.TextChoices):
        GENERAL = 'general', 'General'
        DONOR = 'donor', 'Donor'
        BLOOD_REQUEST = 'blood_request', 'Blood Request'
        ACCOUNT = 'account', 'Account'
        APP = 'app', 'App'

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class SupportRequest(models.Model):
    class RequestType(models.TextChoices):
        CONTACT = 'contact', 'Contact Support'
        PROBLEM = 'problem', 'Report a Problem'
        FEEDBACK = 'feedback', 'Feedback'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_requests',
    )
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices,
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_request_type_display()} - {self.subject}'


