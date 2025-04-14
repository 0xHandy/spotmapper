import time
import random

import bosdyn.client
from bosdyn.client.util import authenticate, create_standard_sdk, setup_logging
from bosdyn.client.lease import LeaseKeepAlive, LeaseClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.graph_nav import GraphNavClient


ROBOT_IP = "192.168.80.3"

def explore_room():
    sdk = create_standard_sdk("RoomExplorer")
    robot = sdk.create_robot(ROBOT_IP)
    authenticate(robot)
    robot.time_sync.wait_for_sync()

    lease_client = robot.ensure_client(LeaseClient.default_service_name)
    command_client = robot.ensure_client(RobotCommandClient.default_service_name)
    graphnav_client = robot.ensure_client(GraphNavClient.default_service_name)

    with LeaseKeepAlive(lease_client, must_acquire=True):
        robot.power_on(timeout_sec=20)
        print("Spot powered on.")

        # Start recording GraphNav map
        print("Starting GraphNav recording...")
        graphnav_client.clear_graph()
        graphnav_client.upload_locks()
        graphnav_client.start_recording()

        try:
            print("Starting autonomous room exploration...")
            for i in range(6):  # Projde 6 kroků = cca 1–2 minuty průzkumu
                # Vpřed 3 sekundy
                walk_cmd = RobotCommandBuilder.synchro_velocity_command(
                    v_x=0.5, v_y=0.0, v_rot=0.0)
                command_client.robot_command(walk_cmd, end_time_secs=time.time() + 3)
                time.sleep(3)

                # Náhodně se otoč vlevo/vpravo
                direction = random.choice([-0.6, 0.6])
                turn_cmd = RobotCommandBuilder.synchro_velocity_command(
                    v_x=0.0, v_y=0.0, v_rot=direction)
                command_client.robot_command(turn_cmd, end_time_secs=time.time() + 2)
                time.sleep(2)

            command_client.robot_command(RobotCommandBuilder.stop_command())
            print("Exploration complete.")

        finally:
            print("Stopping recording...")
            graphnav_client.stop_recording()
            graphnav_client.download_graph('/tmp/spot_automap')
            command_client.robot_command(RobotCommandBuilder.synchro_sit_command())
            print("Spot is now sitting. Map saved to /tmp/spot_automap.")

if __name__ == "__main__":
    explore_room()
