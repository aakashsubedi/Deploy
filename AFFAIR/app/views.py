from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F, Count, Case, When, BooleanField
from django.http import JsonResponse
from django.urls import reverse
from .forms import CustomRegistrationForm, CustomLoginForm, UserProfileForm, UserPictureForm
from .models import UserProfile, User, Match, Conversation, Message, Interest, UserPicture
from django.core.paginator import Paginator
import json
from geopy.distance import geodesic
from django.utils import timezone
from django.views.decorators.http import require_http_methods

def index(request):
    if request.user.is_authenticated:
        return redirect('explore')
    return render(request, 'app/index.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('explore')
    
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                gender='O'  # Set default gender, will be updated in the profile setup
            )
            
            messages.success(request, 'Account created successfully! Please complete your profile.')
            return redirect('profile_setup')
    else:
        form = CustomRegistrationForm()
    
    return render(request, 'app/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('explore')
        
    if request.method == 'POST':
        form = CustomLoginForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('explore')
    else:
        form = CustomLoginForm()
    
    return render(request, 'app/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def profile_setup(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user, gender='O')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        picture_form = UserPictureForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            
            if picture_form.is_valid() and request.FILES.getlist('image'):
                for index, image in enumerate(request.FILES.getlist('image')):
                    UserPicture.objects.create(
                        user_profile=profile,
                        image=image,
                        order=index + 1
                    )
            
            messages.success(request, 'Profile set up successfully!')
            return redirect('explore')
    else:
        form = UserProfileForm(instance=profile)
        picture_form = UserPictureForm()
    
    interests = Interest.objects.all()
    
    return render(request, 'app/profile_setup.html', {
        'form': form, 
        'picture_form': picture_form,
        'interests': interests
    })

@login_required
def explore(request):
    user = request.user
    
    # Import at the beginning of the function
    from app.models import UserProfile
    
    # Ensure user has a profile
    try:
        user_profile = user.profile
    except:
        # Create profile if it doesn't exist
        user_profile = UserProfile.objects.create(
            user=user,
            gender='O'  # Set default gender
        )
    
    # Get users who the current user hasn't interacted with yet
    interacted_users = Match.objects.filter(
        Q(user_from=user) | Q(user_to=user, status='A')
    ).values_list('user_to', 'user_from')
    
    flat_interacted_users = []
    for user_to, user_from in interacted_users:
        flat_interacted_users.append(user_to)
        flat_interacted_users.append(user_from)
    
    # Filter out the current user and interacted users
    potential_matches = UserProfile.objects.exclude(
        Q(user__in=flat_interacted_users) | Q(user=user)
    )
    
    # If we have location data, sort by distance
    if user_profile.latitude and user_profile.longitude:
        # We can't sort by distance directly, so we'll fetch all and sort in Python
        user_coords = (user_profile.latitude, user_profile.longitude)
        
        # Add distance to each profile
        for profile in potential_matches:
            if profile.latitude and profile.longitude:
                profile_coords = (profile.latitude, profile.longitude)
                profile.distance = round(geodesic(user_coords, profile_coords).kilometers, 1)
            else:
                profile.distance = None
        
        # Sort by distance
        potential_matches = sorted(potential_matches, key=lambda x: (x.distance is None, x.distance))
    
    # Paginate results
    paginator = Paginator(potential_matches, 1)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'app/explore.html', {'page_obj': page_obj})

@login_required
def like_user(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    user_to = get_object_or_404(User, id=user_id)
    match = Match.create_match(request.user, user_to)
    
    # Check if this is a mutual match
    is_match = match.status == 'A'
    
    return JsonResponse({
        'status': 'success',
        'is_match': is_match
    })

@login_required
def pass_user(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    user_to = get_object_or_404(User, id=user_id)
    Match.objects.create(user_from=request.user, user_to=user_to, status='R')
    
    return JsonResponse({'status': 'success'})

@login_required
def matches(request):
    user = request.user
    
    # Get all accepted matches
    user_matches = Match.objects.filter(
        (Q(user_from=user) | Q(user_to=user)) & Q(status='A')
    )
    
    matched_users = []
    for match in user_matches:
        if match.user_from == user:
            matched_users.append(match.user_to)
        else:
            matched_users.append(match.user_from)
    
    # Get profiles of matched users
    matched_profiles = UserProfile.objects.filter(user__in=matched_users)
    
    return render(request, 'app/matches.html', {'matched_profiles': matched_profiles})

@login_required
def get_profile_details(request, profile_id):
    try:
        profile = get_object_or_404(UserProfile, id=profile_id)
        
        # Check if the profile belongs to a matched user
        if not Match.objects.filter(
            Q(user_from=request.user, user_to=profile.user) | 
            Q(user_from=profile.user, user_to=request.user)
        ).exists():
            return JsonResponse({'error': 'Profile not accessible'}, status=403)
        
        data = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'age': profile.age(),
            'bio': profile.bio,
            'occupation': profile.occupation,
            'location': profile.location,
            'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
            'interests': [interest.name for interest in profile.interests.all()]
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def start_conversation(request, user_id):
    """
    Create or get conversation with another user and redirect to the chat page
    """
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if users are matched
    is_matched = Match.objects.filter(
        (Q(user_from=request.user, user_to=other_user) | Q(user_from=other_user, user_to=request.user)) &
        Q(status='A')
    ).exists()
    
    if not is_matched:
        messages.error(request, "You can only message users you've matched with.")
        return redirect('matches')
    
    # Get or create conversation between users
    conversation, created = Conversation.objects.get_or_create_conversation(request.user, other_user)
    
    # Redirect to chat page
    return redirect('chat', conversation_id=conversation.id)

@login_required
def conversations(request):
    user = request.user
    
    # Get all conversations
    user_conversations = Conversation.objects.get_conversations_for_user(user)
    
    # Add additional info to each conversation
    for conversation in user_conversations:
        other_user = conversation.get_other_user(user)
        conversation.other_user = other_user
        conversation.other_profile = other_user.profile
        conversation.last_msg = conversation.last_message()
        conversation.unread_count = Message.objects.filter(
            conversation=conversation,
            sender=other_user,
            is_read=False
        ).count()
    
    # Sort by latest message
    user_conversations = sorted(
        user_conversations,
        key=lambda x: x.last_msg.created_at if x.last_msg else x.created_at,
        reverse=True
    )
    
    return render(request, 'app/conversations.html', {'conversations': user_conversations})

@login_required
def chat(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.get_conversations_for_user(request.user),
        id=conversation_id
    )
    
    other_user = conversation.get_other_user(request.user)
    other_profile = other_user.profile
    
    # Mark all messages from the other user as read
    Message.objects.filter(
        conversation=conversation,
        sender=other_user,
        is_read=False
    ).update(is_read=True)
    
    # Get all messages for this conversation
    messages_list = conversation.messages.all()
    
    return render(request, 'app/chat.html', {
        'conversation': conversation,
        'other_user': other_user,
        'other_profile': other_profile,
        'messages': messages_list
    })

@login_required
def send_message(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    conversation = get_object_or_404(
        Conversation.objects.get_conversations_for_user(request.user),
        id=conversation_id
    )
    
    content = request.POST.get('content', '').strip()
    message_type = request.POST.get('message_type', 'text')
    
    message = Message(
        conversation=conversation,
        sender=request.user,
        message_type=message_type
    )
    
    if message_type == 'text':
        if not content:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        message.content = content
    elif message_type == 'image':
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'Image file is required'}, status=400)
        message.image = request.FILES['image']
        message.content = content  # Optional caption
    elif message_type == 'voice':
        if 'voice' not in request.FILES:
            return JsonResponse({'error': 'Voice file is required'}, status=400)
        message.voice = request.FILES['voice']
        message.content = content  # Optional caption
    else:
        return JsonResponse({'error': 'Invalid message type'}, status=400)
    
    message.save()
    
    response_data = {
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_mine': True,
            'message_type': message.message_type,
        }
    }
    
    # Add URLs for media files
    if message_type == 'image' and message.image:
        response_data['message']['image_url'] = message.image.url
    elif message_type == 'voice' and message.voice:
        response_data['message']['voice_url'] = message.voice.url
    
    return JsonResponse(response_data)

@login_required
def profile(request):
    user_profile = request.user.profile
    additional_pictures = user_profile.get_additional_pictures()
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        picture_form = UserPictureForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            
            if picture_form.is_valid() and request.FILES.getlist('image'):
                # Get the highest order number
                next_order = 1
                if additional_pictures.exists():
                    next_order = additional_pictures.order_by('-order').first().order + 1
                
                for index, image in enumerate(request.FILES.getlist('image')):
                    UserPicture.objects.create(
                        user_profile=user_profile,
                        image=image,
                        order=next_order + index
                    )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
        picture_form = UserPictureForm()
    
    return render(request, 'app/profile.html', {
        'profile': user_profile,
        'form': form,
        'picture_form': picture_form,
        'additional_pictures': additional_pictures
    })

@login_required
def delete_picture(request, picture_id):
    picture = get_object_or_404(UserPicture, id=picture_id, user_profile=request.user.profile)
    picture.delete()
    
    messages.success(request, 'Picture deleted successfully!')
    return redirect('profile')

@login_required
def edit_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user, gender='O')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        picture_form = UserPictureForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            
            if picture_form.is_valid() and request.FILES.getlist('image'):
                for index, image in enumerate(request.FILES.getlist('image')):
                    UserPicture.objects.create(
                        user_profile=profile,
                        image=image,
                        order=index + 1
                    )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
        picture_form = UserPictureForm()
    
    interests = Interest.objects.all()
    
    return render(request, 'app/profile.html', {
        'form': form, 
        'picture_form': picture_form,
        'interests': interests,
        'profile': profile
    }) 