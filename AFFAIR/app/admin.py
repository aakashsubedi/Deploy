from django.contrib import admin
from .models import UserProfile, UserPicture, Match, Conversation, Message, Interest

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'age', 'location', 'occupation', 'last_active')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('gender',)

@admin.register(UserPicture)
class UserPictureAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'order')
    list_filter = ('user_profile__user__username',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user_from', 'user_to', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user_from__username', 'user_to__username')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'created_at')
    search_fields = ('user1__username', 'user2__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'content', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',) 