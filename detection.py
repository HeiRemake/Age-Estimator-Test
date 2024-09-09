from flask import Flask, render_template, Response, request, jsonify
import cv2
import requests
import numpy as np

app = Flask(__name__)

# Replace with your actual API endpoint and API key
API_URL = "https://telkom-ai-dag.api.apilogy.id/Age_Estimator_GPU/0.0.1/v1"
API_KEY = "adDwfx485WAOwGeaiVcRu4at5nyFvHp4"

# OpenCV capture
camera = cv2.VideoCapture(0)  # Capture from the default webcam

def send_frame_to_api(frame):
    # Encode frame as JPEG
    _, encoded_image = cv2.imencode('.jpg', frame)
    
    # Prepare file for API call
    files = {'file': encoded_image.tobytes()}
    
    # Headers for the API request
    headers = {
        'x-api-key': API_KEY,
        'accept': 'application/json'
    }
    
    # Send the frame to the API
    response = requests.post(API_URL, files=files, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def generate_frames():
    while True:
        success, frame = camera.read()  # Capture frame-by-frame
        if not success:
            break
        
        # Resize the frame to speed up processing (optional)
        frame = cv2.resize(frame, (640, 480))

        # Send the frame to the API
        api_response = send_frame_to_api(frame)

        if api_response:
            for detection in api_response['data']:
                # Get bounding box coordinates
                x1, y1, x2, y2 = [int(c) for c in detection['location']['x1y1x2y2']]
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Display age and gender
                label = f"{detection['gender']} {detection['age']:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Encode frame back to JPEG format to send to the client
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Stream the video frame to the browser

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML page

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')  # Streaming response

if __name__ == '__main__':
    app.run(debug=True)
