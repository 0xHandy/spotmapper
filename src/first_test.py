import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.robot_state
import bosdyn.client.robot_command
import bosdyn.util
import time

def main():
    sdk = bosdyn.client.create_standard_sdk('SpotConsoleControl')
    robot = sdk.create_robot('192.168.80.3') # idk the real address
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.name)
    with bosdyn.client.lease.Lease(lease_client, acquire=True, return_on_exit=True):
        robot_state_client = robot.ensure_client(bosdyn.client.robot_state.RobotStateClient.name)
        robot_command_client = robot.ensure_client(bosdyn.client.robot_command.RobotCommandClient.name)

        while True:
            command = input("Enter command (stand/sit/walk/exit): ").lower()

            if command == "stand":
                # Code to make Spot stand
                command_client = robot.ensure_client(bosdyn.client.robot_command.RobotCommandClient.name)
                stand_cmd = bosdyn.client.robot_command.RobotCommandBuilder.synchro_stand_command()
                command_client.robot_command(stand_cmd)
                print("Spot is standing.")

            elif command == "sit":
                # Code to make Spot sit
                command_client = robot.ensure_client(bosdyn.client.robot_command.RobotCommandClient.name)
                sit_cmd = bosdyn.client.robot_command.RobotCommandBuilder.synchro_sit_command()
                command_client.robot_command(sit_cmd)
                print("Spot is sitting.")

            elif command == "walk":
                # Code to make Spot walk
                #code to walk the robot.
                velocity_cmd = bosdyn.client.robot_command.RobotCommandBuilder.velocity_command(v_x=0.5, v_y=0.0, v_rot=0.0)
                command_client.robot_command(velocity_cmd, end_time_secs=time.time()+2)
                print("Spot is walking forward.")

            elif command == "exit":
                break

            else:
                print("Invalid command.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
