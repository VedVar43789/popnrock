import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./LiveFeed.css";

export default function LiveFeed() {
  const [imageSrc, setImageSrc] = useState("");
  const [exerciseData, setExerciseData] = useState({
    exercise: "",
    counter: 0,
    time_remaining: 0,
    all_counters: {},
  });
  const [showPlayer, setShowPlayer] = useState(false);
  const [playingTrack, setPlayingTrack] = useState(false);
  const [workoutData, setWorkoutData] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [spotifyTrackId, setSpotifyTrackId] = useState("");
  const [message, setMessage] = useState("Connecting to exercise service...");

  const navigate = useNavigate();

  // Load workout data on mount
  useEffect(() => {
    try {
      const storedWorkoutData = localStorage.getItem("workoutData");
      if (storedWorkoutData) {
        const parsedData = JSON.parse(storedWorkoutData);
        const timestamp = new Date(parsedData.timestamp);
        const now = new Date();
        if (now - timestamp < 60 * 60 * 1000) {
          setWorkoutData(parsedData);
          setMessage(`Loaded workout based on your match with ${parsedData.celebrity}`);
        } else {
          localStorage.removeItem("workoutData");
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

  // Fetch Spotify Track ID when workoutData is available
  useEffect(() => {
    if (workoutData?.song) {
      fetchTrackId(workoutData.song);
    }
  }, [workoutData]);

  const fetchTrackId = async (songName) => {
    try {
      const response = await fetch("/json/spotify_song.json");
      const songData = await response.json();
      const trackId = songData[songName.trim()];
      if (trackId) {
        setSpotifyTrackId(trackId);
      } else {
        console.warn(`Track ID not found for song: ${songName}`);
      }
    } catch (error) {
      console.error("Error fetching track ID:", error);
    }
  };

  // Establish WebSocket connection
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/livefeed");

    ws.onopen = () => {
      console.log("WebSocket connected");
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
          all_counters: data.all_counters || {},
        });
      } catch (error) {
        console.error("Error processing exercise data:", error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setWsConnected(false);
      setMessage("Disconnected from exercise service");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setMessage("Error connecting to exercise service");
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  // Toggle Spotify player
  const handleMusicToggle = () => {
    setShowPlayer(true);
    setPlayingTrack(!playingTrack);
  };

  return (
    <div className="live-feed-wrapper">
      {/* Left Side - Video */}
      <div className="left-panel card">
        <h1 className="header-text">Live Pose Detection</h1>
        {!imageSrc && <div className="status-message">{message}</div>}
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
            <p>
              <span className="label">Exercise:</span>{" "}
              <span className="value">{exerciseData.exercise || "None"}</span>
            </p>
            <p>
              <span className="label">Count:</span>{" "}
              <span className="value">{exerciseData.counter}</span>
            </p>
            <p>
              <span className="label">Time Remaining:</span>{" "}
              <span className="value">{exerciseData.time_remaining}s</span>
            </p>
          </div>
        </div>

        {/* Music Player */}
        <div className="card spotify-container">
          {workoutData ? (
            <>
              <h3 className="music-title">Your Workout Music</h3>
              <p>
                <span className="music-label">Song:</span>{" "}
                <span className="music-value">{workoutData.song}</span>
              </p>
              <button onClick={handleMusicToggle} className="spotify-play-button">
                {playingTrack ? "Pause Music" : "Play Workout Music"}
              </button>
              {showPlayer && spotifyTrackId && (
                <div className="spotify-player-wrapper">
                  <iframe
                    title="Spotify Player"
                    src={`https://open.spotify.com/embed/track/${spotifyTrackId}?utm_source=generator${playingTrack ? "&autoplay=1" : ""}`}
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
              <button onClick={() => navigate("/fer")} className="get-workout-button">
                Get Personalized Workout
              </button>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="nav-buttons card">
          <button onClick={() => navigate("/")} className="home-button">
            Back to Home
          </button>
          <button onClick={() => navigate("/fer")} className="fer-button">
            New Celebrity Match
          </button>
        </div>
      </div>
    </div>
  );
}
