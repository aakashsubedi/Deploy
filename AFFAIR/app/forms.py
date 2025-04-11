from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Interest

class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500',
                'placeholder': field.label
            })

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500',
                'placeholder': field.label
            })

class UserProfileForm(forms.ModelForm):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500',
        'placeholder': 'Enter your first name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500',
        'placeholder': 'Enter your last name'
    }))
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500'
        }),
        required=False
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500'
        })
    )
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    custom_interests = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500',
            'placeholder': 'Add your own interests (comma-separated)'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'bio', 'birth_date', 'gender', 'location', 'occupation', 'profile_picture', 'interests', 'custom_interests')
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            # Get initial values for first_name and last_name from related User
            initial = kwargs.get('initial', {})
            initial['first_name'] = instance.user.first_name
            initial['last_name'] = instance.user.last_name
            kwargs['initial'] = initial
        
        super().__init__(*args, **kwargs)
        
        # Add classes to all fields except interests
        for field_name, field in self.fields.items():
            if field_name not in ['interests', 'custom_interests']:
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500',
                })
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        # Save first_name and last_name to User model
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        
        # Handle custom interests
        custom_interests = self.cleaned_data.get('custom_interests', '')
        if custom_interests:
            interest_names = [name.strip() for name in custom_interests.split(',')]
            for name in interest_names:
                if name:
                    interest, created = Interest.objects.get_or_create(name=name)
                    profile.interests.add(interest)
        
        if commit:
            profile.user.save()
            profile.save()
            
        return profile

class UserPictureForm(forms.Form):
    image = forms.ImageField(
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        required=False
    ) 