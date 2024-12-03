from threading import Thread
from app import detect_objects
from test import main
#from smoking import start_camera_smoking

# Define a function that starts both threads
def run_concurrently():
    # Create threads for each function
    app_thread = Thread(target=detect_objects, daemon=True)
    test_thread = Thread(target=main, daemon=True)
    

    # Start both threads
    print("Starting detect_objects thread")
    app_thread.start()
    print("Starting start_camera_streams thread")
    test_thread.start()
    

    # Optionally, wait for both threads to complete
    app_thread.join()
    test_thread.join()
    

# Run the threads concurrently
if __name__ == "__main__":
    run_concurrently()
