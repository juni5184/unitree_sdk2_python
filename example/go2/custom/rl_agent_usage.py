from get_robot_state import RLAgentClient

def rl_agent_callback(robot_state):
    print("\n[RL Agent] Robot State:")
    print("Linear Velocity:", robot_state["linear_velocity"])
    print("Angular Velocity:", robot_state["angular_velocity"])
    print("Quaternion:", robot_state["quaternion"])
    print("RPY:", robot_state["rpy"])
    print("Yaw:", robot_state["rpy"][2])
    print("Joint Position:", robot_state["joint_pos"])
    print("Joint Velocity:", robot_state["joint_vel"])
    print("Waypoint:", robot_state["waypoint"])
    waypoint = robot_state["waypoint"]
    print("Received waypoint from VLM:", waypoint, "\n")
    # policy     
    # TODO: implement your policy here

    # action output
    target_joint_pos = [1.0] * 12
    target_joint_vel = [0.0] * 12
    cmd_vel = [0.5, 0.0, 0.0]

    return target_joint_pos, target_joint_vel, cmd_vel

if __name__ == "__main__":
    client = RLAgentClient()
    client.register_combined_callback(rl_agent_callback)
    client.run()