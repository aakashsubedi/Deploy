from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

class Interest(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    location = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    interests = models.ManyToManyField(Interest, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_active = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def age(self):
        from datetime import date
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
    
    def get_additional_pictures(self):
        return self.pictures.all()

class UserPicture(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='pictures')
    image = models.ImageField(upload_to='user_pics/')
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Picture {self.order} of {self.user_profile.user.username}"

class Match(models.Model):
    STATUS_CHOICES = (
        ('P', 'Pending'),
        ('A', 'Accepted'),
        ('R', 'Rejected'),
    )
    
    user_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_initiated')
    user_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_received')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user_from', 'user_to')
    
    def __str__(self):
        return f"{self.user_from.username} -> {self.user_to.username} ({self.get_status_display()})"
    
    @classmethod
    def create_match(cls, user_from, user_to):
        # Check if reverse match exists
        reverse_match = cls.objects.filter(user_from=user_to, user_to=user_from).first()
        
        if reverse_match:
            # If reverse match exists and is pending, auto-accept both
            if reverse_match.status == 'P':
                reverse_match.status = 'A'
                reverse_match.save()
                return cls.objects.create(user_from=user_from, user_to=user_to, status='A')
        
        # Otherwise create a pending match
        return cls.objects.create(user_from=user_from, user_to=user_to)

class ConversationManager(models.Manager):
    def get_or_create_conversation(self, user1, user2):
        # Check if conversation exists in either direction
        q1 = Q(user1=user1, user2=user2)
        q2 = Q(user1=user2, user2=user1)
        
        conversation = self.filter(q1 | q2).first()
        
        if conversation:
            return conversation, False
        
        # Create new conversation
        return self.create(user1=user1, user2=user2), True
    
    def get_conversations_for_user(self, user):
        # Get all conversations where user is either user1 or user2
        return self.filter(Q(user1=user) | Q(user2=user))

class Conversation(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = ConversationManager()
    
    class Meta:
        unique_together = ('user1', 'user2')
    
    def __str__(self):
        return f"Conversation between {self.user1.username} and {self.user2.username}"
    
    def get_other_user(self, user):
        if user == self.user1:
            return self.user2
        return self.user1
    
    def last_message(self):
        return self.messages.order_by('-created_at').first()

class Message(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('voice', 'Voice'),
    )
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    voice = models.FileField(upload_to='chat_voice/', null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()
    
    @classmethod
    def get_unread_count(cls, user):
        # Get count of unread messages where the user is the recipient
        return cls.objects.filter(
            conversation__in=Conversation.objects.get_conversations_for_user(user),
            sender__in=User.objects.exclude(id=user.id),
            is_read=False
        ).count()

# Add signal handlers to create UserProfile automatically when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile automatically when a User is created
    """
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'gender': 'O'}  # Set default gender, will be updated in the profile setup
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save UserProfile when User is saved
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance, gender='O') 