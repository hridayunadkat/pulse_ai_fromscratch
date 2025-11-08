import React from 'react';
import './App.css';

function App() {
  // Get Flask server URL (port 5001)
  const getFlaskUrl = () => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:5001';
    }
    // If accessing from phone, use the same hostname
    return `http://${hostname}:5001`;
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

