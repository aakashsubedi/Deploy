from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    # Authentication
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('profile/', views.profile, name='profile'),
    path('profile/picture/<int:picture_id>/delete/', views.delete_picture, name='delete_picture'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Matching
    path('explore/', views.explore, name='explore'),
    path('like/<int:user_id>/', views.like_user, name='like_user'),
    path('pass/<int:user_id>/', views.pass_user, name='pass_user'),
    path('matches/', views.matches, name='matches'),
    
    # Messaging
    path('messages/', views.conversations, name='conversations'),
    path('messages/<int:conversation_id>/', views.chat, name='chat'),
    path('messages/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('api/profile/<int:profile_id>/', views.get_profile_details, name='get_profile_details'),
    
    # Media files serving
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
        'show_indexes': True
    }),
]

# Add media serving for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 