import time
import numpy as np

from bosdyn.client.image import ImageClient, build_image_request
import bosdyn.client
import bosdyn.client.lease
from bosdyn.client.util import authenticate, setup_logging
from bosdyn.client.lease import LeaseKeepAlive, LeaseClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.graph_nav import GraphNavClient


ROBOT_IP = "192.168.80.3"


def detect_front_obstacle():
    # Získání depth obrázků z obou předních kamer
    image_sources = ['frontleft_depth', 'frontright_depth']
    image_responses = image_client.get_image_from_sources(image_sources)

    if len(image_responses) != 2:
        print("Nebyly načteny oba depth obrázky.")
        return

    # Vytvoření numpy polí z obou obrázků
    images_np = []
    for img in image_responses:
        data = np.frombuffer(img.shot.image.data, dtype=np.uint16)
        img_np = data.reshape((img.shot.image.rows, img.shot.image.cols))
        images_np.append(img_np)

    # Horizontální spojení obrázků
    stitched_depth = np.hstack(images_np)

    # Vyříznutí středového obdélníku
    center_h, center_w = stitched_depth.shape[0] // 2, stitched_depth.shape[1] // 2
    region = stitched_depth[center_h - 10:center_h + 10, center_w - 10:center_w + 10]

    avg_distance_mm = np.mean(region)
    avg_distance_m = avg_distance_mm / 1000.0

    print(f"Středová vzdálenost k překážce: {avg_distance_m:.2f} m")
    return avg_distance_m <= 0.15  # Pokud je překážka blíže než 0.5 m, vrátí True

def go_straight(step, step_length):
    if detect_front_obstacle():
        print("Překážka detekována, zastavuji.")
        go_backward(step, -step_length/4)
        return
    print(f"Krok {step + 1} dopředu")
    # Pojedeme dopředu (v_x), žádný boční pohyb ani rotace
    walk_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=step_length, v_y=0.0, v_rot=0.0)
    command_client.robot_command(walk_cmd, end_time_secs=time.time() + 3)
    time.sleep(4)

def go_backward(step, step_length):
    print(f"Krok {step + 1} dozadu")
    # Pojedeme dopředu (v_x), žádný boční pohyb ani rotace
    walk_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=step_length, v_y=0.0, v_rot=0.0)
    command_client.robot_command(walk_cmd, end_time_secs=time.time() + 3)
    time.sleep(4)

def go_90():
    # Otočíme se o 90° na místě (v_rot = ±1.0 ~ 90°/s), pak popojedeme do strany
    print("táčím se o 90°")
    rotate_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=1.0)
    command_client.robot_command(rotate_cmd, end_time_secs=time.time() + 1)
    time.sleep(1.2)

def go_sideways(side_step):
    print("Posun do strany")
    side_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=-0.2, v_y=side_step, v_rot=0.0)
    command_client.robot_command(side_cmd, end_time_secs=time.time() + 2)
    time.sleep(2)


def full_room_search(grid_steps=15, step_length=0.6, side_step=0.5):
    
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True):
        robot.power_on(timeout_sec=20)
        stand_cmd = RobotCommandBuilder.synchro_stand_command()
        command_client.robot_command(stand_cmd)
        print("Spot powered on.")
        time.sleep(2)
        try:
            print("Zahajuji full-room search...")

            for step in range(grid_steps):
                
                go_straight(step, step_length)

                # Na posledním kroku už se nemusíme otáčet
                if step == grid_steps - 1:
                    break

                go_90()

                go_sideways(side_step)

                #print("Otočení zpět")
                #rotate_back_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=-1.2)
                #command_client.robot_command(rotate_back_cmd, end_time_secs=time.time() + 1)
                #time.sleep(1.2)
        except Exception as e:
            print(f"Chyba: {e}")
            print("Spot is shutting down.")
        finally:
            stop_cmd = RobotCommandBuilder.stop_command()
            command_client.robot_command(stop_cmd)
            print("Full-room search dokončen.")



sdk = bosdyn.client.create_standard_sdk("RoomExplorer")
robot = sdk.create_robot(ROBOT_IP)
authenticate(robot)
robot.time_sync.wait_for_sync()
lease_client = robot.ensure_client(LeaseClient.default_service_name)
command_client = robot.ensure_client(RobotCommandClient.default_service_name)
graphnav_client = robot.ensure_client(GraphNavClient.default_service_name)
image_client = robot.ensure_client(ImageClient.default_service_name)


if __name__ == "__main__":
    full_room_search()   
