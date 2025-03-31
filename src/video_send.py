import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandClient
from bosdyn.client.image import ImageClient
import cv2
import numpy as np
import time
import ffmpeg

def stream_rtsp(rtsp_url):
    process = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='1280x480')
        .output(rtsp_url, format='rtsp', vcodec='libx264', preset='ultrafast', tune='zerolatency')
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )
    return process

def get_spot_video(robot_ip, save_path="spot_video.avi", duration=10, fps=10, rtsp_url=None):
    bosdyn.client.util.setup_logging()
    sdk = bosdyn.client.create_standard_sdk('SpotVideoClient')
    robot = sdk.create_robot(robot_ip)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()
    
    image_client = robot.ensure_client(ImageClient.default_service_name)
    
    image_sources = ["frontleft_fisheye_image", "frontright_fisheye_image"]
    print("Available image sources:", image_sources)
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(save_path, fourcc, fps, (1280, 480))
    
    rtsp_process = None
    if rtsp_url:
        rtsp_process = stream_rtsp(rtsp_url)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        image_responses = image_client.get_image_from_sources(image_sources)
        if len(image_responses) < 2:
            print("Failed to get images")
            continue
        
        img_left = np.frombuffer(image_responses[0].shot.image.data, dtype=np.uint8)
        img_left = cv2.imdecode(img_left, cv2.IMREAD_COLOR)
        
        img_right = np.frombuffer(image_responses[1].shot.image.data, dtype=np.uint8)
        img_right = cv2.imdecode(img_right, cv2.IMREAD_COLOR)
        
        if img_left is None or img_right is None:
            print("Error decoding images")
            continue
        
        img_left = cv2.resize(img_left, (640, 480))
        img_right = cv2.resize(img_right, (640, 480))
        stitched_img = np.hstack((img_left, img_right))
        
        out.write(stitched_img)
        cv2.imshow('Spot Stitched Camera', stitched_img)
        
        if rtsp_url and rtsp_process:
            rtsp_process.stdin.write(stitched_img.tobytes())
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    out.release()
    if rtsp_process:
        rtsp_process.stdin.close()
        rtsp_process.wait()
    cv2.destroyAllWindows()
    print("Video saved to", save_path)

if __name__ == "__main__":
    robot_ip = "192.168.80.3"  # Spot's Wi-Fi IP
    rtsp_url = "rtsp://192.168.80.3:554/stream"  # RTSP stream address
    get_spot_video(robot_ip, rtsp_url=rtsp_url)
