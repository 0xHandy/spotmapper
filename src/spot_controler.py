import bosdyn.client
    import bosdyn.client.lease
    import bosdyn.util
    import time
    import yaml
    from src import spot_utils

    def main():
        with open('config/spot_config.yaml', 'r') as file:
            config = yaml.safe_load(file)

        sdk = bosdyn.client.create_standard_sdk('SpotController')
        robot = sdk.create_robot(config['spot_ip'])
        bosdyn.client.util.authenticate(robot)
        robot.time_sync.wait_for_sync()

        lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.name)
        with bosdyn.client.lease.Lease(lease_client, acquire=True, return_on_exit=True):
            # Control logic here
            #---------------------------------------------------------------------------
            spot_utils.stand(robot)
            time.sleep(2)
            navigation.navigate_to(robot, 1.0, 0.0, 0.0) #example of navigation
            time.sleep(5)
            image = spot_utils.get_camera_image(robot)
            data_processing.process_image(image)
            spot_utils.sit(robot)

    if __name__ == "__main__":
        try:
            main()
        except Exception as e:
            print(f"Error: {e}")
