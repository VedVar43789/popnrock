import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './FERpage.css';

const FERPage = () => {
  const [connected, setConnected] = useState(false);
  const [imageSrc, setImageSrc] = useState("");
  const [status, setStatus] = useState("Connecting...");
  const [result, setResult] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [intensity, setIntensity] = useState("MEDIUM");
  const [counts, setCounts] = useState({});
  const [workoutGenerated, setWorkoutGenerated] = useState(false);
  const [workoutDetails, setWorkoutDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [useDirectDetection, setUseDirectDetection] = useState(false);

  const wsRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        setStatus("Connecting...");
        const ws = new WebSocket("ws://localhost:8000/ws/fer");
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          setStatus("Connected");
          
          // Send initial configuration
          try {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ 
                scan_duration: 5,
                use_direct_detection: useDirectDetection // Add this option
              }));
            }
          } catch (err) {
            console.error("Error sending config:", err);
          }
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.status === "processing") {
              // For regular processing with video frames
              if (data.frame) {
                setImageSrc(`data:image/jpeg;base64,${data.frame}`);
                setCounts(data.current_counts || {});
                setStatus(`Scanning...`);
              } 
              // For direct detection mode (which may not send frames)
              else if (data.message) {
                setStatus(data.message);
              }
            } else if (data.status === "completed") {
              setResult(data.result);
              setConfidence(parseFloat(data.confidence).toFixed(1));
              setCounts(data.counts || {});
              setStatus("Scan complete!");
              
              // When scan is complete, generate a workout
              if (data.result && data.result !== "No faces detected") {
                generateWorkout(data.result, parseFloat(data.confidence), data.counts || {});
              }
            }
          } catch (error) {
            console.error("Error parsing WebSocket data:", error);
          }
        };

        ws.onclose = (event) => {
          setConnected(false);
          setStatus(`Disconnected (${event.code})`);
        };

        ws.onerror = (error) => {
          setStatus("Connection error");
        };
      } catch (err) {
        setStatus("Failed to connect");
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [useDirectDetection]); // Add useDirectDetection as dependency

  // Function to generate workout based on FER results
  const generateWorkout = async (artistMatch, confidence, counts) => {
    try {
      setLoading(true);
      
      const response = await fetch('http://localhost:8000/connect_fer_to_workout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          result: artistMatch,
          confidence,
          counts,
          // Override with the user-selected intensity
          intensity: intensity
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Workout generated:", data);
      
      setWorkoutGenerated(true);
      setWorkoutDetails(data);
      
      // Store workout data in localStorage to access it in LiveFeed
      localStorage.setItem('workoutData', JSON.stringify({
        artist: data.artist,
        song: data.song,
        intensity: intensity,
        celebrity: artistMatch,
        confidence: confidence,
        timestamp: new Date().toISOString()
      }));
      
      setStatus(`Workout ready! Based on your match with ${artistMatch}, 
                we've created a ${intensity} intensity workout with music from ${data.artist}.`);
    } catch (error) {
      console.error("Error generating workout:", error);
      setStatus(`Error generating workout: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetScan = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "reset" }));
      setResult("");
      setConfidence(0);
      setWorkoutGenerated(false);
      setWorkoutDetails(null);
      setStatus("Scanning...");
    }
  };

  
  // Generate workout manually with selected intensity
  const generateWorkoutManually = () => {
    if (result && result !== "No faces detected") {
      generateWorkout(result, parseFloat(confidence), counts);
    } else {
      setStatus("Complete a face scan first before generating a workout");
    }
  };

  const gridBackgroundStyle = {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backgroundImage: `
      linear-gradient(rgba(136, 136, 136, 0.15) 1px, transparent 1px),
      linear-gradient(90deg, rgba(136, 136, 136, 0.15) 1px, transparent 1px)`,
    backgroundSize: "30px 30px",
    pointerEvents: "none",
    zIndex: -1, // Ensures it stays in the background
  };
  return (
    <div className="page-container">
      <h1 className="header-text">Artist Face Matcher</h1>
  
      <div className="content-container">
        {/* Left Panel - Intensity & Detection */}
        <div className="left-panel">
          <div className="intensity-card">
            <h3>Workout Intensity</h3>
            <select 
              value={intensity} 
              onChange={(e) => setIntensity(e.target.value)} 
              className="intensity-dropdown"
            >
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
  
            {/* Detection Mode Toggle */}
            <div className="detection-mode" style={{ marginTop: "15px" }}>
              <h3>Detection Mode</h3>
              <label className="mode-toggle" style={{ display: "flex", alignItems: "center", marginTop: "5px" }}>
                <input
                  type="checkbox"
                  checked={useDirectDetection}
                  onChange={() => setUseDirectDetection(!useDirectDetection)}
                  style={{ marginRight: "8px" }}
                />
                Use Direct Detection
              </label>
              <p style={{ fontSize: "0.8rem", marginTop: "5px", color: "#999" }}>
                Direct detection uses OpenCV window
              </p>
            </div>
  
            {/* Artist Match Result */}
            {result && (
              <div className="result-info" style={{ marginTop: "20px" }}>
                <h3>Artist Match</h3>
                <p><strong>{result}</strong></p>
                <p>Confidence: {confidence}%</p>
                
                {!workoutGenerated && (
                  <button 
                    onClick={generateWorkoutManually} 
                    className="generate-button"
                    style={{ marginTop: "10px" }}
                  >
                    Generate Workout
                  </button>
                )}
              </div>
            )}
  
            {/* Generated Workout Details */}
            {workoutGenerated && workoutDetails && (
              <div className="workout-info" style={{ marginTop: "20px" }}>
                <h3>Your Workout</h3>
                <p>Artist: <strong>{workoutDetails.artist}</strong></p>
                <p>Song: <strong>{workoutDetails.song}</strong></p>
                <p>Intensity: <strong>{intensity}</strong></p>
                <p>Exercises: <strong>{workoutDetails.exercises.length}</strong></p>
              </div>
            )}
          </div>
        </div>
  
        {/* Center Panel - Video Feed */}
        <div className="video-container">
          <div className="status-text">{status}</div>
          {loading && <div className="loading-text">Generating workout...</div>}
          {imageSrc ? 
            <img src={imageSrc} alt="Artist Matcher Feed" className="video-feed" /> : 
            <p className="waiting-text">Waiting for video feed...</p>
          }
        </div>
  
        {/* Right Panel - Navigation Buttons */}
        <div className="right-panel">
          <button onClick={() => navigate('/')} className="navigation-button">Back to Home</button>
          <button onClick={resetScan} disabled={!connected} className="navigation-button">Reset Scan</button>
          <button 
            onClick={() => navigate('/livefeed')} 
            className={`navigation-button go-to-exercise ${workoutGenerated ? 'ready' : ''}`}
            style={{ 
              background: workoutGenerated ? 'linear-gradient(45deg, #00ff00, #00cc00)' : undefined,
              color: workoutGenerated ? '#fff' : undefined
            }}
          >
            {workoutGenerated ? 'Start Your Workout!' : 'Go to Exercise'}
          </button>
        </div>
      </div>
    </div>
  );
  
};

export default FERPage;