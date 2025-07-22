from client_vlm import register_combined_callback, process_image, vllm_main_process

def vlm_callback(image_data, pos_vec, rpy_vec):
    image = process_image(image_data, "./custom/processed_image.jpg")
    print("Saved image: ", image)
    print("Position:", pos_vec)
    print("RPY:", rpy_vec)

    # vlm process
    # TODO: implement your vlm process here

    # waypoint return to callback
    vlm_waypoint = [pos_vec[0] + 1.0, pos_vec[1] + 1.0, rpy_vec[2]]
    return vlm_waypoint

register_combined_callback(vlm_callback)

vllm_main_process()



