# schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ParkingSearchRequest(BaseModel):
    vehicle_type: Optional[str] = None
    location: Optional[str] = None
    slot_type: Optional[str] = None # e.g., covered, open

class ParkingSpotResponse(BaseModel):
    id: int
    location: str
    spot_type: str
    vehicle_type_allowed: str
    is_available: bool
    price_per_hour: float

    class Config:
        from_attributes = True 

class BookingRequest(BaseModel):
    spot_id: int
    vehicle_type: str
    location: str 
    slot_type: str 
    start_time: datetime
    end_time: datetime

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