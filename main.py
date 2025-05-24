# main_api.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, timedelta

import database, schemas

app = FastAPI(title="Parking API")
database.add_initial_parking_spots()

@app.post("/get-parking-spots", response_model=List[schemas.ParkingSpotResponse])
def get_parking_spots(request: schemas.ParkingSearchRequest, db: Session = Depends(database.get_db)):
    query = db.query(database.ParkingSpot).filter(database.ParkingSpot.is_available == True)

    if request.vehicle_type:
        query = query.filter(database.ParkingSpot.vehicle_type_allowed.ilike(f"%{request.vehicle_type}%"))
    if request.location:
        query = query.filter(database.ParkingSpot.location.ilike(f"%{request.location}%"))
    if request.slot_type:
        query = query.filter(database.ParkingSpot.spot_type.ilike(f"%{request.slot_type}%"))


    available_spots = query.all()
    if not available_spots:
        return []
    return available_spots

@app.post("/book-parking", response_model=schemas.BookingResponse)
def book_parking(request: schemas.BookingRequest, db: Session = Depends(database.get_db)):
    spot = db.query(database.ParkingSpot).filter(database.ParkingSpot.id == request.spot_id).first()

    if not spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    if not spot.is_available:
        raise HTTPException(status_code=400, detail="Parking spot is not available")
    duration_hours = (request.end_time - request.start_time).total_seconds() / 3600
    if duration_hours <= 0:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    total_price = duration_hours * spot.price_per_hour

    # Create booking
    new_booking = database.Booking(
        spot_id=request.spot_id,
        user_id="default_user",
        vehicle_type=request.vehicle_type,
        location=spot.location,
        slot_type=spot.spot_type,
        start_time=request.start_time,
        end_time=request.end_time,
        total_price=total_price
    )
    print(f"Booking details: {new_booking}")
    db.add(new_booking)
    spot.is_available = False 
    db.commit()
    db.refresh(new_booking)
    db.refresh(spot)

    return schemas.BookingResponse(
        booking_id=new_booking.id,
        spot_id=new_booking.spot_id,
        message="Parking spot booked successfully!",
        vehicle_type=new_booking.vehicle_type,
        location=new_booking.location,
        slot_type=new_booking.slot_type,
        start_time=new_booking.start_time,
        end_time=new_booking.end_time,
        total_price=new_booking.total_price
    )

@app.post("/admin/reset-availability")
def reset_availability(db: Session = Depends(database.get_db)):
    db.query(database.ParkingSpot).update({"is_available": True})
    db.query(database.Booking).delete()
    db.commit()
    return {"message": "All parking spot availability reset and bookings cleared."}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)