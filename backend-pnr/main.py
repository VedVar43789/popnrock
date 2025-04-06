from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from pose_detector import ExerciseDetector, create_workout_with_mapper
import cv2
import asyncio
import json
import base64
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import time
import numpy as np
import joblib
import random
from starlette.websockets import WebSocketDisconnect
from FER import get_artist_name
import requests

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

# Load artist directory
try:
    with open("artists/artist_directory.json", "r") as f:
        ARTIST_DIRECTORY = json.load(f)
except Exception as e:
    print(f"Error loading artist directory: {e}")
    ARTIST_DIRECTORY = {}

# Model for schedule updates
class ScheduleUpdate(BaseModel):
    time_intervals: List[int]
    exercises: List[str]

# Model for workout generation
class WorkoutGenerator(BaseModel):
    name: str
    intensity: str

# New model for FER result
class FERResult(BaseModel):
    result: str
    confidence: float
    counts: Dict[str, int]
    intensity: str = None

# Function to determine workout intensity based on confidence
def determine_intensity(confidence: float):
    """Determine workout intensity based on match confidence"""
    if confidence < 60:
        return "LOW"
    elif confidence < 85:
        return "MEDIUM"
    else:
        return "HIGH"

SPOTIFY_CLIENT_ID = "c5fb4cf906ec46e489d376e76a945139"
SPOTIFY_CLIENT_SECRET = "8670d9d25ec24a82a939e0b73806f52d"

@app.get("/api/spotify/token")
def get_spotify_token():
    auth_url = "https://accounts.spotify.com/api/token"
    response = requests.post(
        auth_url,
        data={"grant_type": "client_credentials"},
        headers={"Authorization": f"Basic {SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"}
    )
    return response.json()

@app.websocket("/ws/livefeed")
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
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
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

# New endpoint to connect FER results to workout generation
@app.post("/connect_fer_to_workout")
async def connect_fer_to_workout(fer_result: FERResult):
    """
    Connect FER results to workout generation.
    This endpoint takes FER results and generates a workout based on the detected artist.
    """
    try:
        # Get the artist name directly from the result
        artist = fer_result.result
        
        # Check if artist exists in directory
        if artist not in ARTIST_DIRECTORY:
            print(f"Warning: Artist '{artist}' not found in directory!")
            print("Available artists:", list(ARTIST_DIRECTORY.keys()))
            
            # Choose a random artist as fallback
            artist = random.choice(list(ARTIST_DIRECTORY.keys()))
            print(f"Using fallback artist: {artist}")
        
        # Get the intensity from parameter or determine from confidence
        if fer_result.intensity:
            intensity = fer_result.intensity
        else:
            intensity = determine_intensity(fer_result.confidence)
        
        # Generate workout using existing function
        time_intervals, exercises = create_workout_with_mapper(
            artist,
            intensity
        )
        
        # Update the detector with the new workout
        detector.set_schedule(time_intervals, exercises)
        
        # Get the songs for this artist
        artist_songs = ARTIST_DIRECTORY.get(artist, ["Unknown Song"])
        selected_song = random.choice(artist_songs) if artist_songs else "Unknown Song"
        
        # Return the complete workout information
        return {
            "message": "Workout generated from artist match",
            "artist": artist,
            "song": selected_song,
            "intensity": intensity,
            "time_intervals": time_intervals,
            "exercises": exercises
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/available_artists")
async def get_available_artists():
    """Get a list of all available artists"""
    return {"available_artists": list(ARTIST_DIRECTORY.keys())}

# Add new endpoint for direct artist detection
@app.post("/get_artist_workout")
async def get_artist_workout():
    """
    Endpoint that uses the get_artist_name function to detect an artist
    and generate a workout based on that artist's music
    """
    try:
        # Call the function to get the artist name
        artist = get_artist_name()
        
        # Default confidence
        confidence = 85.0
        
        # Determine intensity based on confidence
        intensity = determine_intensity(confidence)
        
        # Generate workout using the detected artist
        time_intervals, exercises = create_workout_with_mapper(
            artist,
            intensity
        )
        
        # Update the detector with the new workout
        detector.set_schedule(time_intervals, exercises)
        
        # Get the songs for this artist
        artist_songs = ARTIST_DIRECTORY.get(artist, ["Unknown Song"])
        selected_song = random.choice(artist_songs) if artist_songs else "Unknown Song"
        
        # Return the complete workout information
        return {
            "message": "Workout generated based on detected artist",
            "artist": artist,
            "song": selected_song,
            "intensity": intensity,
            "time_intervals": time_intervals,
            "exercises": exercises
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/fer")
async def fer_websocket(websocket: WebSocket):
    await websocket.accept()
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    # Check for direct detection option
    use_direct_detection = False
    try:
        config_data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
        config = json.loads(config_data)
        if 'use_direct_detection' in config:
            use_direct_detection = config['use_direct_detection']
        scan_duration = config.get('scan_duration', 5)  # Default 5 seconds
    except (asyncio.TimeoutError, Exception) as e:
        scan_duration = 5  # Default if no config received
        if isinstance(e, Exception) and not isinstance(e, asyncio.TimeoutError):
            print(f"Error processing config: {str(e)}")
    
    # Use direct detection with get_artist_name if requested
    if use_direct_detection:
        try:
            await websocket.send_json({
                "status": "processing",
                "message": "Detecting artist directly with camera..."
            })
            
            # Import and use get_artist_name directly
            artist_name = get_artist_name()
            
            # Send the result (with default confidence)
            await websocket.send_json({
                "status": "completed",
                "result": artist_name,
                "confidence": 85.0,  # Default confidence value
                "counts": {artist_name: 1}
            })
            return
        except Exception as e:
            print(f"Error in direct detection: {str(e)}")
            try:
                await websocket.send_json({
                    "status": "completed",
                    "result": "Error in detection",
                    "confidence": 0,
                    "error": str(e)
                })
            except:
                pass
            return
    
    # If not using direct detection, continue with standard approach
    # Load FER models
    try:
        model = joblib.load('model.pickle')
        model.prepare(ctx_id=0)
        celeb_embeddings_female = joblib.load('cef.pickle')
        celeb_embeddings_male = joblib.load('cem.pickle')
        celeb_names_female = joblib.load('cnf.pickle')
        celeb_names_male = joblib.load('cnm.pickle')
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        try:
            await websocket.send_json({"error": f"Failed to load FER models: {str(e)}"})
        except:
            pass
        return
    
    # Tracking variables
    name_counts = defaultdict(int)
    start_time = time.time()
    
    try:
        # Main processing loop
        while True:
            # Check if scan duration reached
            current_time = time.time()
            elapsed_time = current_time - start_time
            time_remaining = max(0, scan_duration - elapsed_time)
            
            # Reset if scan completed
            if elapsed_time > scan_duration:
                if name_counts:
                    most_frequent_name = max(name_counts, key=name_counts.get)
                    confidence = (name_counts[most_frequent_name] / sum(name_counts.values())) * 100
                    
                    # Send final result
                    try:
                        await websocket.send_json({
                            "status": "completed",
                            "result": most_frequent_name,
                            "confidence": confidence,
                            "counts": dict(name_counts)
                        })
                    except Exception as e:
                        print(f"Error sending completion message: {str(e)}")
                        break
                else:
                    # No faces detected
                    try:
                        await websocket.send_json({
                            "status": "completed",
                            "result": "No faces detected",
                            "confidence": 0,
                            "counts": {}
                        })
                    except Exception as e:
                        print(f"Error sending completion message: {str(e)}")
                        break
                
                # Reset for next scan
                name_counts = defaultdict(int)
                start_time = current_time
            
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                try:
                    await websocket.send_json({"error": "Failed to capture frame"})
                except:
                    break
                break
            
            # Process with FER
            faces = model.get(frame)
            
            for face in faces:
                gender = "Male" if face.gender == 1 else "Female"
                (x1, y1, x2, y2) = face.bbox.astype(int)
                emb = face.embedding
                face_vector = emb.reshape(1, -1)
                
                if gender == "Male":
                    all_vectors = np.array(celeb_embeddings_male)
                    similarities = cosine_similarity(face_vector, all_vectors)[0]
                    best_idx = np.argmax(similarities)
                    name = celeb_names_male[best_idx]
                else:
                    all_vectors = np.array(celeb_embeddings_female)
                    similarities = cosine_similarity(face_vector, all_vectors)[0]
                    best_idx = np.argmax(similarities)
                    name = celeb_names_female[best_idx]
                
                name_counts[name] += 1
                
                # Draw box and name
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Looks like: {name}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Encode frame for WebSocket
            _, buffer = cv2.imencode('.jpg', frame)
            frame_encoded = base64.b64encode(buffer).decode('utf-8')
            
            # Send update
            try:
                await websocket.send_json({
                    "status": "processing",
                    "frame": frame_encoded,
                    "time_remaining": round(time_remaining),
                    "current_counts": dict(name_counts)
                })
            except Exception as e:
                print(f"Error sending update: {str(e)}")
                break
            
            # Control frame rate
            await asyncio.sleep(0.05)
            
            # Check for commands
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                command = json.loads(data)
                
                if command.get("action") == "reset":
                    name_counts = defaultdict(int)
                    start_time = current_time
                elif command.get("action") == "stop":
                    break
                elif command.get("action") == "config":
                    if 'scan_duration' in command:
                        scan_duration = command['scan_duration']
            except asyncio.TimeoutError:
                # No commands received, continue
                pass
            except WebSocketDisconnect:
                # Client disconnected
                print("WebSocket client disconnected")
                break
            except Exception as e:
                print(f"Error processing command: {str(e)}")
                # Continue the loop rather than breaking
    
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"Error in FER WebSocket: {str(e)}")
        # Don't try to send error message here - connection may be closed
    finally:
        # Release resources
        cap.release()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)