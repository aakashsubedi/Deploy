from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        import app.models  # Import signals
        
        # Only import and run this when the app is ready and not during initialization
        from django.core.management import call_command
        import django
        
        # Don't run this in the autoreload process
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            # Schedule this to run after app initialization is complete
            django.utils.autoreload.autoreload_started.connect(self.create_profiles_for_users)
    
    def create_profiles_for_users(self, *args, **kwargs):
        # Create profiles for existing users without profiles
        from django.contrib.auth.models import User
        from app.models import UserProfile
        
        for user in User.objects.all():
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'gender': 'O'}
            ) 