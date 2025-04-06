import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import './LiveFeed.css';

export default function LiveFeed() {
  // Main states
  const [imageSrc, setImageSrc] = useState("");
  const [exerciseData, setExerciseData] = useState({
    exercise: "",
    counter: 0,
    time_remaining: 0,
    all_counters: {}
  });
  const [showPlayer, setShowPlayer] = useState(false);
  const [playingTrack, setPlayingTrack] = useState(false);
  const [workoutData, setWorkoutData] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [message, setMessage] = useState("Connecting to exercise service...");
  
  const navigate = useNavigate();

  // Load workout data from localStorage on component mount
  useEffect(() => {
    try {
      const storedWorkoutData = localStorage.getItem('workoutData');
      if (storedWorkoutData) {
        const parsedData = JSON.parse(storedWorkoutData);
        
        // Check if the workout data is recent (within the last hour)
        const timestamp = new Date(parsedData.timestamp);
        const now = new Date();
        const isRecent = (now - timestamp) < (60 * 60 * 1000); // 1 hour
        
        if (isRecent) {
          setWorkoutData(parsedData);
          setMessage(`Loaded workout based on your match with ${parsedData.celebrity}`);
        } else {
          localStorage.removeItem('workoutData');
          setMessage("No recent workout data found. Starting default workout.");
        }
      } else {
        setMessage("No workout data found. Starting default workout.");
      }
    } catch (error) {
      console.error("Error loading workout data:", error);
      setMessage("Error loading workout data. Starting default workout.");
    }
  }, []);

  // Connect to exercise WebSocket
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/livefeed");

    ws.onopen = () => {
      console.log("Exercise WebSocket connected");
      setWsConnected(true);
      setMessage("Connected to exercise service");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setImageSrc(`data:image/jpeg;base64,${data.frame}`);
        setExerciseData({
          exercise: data.exercise,
          counter: data.counter,
          time_remaining: data.time_remaining,
          all_counters: data.all_counters || {}
        });
      } catch (error) {
        console.error("Error processing exercise data:", error);
      }
    };

    ws.onclose = () => {
      console.log("Exercise WebSocket disconnected");
      setWsConnected(false);
      setMessage("Disconnected from exercise service");
    };

    ws.onerror = (error) => {
      console.error("Exercise WebSocket error:", error);
      setMessage("Error connecting to exercise service");
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  // Toggle music player
  const handleMusicToggle = () => {
    setShowPlayer(true);
    setPlayingTrack(!playingTrack);
  };

  // Map exercise name to a more user-friendly display name
  const getExerciseDisplayName = (exerciseName) => {
    const exerciseMap = {
      "arm_raises": "Arm Raises",
      "arms_raise": "Arm Raises",
      "jumping_jacks": "Jumping Jacks",
      "squats": "Squats",
      "toe_touch_front": "Toe Touches (Front)",
      "lunges": "Lunges",
      "toe_touches_sides": "Toe Touches (Sides)",
      "toe_touch_intersected": "Toe Touches (Sides)",
      "arm_stretches": "Arm Stretches",
      "arms_stretching": "Arm Stretches",
      "cross_standing_crunches": "Cross Standing Crunches",
      "standing_crunch_cross": "Cross Standing Crunches",
      "side_standing_crunches": "Side Standing Crunches",
      "standing_crunch_side": "Side Standing Crunches"
    };
    
    const exerciseVideos = {
      "arm_raises": './assets/vids/arms_raises.mp4',
      "arms_raise": './assets/vids/arms_raises.mp4',
      "jumping_jacks": './assets/vids/jumping_jacks.mp4',
      "squats": './assets/vids/squats.mp4',
      "toe_touch_front": './assets/vids/toe_touch_front.mp4',
      "lunges": './assets/vids/lunges.mp4',
      "toe_touches_sides": './assets/vids/toe_touch_side.mp4',
      "toe_touch_intersected": './assets/vids/toe_touch_cross.mp4',
      "arm_stretches": './assets/vids/arm_stretches.mp4',
      "arms_stretching": './assets/vids/arm_stretches.mp4',
      "cross_standing_crunches": './assets/vids/crunches(diagonal).mp4',
      "standing_crunch_cross": './assets/vids/crunches(diagonal).mp4',
      "side_standing_crunches": './assets/vids/crunches(side).mp4',
      "standing_crunch_side": './assets/vids/crunches(side).mp4'
    };

    return exerciseMap[exerciseName] || exerciseName;
  };

  // Function to get track ID for Spotify embedded player
  const getTrackId = () => {
    // This would ideally be a mapping of songs to their Spotify track IDs
    // For now, returning a default track ID
    return '2plbrEY59IikOBgBGLjaoe';
  };
  
  return (
    <div className="live-feed-wrapper">
      {/* Left Side - Video */}
      <div className="left-panel card">
        <h1 className="header-text">Live Pose Detection</h1>
        
        {/* Status message */}
        {!imageSrc && (
          <div className="status-message">{message}</div>
        )}
        
        <div className="video-container">
          {imageSrc ? (
            <img src={imageSrc} alt="Live Feed" />
          ) : (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p className="waiting-text">Waiting for video feed...</p>
            </div>
          )}
        </div>
      </div>

      {/* Right Side - Stats & Music */}
      <div className="right-panel">
        {/* Exercise Information */}
        <div className="card exercise-info">
          {workoutData && (
            <div className="workout-header">
              <h3 className="workout-title">Your Personalized Workout</h3>
              <p className="workout-match">
                Based on your {workoutData.confidence}% match with {workoutData.celebrity}
              </p>
            </div>
          )}

          <div className="current-exercise">
            <h3>Current Exercise</h3>
            <p className="exercise-detail">
              <span className="label">Exercise:</span> 
              <span className="value">{getExerciseDisplayName(exerciseData.exercise)}</span>
            </p>
            <p className="exercise-detail">
              <span className="label">Count:</span> 
              <span className="value">{exerciseData.counter}</span>
            </p>
            <p className="exercise-detail">
              <span className="label">Time Remaining:</span> 
              <span className="value">{exerciseData.time_remaining}s</span>
            </p>
          </div>

          {/* Exercise Stats */}
          {Object.keys(exerciseData.all_counters || {}).length > 0 && (
            <div className="exercise-stats">
              <h3>Exercise Stats</h3>
              <ul className="stats-list">
                {Object.entries(exerciseData.all_counters).map(([exercise, count]) => {
                  // Handle complex objects like lunges
                  if (typeof count !== 'number') {
                    if (exercise === 'lunges' && count.left !== undefined && count.right !== undefined) {
                      return (
                        <li key={exercise} className="stat-item">
                          <span className="exercise-name">{getExerciseDisplayName(exercise)}:</span>
                          <span className="exercise-count">{count.left + count.right}</span>
                          <span className="exercise-details">(L: {count.left}, R: {count.right})</span>
                        </li>
                      );
                    }
                    return null;
                  }
                  
                  return count > 0 ? (
                    <li key={exercise} className="stat-item">
                      <span className="exercise-name">{getExerciseDisplayName(exercise)}:</span>
                      <span className="exercise-count">{count}</span>
                    </li>
                  ) : null;
                })}
              </ul>
            </div>
          )}
        </div>

        {/* Music Player */}
        <div className="card spotify-container">
          {workoutData ? (
            <>
              <h3 className="music-title">Your Workout Music</h3>
              <div className="music-details">
                <p className="music-info">
                  <span className="music-label">Artist:</span> 
                  <span className="music-value">{workoutData.artist}</span>
                </p>
                <p className="music-info">
                  <span className="music-label">Song:</span> 
                  <span className="music-value">{workoutData.song}</span>
                </p>
                <p className="music-info">
                  <span className="music-label">Intensity:</span> 
                  <span className="music-value">{workoutData.intensity}</span>
                </p>
              </div>
              
              <button onClick={handleMusicToggle} className="spotify-play-button">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d={playingTrack ? "M6 4h4v16H6V4zm8 0h4v16h-4V4z" : "M8 5V19L19 12L8 5Z"} fill="currentColor"/>
                </svg>
                {playingTrack ? 'Pause Music' : 'Play Workout Music'}
              </button>
              
              {showPlayer && (
                <div className="spotify-player-wrapper">
                  <iframe
                    title="Spotify Player"
                    src={`https://open.spotify.com/embed/track/${getTrackId()}?utm_source=generator${playingTrack ? '&autoplay=1' : ''}`}
                    width="100%"
                    height="80"
                    frameBorder="0"
                    allowFullScreen
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                    loading="lazy"
                  ></iframe>
                </div>
              )}
            </>
          ) : (
            <div className="no-workout-data">
              <p>No personalized workout data available.</p>
              <button 
                onClick={() => navigate('/fer')}
                className="get-workout-button"
              >
                Get Personalized Workout
              </button>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="nav-buttons card">
          <button 
            onClick={() => navigate('/')}
            className="home-button"
          >
            Back to Home
          </button>
          
          <button 
            onClick={() => navigate('/fer')}
            className="fer-button"
          >
            New Celebrity Match
          </button>
        </div>
      </div>
    </div>
  );
}