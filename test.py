import cv2
import requests
from datetime import datetime, timedelta
import base64
from ultralytics import YOLO
import numpy as np
from deepface import DeepFace
from PIL import Image  # For image processing
import io
from PIL import Image
import warnings

warnings.filterwarnings("ignore")

# Initialize YOLO model for person detection
model = YOLO('yolov8s.pt')

# MongoDB API endpoints
MONGO_URL = 'http://localhost:3000/api/UnauthorizedEntry'  # Ensure this URL is correct
CAMERA_URL = 'http://localhost:3000/api/getcamera/CameraData'
EMPLOYEE_URL = 'http://localhost:3000/api/getEmployee/LogInData'

# Globals for storing known faces
KNOWN_FACE_ENCODINGS = []
KNOWN_FACE_NAMES = []

def get_employee_details():
    """Fetch employee details and their face encodings."""
    try:
        response = requests.get(EMPLOYEE_URL)
        response.raise_for_status()
        employee_data = response.json()

        if not employee_data:
            print("No employee data found.")
            return []

        for employee in employee_data:
            employee_id = employee.get('EmployeeID')
            image_data = employee.get('EmployeeImage', {}).get('data')

            if employee_id and image_data:
                try:
                    # Decode and validate the image
                    image_bytes = bytes(image_data)
                    image = Image.open(io.BytesIO(image_bytes))

                    # Ensure the image has 3 channels (RGB) by removing alpha channel (if present)
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')

                    
                    image_array = np.array(image)
                    print(f"Decoded image for Employee {employee_id}, Shape: {image_array.shape}")

                    # Use DeepFace to extract face embeddings
                    try:
                        embeddings = DeepFace.represent(image_array, model_name='VGG-Face', enforce_detection=False)
                        if embeddings and isinstance(embeddings, list) and len(embeddings) > 0:
                            KNOWN_FACE_ENCODINGS.append(embeddings[0]['embedding'])
                            KNOWN_FACE_NAMES.append(employee_id)
                            print(f"Encoded face for Employee {employee_id}.")
                        else:
                            print(f"No face or embeddings detected for Employee {employee_id}.")
                    except Exception as e:
                        print(f"Error processing face for Employee {employee_id}: {e}")
                except Exception as e:
                    print(f"Error decoding image for Employee {employee_id}: {e}")
        return employee_data
    except requests.RequestException as e:
        print(f"Error fetching employee data: {e}")
        return []

def store_unauthorized_entry(employee_id, location_id, location_name, start_timestamp, end_timestamp, alert_frame):
    """Store unauthorized entry in the MongoDB database."""
    try:
        _, buffer = cv2.imencode('.jpg', alert_frame)
        alert_frame_base64 = base64.b64encode(buffer).decode('utf-8')

        # Calculate the duration (seconds, minutes, hours)
        duration_seconds = (end_timestamp - start_timestamp).total_seconds()
        duration_minutes = duration_seconds / 60
        duration_hours = duration_minutes / 60

        unauthorized_entry = {
            "employee_id": employee_id,
            "scenario": "unauthorized entry",
            "CameraLocationID": location_id,
            "location_name": location_name,
            "start_timestamp": start_timestamp.isoformat(),
            "end_timestamp": end_timestamp.isoformat(),
            "duration": {
                "seconds": round(duration_seconds),
                "minutes": round(duration_minutes),
                "hours": round(duration_hours, 2),
            },
            "frame": alert_frame_base64
        }

        response = requests.post(MONGO_URL, json=unauthorized_entry)
        if response.status_code == 200:
            print("Unauthorized entry stored successfully.")
        else:
            print(f"Failed to store unauthorized entry. Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error storing unauthorized entry: {e}")

def get_camera_details():
    """Fetch camera details from the server."""
    try:
        response = requests.get(CAMERA_URL)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.RequestException as e:
        print(f"Error fetching camera details: {e}")
        return []

def is_authorized(employee_details, camera):
    """Check if the employee is authorized for the given camera location."""
    if camera.get('CameraVisibility', True):
        if employee_details.get('Location') == camera.get('CameraLocationID'):
            return True
    return False

def process_video(camera, employee_details):
    """Process video stream for detecting unauthorized entries."""
    camera_id = camera.get("CameraLocationID", "Unknown")
    rtsp_url = f'rtsp://{camera["UserName"]}:{camera["Password"]}@{camera["IPAddress"]}/Streaming/Channels/101'
    print(f"Starting stream for camera ID {camera_id}: {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url)
    retries = 5

    while not cap.isOpened() and retries > 0:
        print(f"Retrying connection to camera {camera_id}...")
        cap = cv2.VideoCapture(rtsp_url)
        retries -= 1

    if not cap.isOpened():
        print(f"Failed to connect to camera {camera_id}.")
        return

    alert_start_time = None  # To track when an unauthorized entry starts
    alert_end_time = None  # To track when the unauthorized entry ends

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to grab frame for camera {camera_id}.")
            continue

        # Resize the frame for faster processing
        frame_resized = cv2.resize(frame, (1280, 720))
        results = model(frame_resized, conf=0.4)

        # Extract YOLO detections (persons)
        detected_persons = []
        for box in results[0].boxes:
            class_id = int(box.cls)
            if class_id == 0:  # Class 0 is 'person' in COCO dataset
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                detected_persons.append((x1, y1, x2, y2))

        # Process the full frame for face detection using DeepFace.extract_faces
        detected_faces = DeepFace.extract_faces(frame_resized, detector_backend='mtcnn', enforce_detection=False)
        print(f"Detected faces in the frame: {len(detected_faces)}")

        alert_displayed = False  # Flag to track if alert has been shown

        if len(detected_faces) > 0:
            for face in detected_faces:
                try:

                    face_image = face['face']
                    if face_image.shape[2] == 4:  # Check if it's RGBA
                        face_image = cv2.cvtColor(face_image, cv2.COLOR_BGRA2BGR)
                    # Use DeepFace to extract face embeddings
                    face_encoding = DeepFace.represent(face['face'], model_name='VGG-Face', enforce_detection=False)

                    # Ensure face_encoding is not empty
                    if face_encoding and isinstance(face_encoding, list) and len(face_encoding) > 0:
                        face_encoding = face_encoding[0]['embedding']

                        # Compare embeddings with known faces
                        best_match_index = None
                        min_distance = float('inf')
                        
                        for i, known_encoding in enumerate(KNOWN_FACE_ENCODINGS):
                            distance = np.linalg.norm(np.array(known_encoding) - np.array(face_encoding))
                            if distance < min_distance:
                                min_distance = distance
                                best_match_index = i

                        threshold = 0.7
                        if best_match_index is not None and min_distance < threshold:
                            employee_id = KNOWN_FACE_NAMES[best_match_index]
                            print(f"Employee ID matched: {employee_id}")

                            # Check authorization
                            if is_authorized(employee_details, camera):
                                print(f"Authorized access for Employee {employee_id}.")
                            else:
                                print(f"Unauthorized entry detected for Employee {employee_id}.")
                                if alert_start_time is None:
                                    alert_start_time = datetime.now()  # Start the alert timer

                                alert_end_time = datetime.now() + timedelta(minutes=5)  # Set the alert end time
                                store_unauthorized_entry(
                                    employee_id,
                                    camera["CameraLocationID"],
                                    camera["CameraLocationName"],
                                    alert_start_time,
                                    alert_end_time,
                                    frame
                                )

                                # Display alert on frame
                                cv2.putText(frame_resized, "UNAUTHORIZED ENTRY DETECTED", (50, 50), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                                alert_displayed = True
                        else:
                            print("No match found. Unauthorized entry detected.")
                            if alert_start_time is None:
                                alert_start_time = datetime.now()

                            alert_end_time = datetime.now() + timedelta(minutes=5)
                            store_unauthorized_entry(
                                "Unknown",
                                camera["CameraLocationID"],
                                camera["CameraLocationName"],
                                alert_start_time,
                                alert_end_time,
                                frame
                            )

                            # Display alert on frame
                            cv2.putText(frame_resized, "UNAUTHORIZED ENTRY DETECTED", (50, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                            alert_displayed = True
                    else:
                        print(f"No embeddings found for face.")
                except Exception as e:
                    print(f"Error during face matching: {e}")
        else:
            print("No faces detected in this frame.")

        # Render detections on the frame
        for (x1, y1, x2, y2) in detected_persons:
            color = (0, 0, 255)  # Red for unauthorized
            cv2.rectangle(frame_resized, (x1, y1), (x2, y2), color, 2)

        if alert_displayed:
            cv2.imshow("Alert Frame", frame_resized)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

def main():
    """Main function to start the monitoring system."""
    print("Fetching camera details and employee data...")
    cameras = get_camera_details()
    employee_details = get_employee_details()

    if cameras and employee_details:
        for camera in cameras:
            process_video(camera, employee_details)
    else:
        print("Error: No cameras or employee details found.")

if __name__ == "__main__":
    main()
