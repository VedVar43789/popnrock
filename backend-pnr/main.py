from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from pose_detector import ExerciseDetector, create_workout_with_mapper
import cv2
import asyncio
import json
import base64

app = FastAPI()

# Add CORS middleware to allow browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
detector = ExerciseDetector()

# Model for schedule updates
class ScheduleUpdate(BaseModel):
    time_intervals: List[int]
    exercises: List[str]

# Model for workout generation
class WorkoutGenerator(BaseModel):
    name: str
    intensity: str

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            
            # Process frame with current exercise detection
            processed_frame, exercise_data = detector.process_frame(frame)
            
            # Encode the frame as base64 for sending over websocket
            _, buffer = cv2.imencode('.jpg', processed_frame)
            frame_encoded = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare complete message
            message = {
                "frame": frame_encoded,
                "exercise": exercise_data['exercise'],
                "counter": exercise_data['counter'],
                "time_remaining": exercise_data['time_remaining'],
                "all_counters": exercise_data['all_counters']
            }
            
            # Send the frame and data as JSON
            await websocket.send_text(json.dumps(message))
            
            # Control the frame rate (20 FPS)
            await asyncio.sleep(0.05)
    except Exception as e:
        print(f"Error in websocket: {e}")
    finally:
        cap.release()

@app.get("/")
async def root():
    return {"message": "Exercise Detection API"}

@app.post("/set_schedule")
async def set_schedule(schedule: ScheduleUpdate):
    """Update the exercise schedule with new time intervals and exercises"""
    if len(schedule.time_intervals) != len(schedule.exercises):
        raise HTTPException(status_code=400, detail="Time intervals and exercises lists must be the same length")
    
    detector.set_schedule(schedule.time_intervals, schedule.exercises)
    return {"message": "Schedule updated successfully"}

@app.get("/current_schedule")
async def get_current_schedule():
    """Get the current exercise schedule"""
    return {
        "time_intervals": detector.time_intervals,
        "exercises": detector.exercises,
        "current_exercise": detector.get_current_exercise(),
        "time_remaining": detector.get_time_remaining()
    }

@app.get("/counters")
async def get_counters():
    """Get all exercise counters"""
    return detector.get_all_counters()

@app.post("/reset_counters")
async def reset_counters():
    """Reset all exercise counters to zero"""
    return detector.reset_counters()

@app.post("/generate_workout")
async def generate_workout(workout_params: WorkoutGenerator):
    """Generate a workout routine based on name and intensity"""
    try:
        # Valid intensity values
        valid_intensities = ["LOW", "MEDIUM", "HIGH"]
        
        # Validate intensity
        if workout_params.intensity not in valid_intensities:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid intensity. Must be one of: {', '.join(valid_intensities)}"
            )
        
        # Generate workout
        time_intervals, exercises = create_workout_with_mapper(
            workout_params.name, 
            workout_params.intensity
        )
        
        # Update the detector with new workout
        detector.set_schedule(time_intervals, exercises)
        
        return {
            "message": "Workout generated and schedule updated",
            "time_intervals": time_intervals,
            "exercises": exercises
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/available_exercises")
async def get_available_exercises():
    """Get a list of all available exercises"""
    available_exercises = [
        "arms_raise", "arm_raises",
        "jumping_jacks",
        "squats",
        "toe_touch_front",
        "lunges",
        "toe_touch_intersected", "toe_touches_sides",
        "arms_stretching", "arm_stretches",
        "standing_crunch_cross", "cross_standing_crunches",
        "standing_crunch_side", "side_standing_crunches"
    ]
    return {"available_exercises": available_exercises}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)