import os
import sys
from pathlib import Path
import django
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import jwt
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

# Add the project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from api.models import Profile, FarmerProfile, Role

app = FastAPI(
    title="Agrotrust API",
    docs_url=None, 
    redoc_url=None, 
    openapi_url=None
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Agrotrust API - Swagger UI"
    )

@app.get("/docs/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Agrotrust API - ReDoc"
    )

@app.get("/redoc/", include_in_schema=False)
async def redirect_to_redoc():
    return RedirectResponse(url="/redoc")

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="Agrotrust API", version="1.0.0", routes=app.routes))

# JWT Helper (simplified for V1)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-secret-key")

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth header")
    try:
        token = authorization.split(" ")[1]
        # In a real app, verify with Supabase secret
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

class SyncUserRequest(BaseModel):
    supabase_user_id: str
    phone: str

@app.post("/auth/sync-user")
def sync_user(data: SyncUserRequest):
    profile, created = Profile.objects.get_or_create(
        supabase_user_id=data.supabase_user_id,
        defaults={'phone': data.phone, 'role': Role.FARMER}
    )
    
    if created:
        FarmerProfile.objects.create(profile=profile)
        
    return {
        "user_id": profile.id,
        "role": profile.role,
        "is_profile_complete": profile.is_profile_complete
    }

# Farmer Profile APIs
class FarmerProfileCreate(BaseModel):
    full_name: str
    location: str
    main_crop: str
    farm_size: str

@app.post("/farmers/profile")
def create_farmer_profile(data: FarmerProfileCreate, token: dict = Depends(verify_token)):
    # In real app, get user from token
    try:
        profile = Profile.objects.get(supabase_user_id=token["sub"])
        farmer_profile = profile.farmer_profile
        farmer_profile.full_name = data.full_name
        farmer_profile.location = data.location
        farmer_profile.main_crop = data.main_crop
        farmer_profile.farm_size = data.farm_size
        farmer_profile.save()
        
        profile.is_profile_complete = True
        profile.save()
        
        return {"status": "created", "farmer_id": profile.id}
    except Profile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Profile not found")

@app.get("/farmers/profile")
def get_farmer_profile(token: dict = Depends(verify_token)):
    try:
        profile = Profile.objects.get(supabase_user_id=token["sub"])
        farmer = profile.farmer_profile
        return {
            "full_name": farmer.full_name,
            "location": farmer.location,
            "main_crop": farmer.main_crop,
            "farm_size": farmer.farm_size,
            "created_at": profile.created_at
        }
    except Profile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Profile not found")

# Farmer Home / Status
@app.get("/farmers/home")
def get_farmer_home(token: dict = Depends(verify_token)):
    try:
        profile = Profile.objects.get(supabase_user_id=token["sub"])
        farmer = profile.farmer_profile
        
        greeting_name = farmer.full_name.split(" ")[0] if farmer.full_name else "Farmer"
        
        return {
            "greeting_name": greeting_name,
            "farm_status": "record_growing" if farmer.activities.exists() else "new_farmer",
            "trust_level": farmer.trust_level,
            "pending_actions": ["Log farm activity"] if not farmer.activities.exists() else []
        }
    except Profile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Profile not found")

# Farm Activity APIs
class FarmActivityCreate(BaseModel):
    activity_type: str
    activity_date: str
    notes: Optional[str] = None
    photo_url: Optional[str] = None

@app.post("/farm-activities")
def log_farm_activity(data: FarmActivityCreate, token: dict = Depends(verify_token)):
    try:
        profile = Profile.objects.get(supabase_user_id=token["sub"])
        farmer = profile.farmer_profile
        from datetime import datetime
        
        activity = FarmActivity.objects.create(
            farmer_profile=farmer,
            activity_type=data.activity_type,
            activity_date=datetime.strptime(data.activity_date, "%Y-%m-%d").date(),
            notes=data.notes,
            photo_url=data.photo_url
        )
        
        return {
            "status": "saved",
            "activity_id": str(activity.id),
            "sync_status": activity.sync_status
        }
    except Profile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Profile not found")

@app.get("/farm-activities")
def list_farm_activities(token: dict = Depends(verify_token)):
    try:
        profile = Profile.objects.get(supabase_user_id=token["sub"])
        farmer = profile.farmer_profile
        activities = farmer.activities.all().order_by('-activity_date')
        
        return [
            {
                "activity_type": a.activity_type,
                "activity_date": a.activity_date,
                "created_at": a.created_at
            } for a in activities
        ]
    except Profile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Profile not found")

# Farm Trust Level API
@app.get("/farmers/trust-level")
def get_trust_level(token: dict = Depends(verify_token)):
    try:
        profile = Profile.objects.get(supabase_user_id=token["sub"])
        farmer = profile.farmer_profile
        
        explanation = [
            "You are logging farm activities",
            "More consistency will improve your trust"
        ] if farmer.activities.exists() else ["Please start logging your farm activities to build trust."]
        
        return {
            "trust_level": farmer.trust_level,
            "status_color": "yellow" if farmer.trust_level == "Fair" else "green" if farmer.trust_level == "Good" else "red",
            "explanation": explanation,
            "tips": [
                "Record activities weekly",
                "Add photos when possible"
            ]
        }
    except Profile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Profile not found")

# Loan Status API
@app.get("/loans/status")
async def get_loan_status():
    return {
        "loan_status": "Not Available",
        "message": "Loans will be available through partner organizations"
    }

# Partner APIs
@app.get("/partners/farmers")
def list_partners_farmers(
    trust_level: Optional[str] = None,
    location: Optional[str] = None,
    crop: Optional[str] = None
):
    farmers = FarmerProfile.objects.all()
    if trust_level:
        farmers = farmers.filter(trust_level=trust_level)
    if location:
        farmers = farmers.filter(location__icontains=location)
    if crop:
        farmers = farmers.filter(main_crop__icontains=crop)
        
    return [
        {
            "farmer_id": f.profile.id,
            "name": f.full_name,
            "location": f.location,
            "main_crop": f.main_crop,
            "trust_level": f.trust_level
        } for f in farmers
    ]

@app.get("/partners/farmers/{farmer_id}")
def get_partner_farmer_detail(farmer_id: str):
    try:
        farmer = FarmerProfile.objects.get(profile__id=farmer_id)
        activities = farmer.activities.all().order_by('-activity_date')
        
        return {
            "profile": {
                "name": farmer.full_name,
                "location": farmer.location,
                "main_crop": farmer.main_crop
            },
            "trust_level": farmer.trust_level,
            "activities": [
                {
                    "type": a.activity_type,
                    "date": a.activity_date
                } for a in activities
            ]
        }
    except FarmerProfile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Farmer not found")

@app.get("/partners/export/farmers")
def export_farmers_csv():
    import csv
    from fastapi.responses import StreamingResponse
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Location', 'Main Crop', 'Trust Level', 'Internal Score'])
    
    for f in FarmerProfile.objects.all():
        writer.writerow([f.profile.id, f.full_name, f.location, f.main_crop, f.trust_level, f.internal_score])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=farmers.csv"}
    )

# Internal Trust Scoring
class TrustCalculateRequest(BaseModel):
    farmer_id: str

@app.post("/internal/calculate-trust")
def calculate_trust(data: TrustCalculateRequest):
    try:
        farmer = FarmerProfile.objects.get(profile__id=data.farmer_id)
        config = TrustConfig.objects.first()
        if not config:
            config = TrustConfig.objects.create()
            
        # Mock logic for V1
        activity_count = farmer.activities.count()
        score = min(activity_count * 10, 100) # Simple linear growth
        
        farmer.internal_score = score
        if score > 70:
            farmer.trust_level = "Good"
        elif score > 30:
            farmer.trust_level = "Fair"
        else:
            farmer.trust_level = "New"
        farmer.save()
        
        return {
            "trust_level": farmer.trust_level,
            "internal_score": farmer.internal_score
        }
    except FarmerProfile.DoesNotExist:
        raise HTTPException(status_code=404, detail="Farmer not found")

# Admin APIs
@app.get("/admin/dashboard")
def get_admin_dashboard():
    total_farmers = FarmerProfile.objects.count()
    total_activities = FarmActivity.objects.count()
    
    trust_dist = {
        "Good": FarmerProfile.objects.filter(trust_level="Good").count(),
        "Fair": FarmerProfile.objects.filter(trust_level="Fair").count(),
        "New": FarmerProfile.objects.filter(trust_level="New").count(),
    }
    
    return {
        "total_farmers": total_farmers,
        "total_activities": total_activities,
        "trust_distribution": trust_dist
    }

@app.get("/")
def home():
    return {
        "message": "Agrotrust API is running",
        "api_docs": "/docs",
        "admin_interface": "/admin"
    }

# Mount Django as a fallback
app.mount("/", django_asgi_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
