#!/usr/bin/env python3
"""
Simple Flask server to stream MediaPipe hand detection
"""
from flask import Flask, Response, render_template_string
from flask_cors import CORS
from cpr_assistant import CPRAssistant
import cv2
import atexit
import ssl
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
cpr_assistant = CPRAssistant()
camera_initialized = False

# HTML template for the web page (mobile-friendly, uses device's own camera)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediaPipe Hand Detection</title>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #1a1a1a;
            color: white;
            text-align: center;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        h1 {
            margin-bottom: 15px;
            font-size: 24px;
        }
        .video-container {
            width: 100%;
            max-width: 100%;
            margin: 0 auto;
            position: relative;
        }
        video, canvas {
            width: 100%;
            height: auto;
            max-width: 100%;
            border: 2px solid #333;
            border-radius: 8px;
            display: block;
            margin: 0 auto;
        }
        canvas {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
        }
        video {
            /* Video not mirrored */
        }
        canvas {
            transform: translateX(-50%); /* Canvas not mirrored */
        }
        .error {
            color: #ff4444;
            padding: 10px;
            margin: 10px;
        }
        @media (max-width: 768px) {
            h1 {
                font-size: 20px;
            }
            body {
                padding: 5px;
            }
        }
    </style>
</head>
<body>
    <h1>🤚 MediaPipe Hand Detection</h1>
    <div class="video-container">
        <video id="input_video" autoplay playsinline></video>
        <canvas id="output_canvas"></canvas>
    </div>
    <div id="error" class="error"></div>

    <script>
        const videoElement = document.getElementById('input_video');
        const canvasElement = document.getElementById('output_canvas');
        const canvasCtx = canvasElement.getContext('2d');
        const errorDiv = document.getElementById('error');

        function onResults(results) {
            canvasCtx.save();
            canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
            canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
            
            if (results.multiHandLandmarks) {
                for (const landmarks of results.multiHandLandmarks) {
                    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 2});
                    drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 1, radius: 3});
                }
            }
            canvasCtx.restore();
        }

        const hands = new Hands({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
            }
        });
        hands.setOptions({
            maxNumHands: 2,
            modelComplexity: 1,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });
        hands.onResults(onResults);

        // Get user media
        async function initCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: 'environment', // Use back camera on mobile
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                });
                videoElement.srcObject = stream;
                
                // Set canvas size to match video
                videoElement.addEventListener('loadedmetadata', () => {
                    canvasElement.width = videoElement.videoWidth;
                    canvasElement.height = videoElement.videoHeight;
                });

                // Start processing frames
                function processFrame() {
                    if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
                        hands.send({image: videoElement});
                    }
                    requestAnimationFrame(processFrame);
                }
                processFrame();
            } catch (err) {
                errorDiv.textContent = 'Error accessing camera: ' + err.message;
                console.error('Camera error:', err);
            }
        }

        // Initialize when page loads
        initCamera();
    </script>
</body>
</html>
"""

def generate_frames():
    """Generator function to stream video frames"""
    global camera_initialized
    
    # Check if camera is initialized
    if not camera_initialized or not cpr_assistant.camera or not cpr_assistant.camera.isOpened():
        # Send error frame
        error_img = cv2.zeros((480, 640, 3), dtype=cv2.uint8)
        cv2.putText(error_img, "Camera not initialized", (50, 220),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(error_img, "Check server logs", (50, 260),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        error_frame = cv2.imencode('.jpg', error_img)[1].tobytes()
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
        return
    
    frame_count = 0
    while cpr_assistant.running:
        ret, frame = cpr_assistant.camera.read()
        if not ret:
            print("Failed to read frame from camera")
            break
        
        # Process frame with MediaPipe hand detection
        try:
            processed_frame, _, _ = cpr_assistant.process_frame(frame)
        except Exception as e:
            print(f"Error processing frame: {e}")
            processed_frame = frame  # Use original frame if processing fails
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        frame_count += 1
        
        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )

# Cleanup function
def cleanup():
    """Cleanup camera resources"""
    cpr_assistant.running = False
    if cpr_assistant.camera:
        cpr_assistant.camera.release()
    cv2.destroyAllWindows()

# Register cleanup function
atexit.register(cleanup)

if __name__ == '__main__':
    print("🚀 Starting MediaPipe Hand Detection Server...")
    print("📱 Each device will use its own camera (client-side processing)")
    
    # Try to use HTTPS if certificates exist, otherwise use HTTP
    cert_path = os.path.join(os.path.dirname(__file__), 'certs', 'cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'certs', 'key.pem')
    
    use_https = os.path.exists(cert_path) and os.path.exists(key_path)
    
    if use_https:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        print("📱 Access from your computer: https://localhost:5001")
        print("📱 Access from your phone: https://YOUR_LAPTOP_IP:5001")
        print("\nTo find your laptop IP:")
        print("  macOS: ifconfig | grep 'inet ' | grep -v 127.0.0.1")
        print("\nPress Ctrl+C to stop")
        
        try:
            app.run(host='0.0.0.0', port=5001, debug=False, threaded=True, ssl_context=context)
        except KeyboardInterrupt:
            cleanup()
            print("\n👋 Server stopped")
    else:
        print("⚠️  No SSL certificates found. Using HTTP (may not work on iOS Safari).")
        print("📱 Access from your computer: http://localhost:5001")
        print("📱 Access from your phone: http://YOUR_LAPTOP_IP:5001")
        print("\nTo find your laptop IP:")
        print("  macOS: ifconfig | grep 'inet ' | grep -v 127.0.0.1")
        print("\n💡 To enable HTTPS, run: ./generate-cert.sh")
        print("Press Ctrl+C to stop")
        
        try:
            app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
        except KeyboardInterrupt:
            cleanup()
            print("\n👋 Server stopped")

