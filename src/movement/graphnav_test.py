import time
import numpy as np

from bosdyn.client.image import ImageClient, build_image_request
import bosdyn.client
import bosdyn.client.lease
from bosdyn.client.util import authenticate, setup_logging
from bosdyn.client.lease import LeaseKeepAlive, LeaseClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.graph_nav import GraphNavClient
import threading
from PIL import Image


ROBOT_IP = "192.168.80.3"

obstacle_detected = False



def detect_front_obstacle_loop(stop_event):
    global obstacle_detected
    image_counter = 0
    while not stop_event.is_set():
        try:
            image_sources = ['frontright_depth', 'frontleft_depth']
            image_responses = image_client.get_image_from_sources(image_sources)

            if len(image_responses) != 2:
                continue

            images_np = []
            for img in image_responses:
                data = np.frombuffer(img.shot.image.data, dtype=np.uint16)
                img_np = data.reshape((img.shot.image.rows, img.shot.image.cols))
                #images_np.append(img_np)

                # Otočení o 90° ve směru hodinových ručiček
                img_rotated = np.rot90(img_np, k=-1)
                images_np.append(img_rotated)

            

            stitched_depth = np.hstack(images_np)
            center_h, center_w = stitched_depth.shape[0] // 2, stitched_depth.shape[1] // 2
            region = stitched_depth[center_h - 10:center_h + 10, center_w - 10:center_w + 10]


            # Filtruj nuly (chybějící data)
            region_valid = region[region > 0]

            # Pokud něco zbylo, vypočítej vzdálenost
            if region_valid.size > 0:
                avg_distance_mm = np.mean(region_valid)
                avg_distance_m = avg_distance_mm / 1000.0

            print(f"[OBSTACLE CHECK] Středová vzdálenost: {avg_distance_m:.2f} m")

            depth_image = Image.fromarray(stitched_depth, mode='I;16')
            filename = f"stitched_depth_{image_counter:04d}.png"
            #depth_image.save(filename)
            #print(f"[SAVE] Uložen obrázek: {filename}")
            image_counter += 1

            if avg_distance_m <= 0.30:
                # Pokud je průměrná vzdálenost menší než 0.30 m, detekujeme překážku
                print("Překážka detekována! Zastavuji")
                #obstacle_detected = True
                #stop_cmd = RobotCommandBuilder.stop_command()
                #command_client.robot_command(stop_cmd)
                go_backward(0, 0.5)
                go_90()
                time.sleep(1)
                
                

        except Exception as e:
            print(f"Chyba ve vlákně pro detekci překážek: {e}")
        time.sleep(0.3)  # Četnost kontrol

def go_straight(step, step_length, duration=3):
    global obstacle_detected

    print(f"Krok {step + 1} dopředu")
    end_time = time.time() + duration
    walk_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=step_length, v_y=0.0, v_rot=0.0)
    command_client.robot_command(walk_cmd, end_time_secs=end_time)

    ## Čekání s kontrolou překážky
    #while time.time() < end_time + 1:
    #    if obstacle_detected:
    #        print("Překážka zjištěna během kroku, zastavuji.")
    #        stop_cmd = RobotCommandBuilder.stop_command()
    #        command_client.robot_command(stop_cmd)
    #        return
    #    time.sleep(0.2)  # menší čekání pro kontrolu

    print(f"Krok {step + 1} dopředu")
    duration = 3
    end_time = time.time() + duration
    walk_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=step_length, v_y=0.0, v_rot=0.0)
    command_client.robot_command(walk_cmd, end_time_secs=end_time)
    time.sleep(duration + 1)

def go_backward(step, step_length):
    print(f"Krok {step + 1} dozadu")
    duration = 3
    end_time = time.time() + duration
    walk_cmd = RobotCommandBuilder.synchro_velocity_command(v_x= -step_length, v_y=0.0, v_rot=0.0)
    command_client.robot_command(walk_cmd, end_time_secs=end_time)
    time.sleep(duration + 1)

def go_90():
    print("táčím se o 90°")
    duration = 2
    end_time = time.time() + duration
    rotate_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=0.7)
    command_client.robot_command(rotate_cmd, end_time_secs=end_time)
    time.sleep(duration + 0.6)

def go_sideways(side_step):
    print("Posun do strany")
    duration = 2
    end_time = time.time() + duration
    side_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=-0.2, v_y=side_step, v_rot=0.0)
    command_client.robot_command(side_cmd, end_time_secs=end_time)
    time.sleep(duration + 1)


def full_room_search(grid_steps=3, step_length=0.7):
    
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True):
        robot.power_on(timeout_sec=20)
        stand_cmd = RobotCommandBuilder.synchro_stand_command()
        command_client.robot_command(stand_cmd)
        print("Spot powered on.")
        time.sleep(2)

        stop_event = threading.Event()
        global obstacle_thread 
        obstacle_thread = threading.Thread(target=detect_front_obstacle_loop, args=(stop_event,))
        obstacle_thread.start()

        try:
            print("Zahajuji full-room search...")

            for step in range(grid_steps):
                obstacle_detected = False
                #if obstacle_detected:
                 #   go_backward(step, step_length/2)
                 #   go_90()
                 #   continue

                go_straight(step, step_length)

                # Na posledním kroku už se nemusíme otáčet
                if step == grid_steps - 1:
                    break

                go_90()

                #go_sideways(side_step)

                #print("Otočení zpět")
                #rotate_back_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=-1.2)
                #command_client.robot_command(rotate_back_cmd, end_time_secs=time.time() + 1)
                #time.sleep(1.2)
            print("ukoncuji full-room search")
            stop_event.set()
            obstacle_thread.join()
            sit_cmd = RobotCommandBuilder.synchro_sit_command()
            command_client.robot_command(sit_cmd)
            print("Spot is sitting.")
            time.sleep(2)
            print("Zastavuji Spot")
            stop_cmd = RobotCommandBuilder.stop_command()
            command_client.robot_command(stop_cmd)
            print("Full-room search dokončen.")
        except Exception as e:
            print(f"Chyba: {e}")
            print("Spot is shutting down.")
            



sdk = bosdyn.client.create_standard_sdk("RoomExplorer")
robot = sdk.create_robot(ROBOT_IP)
authenticate(robot)
robot.time_sync.wait_for_sync()
lease_client = robot.ensure_client(LeaseClient.default_service_name)
command_client = robot.ensure_client(RobotCommandClient.default_service_name)
graphnav_client = robot.ensure_client(GraphNavClient.default_service_name)
image_client = robot.ensure_client(ImageClient.default_service_name)
obstacle_thread = None

if __name__ == "__main__":
    #stop_event = threading.Event()
    #obstacle_thread = threading.Thread(target=detect_front_obstacle_loop, args=(stop_event,))
    #obstacle_thread.start()
    #with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True):
    #    robot.power_on(timeout_sec=20)
    #    stand_cmd = RobotCommandBuilder.synchro_stand_command()
    #    command_client.robot_command(stand_cmd)
    #    print("Spot powered on.")
    #    time.sleep(2)
    #    
    

    full_room_search()   
