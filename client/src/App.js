import React from 'react';
import './App.css';

function App() {
  // Get Flask server URL (port 5001)
  const getFlaskUrl = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    // Use the same hostname for both localhost and network devices
    return `${protocol}//${hostname}:5001`;
  };

  const flaskUrl = getFlaskUrl();
  const videoFeedUrl = `${flaskUrl}/video_feed`;

  return (
    <div className="App">
      <div className="container">
        <h1>🤚 MediaPipe Hand Detection</h1>
        
        <div className="video-container">
          <img
            src={videoFeedUrl}
            alt="MediaPipe Hand Detection Stream"
            className="video-preview"
            style={{ width: '100%', height: 'auto' }}
          />
        </div>
      </div>
    </div>
  );
}

export default App;

