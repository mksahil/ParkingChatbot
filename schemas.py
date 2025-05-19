# schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ParkingSearchRequest(BaseModel):
    vehicle_type: Optional[str] = None
    location: Optional[str] = None
    slot_type: Optional[str] = None # e.g., covered, open
    # parking_duration: Optional[str] = None # We'll use start_time and end_time for booking
    # For search, we might just check availability broadly

class ParkingSpotResponse(BaseModel):
    id: int
    location: str
    spot_type: str
    vehicle_type_allowed: str
    is_available: bool
    price_per_hour: float

    class Config:
        from_attributes = True # Pydantic V2, or orm_mode = True for V1

class BookingRequest(BaseModel):
    spot_id: int
    vehicle_type: str
    location: str # From the spot
    slot_type: str # From the spot
    start_time: datetime
    end_time: datetime
    # user_id: Optional[str] = "default_user" # Can be passed or set default

class BookingResponse(BaseModel):
    booking_id: int
    spot_id: int
    message: str
    vehicle_type: str
    location: str
    slot_type: str
    start_time: datetime
    end_time: datetime
    total_price: float

    class Config:
        from_attributes = True