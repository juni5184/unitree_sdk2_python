import sys
import time
import cv2
import numpy as np

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.go2.video.video_client import VideoClient
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_, LowState_


class UnitreeClientBase:
    def __init__(self):
        self.state_manager = RobotStateManager()
        self.combined_callback = None

    def init_channels(self):
        if len(sys.argv) > 1:
            ChannelFactoryInitialize(0, sys.argv[1])
        else:
            ChannelFactoryInitialize(0)

        # Subscribe to state channels
        high_sub = ChannelSubscriber("rt/sportmodestate", SportModeState_)
        high_sub.Init(self.state_manager.state_callback, 1)

        low_sub = ChannelSubscriber("rt/lowstate", LowState_)
        low_sub.Init(self.state_manager.low_state_callback, 1)

    def register_combined_callback(self, callback_fn):
        self.combined_callback = callback_fn


class RobotStateManager:
    def __init__(self):
        self.sport_state = None
        self.low_state = None
        self.waypoint = [0.0, 0.0, 0.0]

    def state_callback(self, msg: SportModeState_):
        self.sport_state = msg

    def low_state_callback(self, msg: LowState_):
        self.low_state = msg

    def set_waypoint(self, waypoint):
        self.waypoint = waypoint

    def extract_robot_state(self):
        if self.sport_state is None or self.low_state is None:
            return None

        state = self.sport_state
        low = self.low_state

        linear_velocity = state.velocity
        angular_velocity = state.imu_state.gyroscope
        quaternion = state.imu_state.quaternion
        rpy = state.imu_state.rpy

        joint_pos = [m.q for m in low.motor_state]
        joint_vel = [m.dq for m in low.motor_state]
        joint_torque = [m.tau_est for m in low.motor_state]

        return {
            "linear_velocity": linear_velocity,
            "angular_velocity": angular_velocity,
            "quaternion": quaternion,
            "rpy": rpy,
            "joint_pos": joint_pos,
            "joint_vel": joint_vel,
            "joint_torque": joint_torque,
            "waypoint": self.waypoint
        }


class VLMClient(UnitreeClientBase):
    def __init__(self):
        super().__init__()
        self.video_client = None  # Lazy init

    def init_video_client(self):
        self.video_client = VideoClient()
        self.video_client.SetTimeout(1.0)
        self.video_client.Init()
        print("[VLM Client] Video streaming started...")

    def process_image(self, image_data, save_path="./custom/processed_image.jpg"):
        image = np.frombuffer(bytes(image_data), dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        if image is None:
            raise RuntimeError("Failed to decode image")

        h, w = image.shape[:2]
        size = min(h, w)
        roi = image[(h-size)//2:(h+size)//2, (w-size)//2:(w+size)//2]
        resized = cv2.resize(roi, (320, 320))   

        cv2.imwrite(save_path, resized)
        return save_path

    def run(self):
        self.init_channels()  # ChannelFactoryInitialize() 여기서 호출됨
        self.init_video_client()

        while True:
            code, image_data = self.video_client.GetImageSample()
            if code != 0 or not image_data:
                time.sleep(0.05)
                continue

            if self.state_manager.sport_state is None or self.state_manager.low_state is None:
                time.sleep(0.05)
                continue

            pos_vec = self.state_manager.sport_state.position
            rpy_vec = self.state_manager.sport_state.imu_state.rpy

            if self.combined_callback:
                try:
                    waypoint = self.combined_callback(self.process_image(image_data), pos_vec, rpy_vec)
                    if waypoint is not None:
                        self.state_manager.set_waypoint(waypoint)
                except Exception as e:
                    print("[VLM Client] Callback error:", e)
            else:
                print("[VLM Client] pos:", pos_vec, "rpy:", rpy_vec)
            print("[VLM Client] Current Waypoint:", self.state_manager.waypoint, "\n")


class RLAgentClient(UnitreeClientBase):
    def run(self):
        self.init_channels()
        print("[RL Agent Client] Control loop started...")

        while True:
            robot_state = self.state_manager.extract_robot_state()
            if robot_state is None:
                print("[RL Agent Client] Waiting for state data...")
                time.sleep(0.05)
                continue

            if self.combined_callback:
                try:
                    target_joint_pos, target_joint_vel, cmd_vel = self.combined_callback(robot_state)

                    # Print action outputs
                    print("[RL Agent] Action output:")
                    print("Target joint pos:", target_joint_pos)
                    print("Target joint vel:", target_joint_vel)
                    print("Cmd vel:", cmd_vel)

                except Exception as e:
                    print("[RL Agent Client] Callback error:", e)
            else:
                print("[RL Agent] Linear vel:", robot_state["linear_velocity"])
                print("[RL Agent] Yaw:", robot_state["rpy"][2])


# # Example usage:
# def your_callback_function(image_data, pos_vec, rpy_vec):
#     # 이미지 저장 및 처리 예시
#     processed_image_path = process_image(image_data, "./custom/processed_image.jpg")
#     print("Processed image saved to:", processed_image_path)
#     print("Position:", pos_vec)
#     print("RPY:", rpy_vec)

#     # Waypoint 예시 (임의값)
#     new_waypoint = [pos_vec[0] + 1.0, pos_vec[1] + 1.0, rpy_vec[2]]
#     return new_waypoint

# if __name__ == "__main__":
#     client = VLMClient()
#     client.register_combined_callback(your_callback_function)
#     client.run()