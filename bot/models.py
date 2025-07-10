from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class CollegeData(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='data_points')
    question = models.TextField()
    answer = models.TextField()
    keywords = models.TextField(help_text="Comma-separated keywords", blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question[:50]

class Conversation(models.Model):
    user_identifier = models.CharField(max_length=100, blank=True)
    user_name = models.CharField(max_length=100, blank=True)
    user_phone = models.CharField(max_length=20, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user_name if self.user_name else 'Anonymous'} - {self.start_time}"

class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('bot', 'Bot'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"
