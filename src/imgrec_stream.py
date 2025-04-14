import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandClient
from bosdyn.client.image import ImageClient
import cv2
import numpy as np
import time
import subprocess

def detect_people_in_image(img):
    net = cv2.dnn.readNetFromCaffe(
        "deploy.prototxt", "mobilenet_iter_73000.caffemodel"
    )

    CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
               "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
               "dog", "horse", "motorbike", "person", "pottedplant",
               "sheep", "sofa", "train", "tvmonitor"]

    (h, w) = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            class_id = int(detections[0, 0, i, 1])
            if CLASSES[class_id] == "person":
                return True

    return False

def get_spot_video_rtsp(robot_ip, duration=60, fps=30):
    bosdyn.client.util.setup_logging()
    sdk = bosdyn.client.create_standard_sdk('SpotVideoClient')
    robot = sdk.create_robot(robot_ip)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    image_client = robot.ensure_client(ImageClient.default_service_name)
    image_source = "frontleft_fisheye_image"

    ffmpeg = subprocess.Popen([
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', '640x480',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-f', 'rtsp',
        'rtsp://localhost:8554/mystream'
    ], stdin=subprocess.PIPE)

    start_time = time.time()
    frame_count = 0
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

        if frame_count % 10 == 0:
            if detect_people_in_image(img):
                print("Člověk detekován!")
            else:
                print("Člověk detekován nebyl.")

        ffmpeg.stdin.write(img.tobytes())

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_count += 1

    ffmpeg.stdin.close()
    ffmpeg.wait()
    print("RTSP stream ukončen.")

if __name__ == "__main__":
    robot_ip = "192.168.80.3"  # Změň na IP adresu tvého Spotu
    get_spot_video_rtsp(robot_ip)
