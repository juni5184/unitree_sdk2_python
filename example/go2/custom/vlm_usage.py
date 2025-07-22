from get_robot_state import VLMClient

# Example usage:
def vlm_callback_function(image_path, pos_vec, rpy_vec):
    print("Saved image path:", image_path)
    print("Position:", pos_vec)
    print("RPY:", rpy_vec)

    # Waypoint 예시 (임의값)
    new_waypoint = [pos_vec[0] + 1.0, pos_vec[1] + 1.0, rpy_vec[2]]
    return new_waypoint

if __name__ == "__main__":
    client = VLMClient()
    client.register_combined_callback(vlm_callback_function)
    client.run()