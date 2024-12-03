import cv2
import os
import face_recognition
from ultralytics import YOLO
import time
import threading
import requests
from datetime import datetime, timedelta
import numpy as np
import base64




# Load YOLO model for detecting people and chairs
model = YOLO('yolov8s.pt')


# MongoDB API endpoint
mongo_url = 'http://localhost:3000/api/restrict'
camera_url = 'http://localhost:3000/api/getcamera/CameraData'
print("camera_url :", camera_url)
threshold = 2  # Set your threshold for alerts
running = True
alert_start_time = None  # For tracking alert duration

# Define margins for bounding boxes
FACE_MARGIN = 40  # Adjust this value as needed for faces
CHAIR_MARGIN = 30  # Adjust this value as needed for chairs

def calculate_intersection(boxA, boxB):
    # Calculate the coordinates of the intersection of two bounding boxes
    xA = max(boxA[0], boxB[0])  # Left side of intersection
    yA = max(boxA[1], boxB[1])  # Top side of intersection
    xB = min(boxA[2], boxB[2])  # Right side of intersection
    yB = min(boxA[3], boxB[3])  # Bottom side of intersection

    # Compute the area of intersection (if any)
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    # Compute the area of both the person and the chair
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    
    # Compute the intersection over union (IoU) score
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def get_camera_details():
    try:
        response = requests.get(camera_url)
        response.raise_for_status()  # Ensure the request was successful
        data = response.json()  # Parse the response as JSON

        # Access the list of cameras within the "data" key
        if isinstance(data.get("data"), list):
            return data["data"]
        else:
            print("Error: Expected a list of cameras but received a different format.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching camera details: {e}")
        return []


def process_video(camera):
    global alert_start_time, vacancy_start_time, vacancy_end_time, person_exceed_start_time, person_exceed_end_time

    # Initialize these variables if they are not already initialized
    if 'vacancy_start_time' not in globals():
        vacancy_start_time = None
    if 'vacancy_end_time' not in globals():
        vacancy_end_time = None
    if 'person_exceed_start_time' not in globals():
        person_exceed_start_time = None
    if 'person_exceed_end_time' not in globals():
        person_exceed_end_time = None

    camera_id = camera['CameraLocationID']
    # camera_username = camera["UserName"]
    # camera_password = camera["Password"]
    # camera_ip = camera["IPAddress"]
    # camera_location_id = camera["CameraLocationID"]

    rtsp_url = f'rtsp://{camera["UserName"]}:{camera["Password"]}@{camera["IPAddress"]}/Streaming/Channels/101'
    print(f"Starting stream for camera ID {camera_id}: {rtsp_url}")
    cap = cv2.VideoCapture(rtsp_url)
    retries = 5

    while not cap.isOpened() and retries > 0:
        print("Failed to open video stream. Retrying in 5 seconds...")
        time.sleep(5)
        cap = cv2.VideoCapture(rtsp_url)
        retries -= 1

    if not cap.isOpened():
        print("Unable to open video stream after retries.")
        return

    print("Video stream opened successfully.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame. Retrying...")
            time.sleep(1)
            continue

        frame_resized = cv2.resize(frame, (640, 380))
        results = model(frame_resized)
        detections = results[0].boxes

        recognized_names = set()
        person_count = 0
        vacant_chairs = 0
        occupied_chairs = 0
        persons = []
        chairs = []
        occupied = True  # or False, based on your condition


        for detection in detections:
            bbox = detection.xyxy[0].cpu().numpy()
            cls = int(detection.cls)
            x1, y1, x2, y2 = map(int, bbox)

            if cls == 0:  # 'person' class
                persons.append((x1, y1, x2, y2))
                person_count += 1
                cv2.rectangle(frame_resized, (x1, y1), (x2, y2), (255, 0, 0), 2)
            elif cls == 56:  # 'chair' class
                chairs.append((x1, y1, x2, y2))

        rgb_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        # face_locations = face_recognition.face_locations(rgb_frame)
        # face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        #     matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        #     name = "Unknown"

        #     if any(matches):
        #         face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        #         best_match_index = np.argmin(face_distances)
        #         if matches[best_match_index]:
        #             name = known_face_names[best_match_index]

        #     recognized_names.add(name)
        #     cv2.rectangle(frame_resized, (left, top), (right, bottom), (0, 255, 0), 2)
        #     cv2.putText(frame_resized, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        for chair in chairs:
            chair_x1, chair_y1, chair_x2, chair_y2 = chair
            occupied = False
            

            for person in persons:
                person_x1, person_y1, person_x2, person_y2 = person
                iou = calculate_intersection((chair_x1, chair_y1, chair_x2, chair_y2), (person_x1, person_y1, person_x2, person_y2))
                if iou > 0.3:  # Adjust this threshold based on accuracy needs
                    occupied = True
                    break    

            color = (0, 0, 255) if occupied else (0, 255, 0)
            if occupied:
                label = "Occupied"
                occupied_chairs += 1
            else:
                label = "Vacant"
                vacant_chairs += 1

            cv2.rectangle(frame_resized, (chair_x1, chair_y1), (chair_x2, chair_y2), color, 2)
            cv2.putText(frame_resized, label, (chair_x1, chair_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        print(f"People Count: {person_count}, Vacant Chairs: {vacant_chairs}, Occupied Chairs: {occupied_chairs}")

        # Handle Vacancy Status
        if vacant_chairs > 0:
            if vacancy_start_time is None:
                vacancy_start_time = time.time()
            vacancy_end_time = time.time()  # Update end time for vacancy
            vacancy_duration = vacancy_end_time - vacancy_start_time
            save_data_to_mongodb(vacant_chairs, camera_id, vacancy_duration, frame_resized, "vacancy_status")
        else:
            if vacancy_start_time is not None:  # Reset the vacancy alert if vacant chairs drop to 0
                vacancy_start_time = None
                vacancy_end_time = None

        # Handle Compliance Policy Exceedance (Person Count)
        if person_count > threshold:
            if person_exceed_start_time is None:
                person_exceed_start_time = time.time()
            person_exceed_end_time = time.time()  # Update end time for exceeding compliance
            person_exceed_duration = person_exceed_end_time - person_exceed_start_time
            save_data_to_mongodb(person_count, camera_id, person_exceed_duration, frame_resized, "compliance_exceedance")
        else:
            if person_exceed_start_time is not None:  # Reset if person count goes below threshold
                person_exceed_start_time = None
                person_exceed_end_time = None

        cv2.putText(frame_resized, f"People Count: {person_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(frame_resized, f"Vacant Place: {vacant_chairs}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame_resized, f"Occupied Place: {occupied_chairs}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("Video", frame_resized)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def detect_objects():
    cameras = get_camera_details()
    threads = []

    for camera in cameras:
        thread = threading.Thread(target=process_video, args=(camera,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()    


def save_data_to_mongodb(count, camera_location_id, alert_duration, alert_frame, scenario):
    timestamp = datetime.now().isoformat()
    alert_frame_base64 = None
    if alert_frame is not None:
        _, buffer = cv2.imencode('.jpg', alert_frame)
        alert_frame_base64 = base64.b64encode(buffer).decode('utf-8')

    # Prepare data dictionary with scenario-based fields
    # Prepare data dictionary with scenario-based fields
    data = {
        "location_id": camera_location_id,
        "timestamp_alert_start": timestamp,
        "timestamp_alert_end": (datetime.now() + timedelta(seconds=alert_duration)).isoformat(),
        "vacant_count_duration": alert_duration if scenario == "vacancy_status" else 0,
        "person_count_duration": alert_duration if scenario == "compliance_exceedance" else 0,
        "scenario": scenario,
    }

    # Include the appropriate fields based on the scenario
    if scenario == "vacancy_status":
        data["vacancy_status"] = f"Vacant Chairs: {count}"
        data["vacant_frame"] = alert_frame_base64
    elif scenario == "compliance_exceedance":
        data["person_count_status"] = f"People Count Exceeds: {count}"
        data["compliance_frame"] = alert_frame_base64
        data["exceeds_compliance_policy"] = count > threshold
        ##data["frame_count_exceeds"] = alert_frame_base64


    try:
        response = requests.post(mongo_url, json=data)
        if response.status_code in [200, 201]:
            print("Data sent successfully to MongoDB.")
        else:
            print(f"Failed to send data to MongoDB: {response.status_code}")
    except Exception as e:
        print(f"Error sending data to MongoDB: {e}")



# Start video processing for multiple cameras
if __name__ == "__main__":
    detect_objects()
