import argparse
import sys
import time
import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_state import RobotStateClient

def hello_spot(config):
    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('HelloSpotClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()
    
    assert not robot.is_estopped(), 'Robot is estopped. Please use an E-Stop client to configure E-Stop.'
    
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    command_client = robot.ensure_client(RobotCommandClient.default_service_name)
    
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        robot.power_on(timeout_sec=20)
        print("Robot powered on.")
        
        while True:
            command = input("Enter command (stand/sit/walk/stop/exit): ").lower()
            commands = command.split(" ")
            
            if commands[0] == "stand":
                stand_cmd = RobotCommandBuilder.synchro_stand_command()
                command_client.robot_command(stand_cmd)
                print("Spot is standing.")
                
            elif commands[0] == "sit":
                sit_cmd = RobotCommandBuilder.synchro_sit_command()
                command_client.robot_command(sit_cmd)
                print("Spot is sitting.")
                
            elif commands[0] == "walk":
                walk_cmd = RobotCommandBuilder.synchro_velocity_command(v_x=float(commands[1]), v_y=float(commands[2]), v_rot=float(commands[3]))
                command_client.robot_command(walk_cmd, end_time_secs=time.time()+5)
                print("Spot is walking.")
                
            elif commands[0] == "stop":
                stop_cmd = RobotCommandBuilder.stop_command()
                command_client.robot_command(stop_cmd)
                print("Spot stopped.")
                
            elif commands[0] == "exit":
                sit_cmd = RobotCommandBuilder.synchro_sit_command()
                command_client.robot_command(sit_cmd)
                power_off_cmd = RobotCommandBuilder.safe_power_off_command()
                command_client.robot_command(power_off_cmd)
                print("Spot is shutting down.")
                break
            
            else:
                print("Invalid command.")

def main():
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    try:
        hello_spot(options)
    except Exception as exc:
        print(f"Error: {exc}")
        return False
    return True

if __name__ == '__main__':
    if not main():
        sys.exit(1)
