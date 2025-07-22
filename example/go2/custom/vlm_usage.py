from get_robot_state import VLMClient, process_image

# Example usage:
def your_callback_function(image_data, pos_vec, rpy_vec):
    # 이미지 저장 및 처리 예시
    processed_image_path = process_image(image_data, "./custom/processed_image.jpg")
    print("Saved image:", processed_image_path)
    print("Position:", pos_vec)
    print("RPY:", rpy_vec)

    # Waypoint 예시 (임의값)
    new_waypoint = [pos_vec[0] + 1.0, pos_vec[1] + 1.0, rpy_vec[2]]
    return new_waypoint

if __name__ == "__main__":
    client = VLMClient()
    client.register_combined_callback(your_callback_function)
    client.run()