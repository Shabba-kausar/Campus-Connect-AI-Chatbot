from django.contrib import admin
from .models import Category, CollegeData, Conversation, Message

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(CollegeData)
class CollegeDataAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'last_updated')
    list_filter = ('category', 'last_updated')
    search_fields = ('question', 'answer', 'keywords')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_phone', 'start_time', 'last_updated')
    list_filter = ('start_time', 'last_updated')
    search_fields = ('user_name', 'user_phone', 'user_identifier')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'content', 'timestamp')
    list_filter = ('sender', 'timestamp')
    search_fields = ('content',)
