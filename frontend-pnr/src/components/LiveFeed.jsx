import { useEffect, useState } from "react";
import './LiveFeed.css';

export default function LiveFeed() {
  const [imageSrc, setImageSrc] = useState("");
  const [exerciseData, setExerciseData] = useState({
    exercise: "",
    counter: 0,
    time_remaining: 0
  });

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    
    ws.onmessage = (event) => {
      try {
        // Parse the JSON message from the server
        const data = JSON.parse(event.data);
        
        // Set the image source using the frame data
        setImageSrc(`data:image/jpeg;base64,${data.frame}`);
        
        // Update exercise data
        setExerciseData({
          exercise: data.exercise,
          counter: data.counter,
          time_remaining: data.time_remaining
        });
      } catch (error) {
        console.error("Error parsing WebSocket data:", error);
      }
    };
    
    return () => ws.close();
  }, []);

  return (
    <div className="live-feed-container">
      <h1 className="header-text">Live Pose Detection</h1>
      
      <div className="exercise-info">
        <p>Exercise: {exerciseData.exercise}</p>
        <p>Count: {exerciseData.counter}</p>
        <p>Time Remaining: {exerciseData.time_remaining}s</p>
      </div>
      
      <div className="video-container">
        {imageSrc ? (
          <img src={imageSrc} alt="Live Feed" />
        ) : (
          <p className="waiting-text">Waiting for video feed...</p>
        )}
      </div>
    </div>
  );
}