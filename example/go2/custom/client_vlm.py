import sys
import time
import cv2
import numpy as np

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.go2.video.video_client import VideoClient
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_, LowState_

# Global variables (store latest state in callback)
g_state = None
g_low_state = None
combined_callback = None
g_waypoint = None
save_path = "./custom/processed_image.jpg"

# Callback functions
def state_callback(msg: SportModeState_):
    global g_state
    g_state = msg

def low_state_callback(msg: LowState_):
    global g_low_state
    g_low_state = msg

def register_combined_callback(callback_fn):
    global combined_callback
    combined_callback = callback_fn  # Expect callback to return waypoint

def set_waypoint(waypoint):
    global g_waypoint
    g_waypoint = waypoint


def process_image(image_data, save_path):
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

def vllm_main_process():
    print("Initializing...")

    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    # Initialize video client and subscribers
    video_client = VideoClient()
    video_client.SetTimeout(1.0)
    video_client.Init()

    high_sub = ChannelSubscriber("rt/sportmodestate", SportModeState_)
    high_sub.Init(state_callback, 1)

    low_sub = ChannelSubscriber("rt/lowstate", LowState_)
    low_sub.Init(low_state_callback, 1)

    print("[client_vlm] Streaming started...")

    global g_waypoint
    g_waypoint = [0.0, 0.0, 0.0]  # default waypoint

    while True:
        code, image_data = video_client.GetImageSample()
        if code != 0 or not image_data:
            time.sleep(0.05)
            continue

        if g_state is None or g_low_state is None:
            time.sleep(0.05)
            continue

        pos_vec = g_state.position
        rpy_vec = g_state.imu_state.rpy

        if combined_callback is not None:
            try:
                # waypoint return from callback
                waypoint = combined_callback(image_data, pos_vec, rpy_vec)
                if waypoint is not None:
                    g_waypoint = waypoint  # update waypoint
            except Exception as e:
                print("Callback error:", e)
        else:
            print("pos:", pos_vec, "rpy:", rpy_vec)
        
        print("Waypoint:", g_waypoint)


# if __name__ == "__main__":
#     vllm_main_process()