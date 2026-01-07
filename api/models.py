import uuid
from django.db import models
from django.contrib.auth.models import User

class Role(models.TextChoices):
    FARMER = 'farmer', 'Farmer'
    PARTNER = 'partner', 'Partner'
    ADMIN = 'admin', 'Admin'

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supabase_user_id = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.FARMER)
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} ({self.role})"

class FarmerProfile(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='farmer_profile')
    full_name = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    main_crop = models.CharField(max_length=100, null=True, blank=True)
    farm_size = models.CharField(max_length=100, null=True, blank=True)
    trust_level = models.CharField(max_length=50, default="New")
    internal_score = models.IntegerField(default=0)

    def __str__(self):
        return self.full_name or self.profile.phone

class FarmActivity(models.Model):
    farmer_profile = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=100)
    activity_date = models.DateField()
    notes = models.TextField(null=True, blank=True)
    photo_url = models.URLField(max_length=500, null=True, blank=True)
    sync_status = models.CharField(max_length=20, default="synced")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Farm Activities"

class TrustConfig(models.Model):
    profile_weight = models.IntegerField(default=20)
    activity_frequency_weight = models.IntegerField(default=50)
    consistency_weight = models.IntegerField(default=30)

    def __str__(self):
        return "Trust Logic Configuration"
