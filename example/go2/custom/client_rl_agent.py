import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_, LowState_

# Global variables
g_state = None
g_low_state = None
combined_callback = None
g_waypoint = None

def set_waypoint(waypoint):
    global g_waypoint
    g_waypoint = waypoint

# Callback register
def register_combined_callback(callback_fn):
    global combined_callback
    combined_callback = callback_fn

# Unitree state callbacks
def state_callback(msg: SportModeState_):
    global g_state
    g_state = msg

def low_state_callback(msg: LowState_):
    global g_low_state
    g_low_state = msg

def extract_robot_state():
    # Base linear and angular velocity
    linear_velocity = g_state.velocity
    angular_velocity = g_state.imu_state.gyroscope

    # IMU quaternion and yaw
    quaternion = g_state.imu_state.quaternion
    rpy = g_state.imu_state.rpy

    # Joint state
    joint_pos = []
    joint_vel = []
    for motor in g_low_state.motor_state:
        joint_pos.append(motor.q)
        joint_vel.append(motor.dq)

    # Build robot state dict
    robot_state = {
        "linear_velocity": linear_velocity,
        "angular_velocity": angular_velocity,
        "quaternion": quaternion,
        "rpy": rpy,
        "joint_pos": joint_pos,
        "joint_vel": joint_vel,
        "waypoint": g_waypoint
    }

    return robot_state

def rl_agent_main_process():
    print("Initializing RL Agent...")

    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    # Initialize channel subscribers
    high_sub = ChannelSubscriber("rt/sportmodestate", SportModeState_)
    high_sub.Init(state_callback, 1)

    low_sub = ChannelSubscriber("rt/lowstate", LowState_)
    low_sub.Init(low_state_callback, 1)

    print("[client_rl_agent] Streaming started...")

    while True:
        if g_state is None or g_low_state is None:
            print("Waiting for state data...")
            time.sleep(0.05)
            continue

        robot_state = extract_robot_state()

        if combined_callback is not None:
            try:
                # action return from callback
                target_joint_pos, target_joint_vel, cmd_vel = combined_callback(robot_state)


            except Exception as e:
                print("Callback error:", e)
        else:
            print("[Default] Linear vel:", robot_state["linear_velocity"])
            print("[Default] Yaw:", robot_state["rpy"][2])
    
        # print action
        print("[RL Agent] Action output:")
        print("Target joint pos:", target_joint_pos)
        print("Target joint vel:", target_joint_vel)
        print("Cmd vel:", cmd_vel)

# if __name__ == "__main__":
#     rl_agent_main_process()
