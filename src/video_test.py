import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandClient
from bosdyn.client.image import ImageClient
import cv2
import numpy as np
import time

def get_spot_video(robot_ip, save_path="spot_video.avi", duration=10, fps=40):
    bosdyn.client.util.setup_logging()
    sdk = bosdyn.client.create_standard_sdk('SpotVideoClient')
    robot = sdk.create_robot(robot_ip)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()
    
    image_client = robot.ensure_client(ImageClient.default_service_name)
    
    image_sources = image_client.list_image_sources()
    print("Available image sources:", image_sources)
    
    # Choose an image source (e.g., 'frontleft_fisheye_image')
    image_source = "frontleft_fisheye_image"
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(save_path, fourcc, fps, (640, 480))
    
    start_time = time.time()
    while time.time() - start_time < duration:
        image_responses = image_client.get_image_from_sources([image_source])
        if not image_responses:
            print("Failed to get image")
            continue
        
        img = np.frombuffer(image_responses[0].shot.image.data, dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        if img is None:
            print("Error decoding image")
            continue
        
        img = cv2.resize(img, (640, 480))
        out.write(img)
        cv2.imshow('Spot Camera', img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    out.release()
    cv2.destroyAllWindows()
    print("Video saved to", save_path)

if __name__ == "__main__":
    robot_ip = "192.168.80.3"  # Change to your Spot's IP address
    get_spot_video(robot_ip)