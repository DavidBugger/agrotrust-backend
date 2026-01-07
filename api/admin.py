from django.contrib import admin
from .models import Profile, FarmerProfile, FarmActivity, TrustConfig

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('phone', 'role', 'is_profile_complete', 'created_at')
    list_filter = ('role', 'is_profile_complete')
    search_fields = ('phone', 'supabase_user_id')

@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'location', 'main_crop', 'trust_level', 'internal_score')
    list_filter = ('trust_level', 'main_crop')
    search_fields = ('full_name', 'location', 'profile__phone')

@admin.register(FarmActivity)
class FarmActivityAdmin(admin.ModelAdmin):
    list_display = ('farmer_profile', 'activity_type', 'activity_date', 'sync_status')
    list_filter = ('activity_type', 'sync_status')
    search_fields = ('farmer_profile__full_name', 'activity_type')

@admin.register(TrustConfig)
class TrustConfigAdmin(admin.ModelAdmin):
    list_display = ('profile_weight', 'activity_frequency_weight', 'consistency_weight')
