import bosdyn.client.robot_command
    import bosdyn.client.image
    from bosdyn.api import image_pb2
    import cv2
    import numpy as np

    def stand(robot):
        command_client = robot.ensure_client(bosdyn.client.robot_command.RobotCommandClient.name)
        stand_cmd = bosdyn.client.robot_command.RobotCommandBuilder.synchro_stand_command()
        command_client.robot_command(stand_cmd)

    def sit(robot):
        command_client = robot.ensure_client(bosdyn.client.robot_command.RobotCommandClient.name)
        sit_cmd = bosdyn.client.robot_command.RobotCommandBuilder.synchro_sit_command()
        command_client.robot_command(sit_cmd)

    def get_camera_image(robot):
        image_client = robot.ensure_client(bosdyn.client.image.ImageClient.name)
        image_responses = image_client.get_image([image_pb2.ImageSource.FRONTLEFT_FISHEYE])
        image = image_responses[0]
        img = np.frombuffer(image.data, dtype=np.uint8)
        img = cv2.imdecode(img, -1)
        return img
