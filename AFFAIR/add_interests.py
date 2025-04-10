import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dating_site.settings')
django.setup()

from app.models import Interest

# List of interests to create
interests = [
    "Travel", "Fitness", "Cooking", "Reading", "Movies", "Music",
    "Photography", "Art", "Dance", "Sports", "Hiking", "Gaming",
    "Technology", "Fashion", "Wine", "Coffee", "Pets", "Yoga",
    "Meditation", "Volunteering", "Languages", "Politics", "Science",
    "History", "Writing", "Swimming", "Cycling", "Running", "Theater",
    "Comedy", "Philosophy", "DIY", "Gardening", "Nature"
]

# Create interests
for interest_name in interests:
    Interest.objects.get_or_create(name=interest_name)
    print(f"Created interest: {interest_name}")

print(f"\nTotal interests created: {Interest.objects.count()}") 