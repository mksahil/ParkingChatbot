# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

DATABASE_URL = "sqlite:///./parking_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ParkingSpot(Base):
    __tablename__ = "parking_spots"
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)
    spot_type = Column(String) # e.g., "covered", "open", "compact", "large"
    vehicle_type_allowed = Column(String) # e.g., "two-wheeler", "car", "suv", "truck"
    is_available = Column(Boolean, default=True)
    price_per_hour = Column(Float, default=10.0) # Example price

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    spot_id = Column(Integer, index=True) # Foreign key to ParkingSpot
    user_id = Column(String, index=True, default="default_user") # For simplicity, can be enhanced
    vehicle_type = Column(String)
    location = Column(String)
    slot_type = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    total_price = Column(Float)
    booked_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper to add dummy data ---
def add_initial_parking_spots():
    db = SessionLocal()
    if db.query(ParkingSpot).count() == 0:
        spots_data = [
            {"location": "downtown", "spot_type": "covered", "vehicle_type_allowed": "car", "price_per_hour": 15.0},
            {"location": "downtown", "spot_type": "open", "vehicle_type_allowed": "two-wheeler", "price_per_hour": 5.0},
            {"location": "airport", "spot_type": "long-term", "vehicle_type_allowed": "suv", "price_per_hour": 12.0},
            {"location": "mall", "spot_type": "compact", "vehicle_type_allowed": "car", "price_per_hour": 8.0},
            {"location": "mall", "spot_type": "open", "vehicle_type_allowed": "two-wheeler", "price_per_hour": 3.0},
        ]
        for spot_data in spots_data:
            db_spot = ParkingSpot(**spot_data)
            db.add(db_spot)
        db.commit()
        print("Added initial parking spots.")
    db.close()