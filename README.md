# G1 hand tracking and RViz visualization

This ROS 2 Humble project adapts the body-relative wrist tracking pipeline from the LabRoM Spot teleoperation work to a Unitree G1 model and a RealSense RGB-D camera. The current end-to-end scope is right-wrist tracking, a torso-relative target TF, and position-only right-arm inverse kinematics shown in RViz.

**This repository does not send commands to a physical G1.** The IK node publishes a private visualization joint-state topic for `robot_state_publisher`; it has no Unitree SDK/controller integration. Hand orientation and gesture nodes publish estimates, but they are not consumed by the arm IK or a gripper controller.

## What runs

`g1_wrist_realsense.launch.py` starts the RealSense driver (unless disabled), `wrist_detector`, `g1_arm_ik_node`, `robot_state_publisher`, RViz, and optional gesture/orientation estimators. The detector uses MediaPipe Pose right-wrist landmark 16, synchronized color and aligned depth, camera intrinsics, and a body frame estimated from pose landmarks. It publishes `/wrist_pose` and the `torso_link -> wrist_target` TF. The IK node follows that target with the seven right-arm joints and publishes all movable joints on `/g1_visualization/joint_states`; robot state publisher consumes this topic to provide the robot TF tree.

The transfer from a human arm to the robot arm is an approximate scaled mapping. The launch derives the robot shoulder location and a reach estimate from the chosen URDF, and sets the initial human-to-robot scale to `reach / 0.65 m`. The detector also has optional online arm-length estimation. These values need calibration for the operator, camera placement, and desired G1 workspace. Target coordinates are torso-relative; this is not a camera-frame-to-joint direct mapping.

## Run

The provided Docker setup expects the LabRoM base image `spot_ros2:latest` to exist locally. Build the image and launch the container using the repository's Docker configuration. With the ROS workspace sourced, the launch command is:

```bash
ros2 launch g1_teleop g1_wrist_realsense.launch.py
```

Choose the URDF variant that matches the actual G1 hardware. For example:

```bash
ros2 launch g1_teleop g1_wrist_realsense.launch.py model:=g1_29dof_rev_1_0.urdf
```

Other installed models are listed in `src/g1_teleop/urdf/`. `camera:=false` disables the camera driver, and `show_window:=false` disables the OpenCV preview. The launch defaults to `g1_29dof_rev_1_0.urdf`; the model must contain `torso_link`, `right_shoulder_pitch_joint`, and a seven-joint chain ending at `right_wrist_yaw_link`.

## Topics and frames

- Inputs: `/camera/camera/color/image_raw`, `/camera/camera/aligned_depth_to_color/image_raw`, `/camera/camera/color/camera_info`.
- Wrist target: `/wrist_pose` (`geometry_msgs/PoseStamped`, in `torso_link`).
- Target TF: `torso_link -> wrist_target`.
- Visualization joint states: `/g1_visualization/joint_states`.
- Arm target orientation is currently ignored by the position-only IK.

## Dependencies and verification

The package is built with `colcon` in ROS 2 Humble. The Dockerfile uses the `spot_ros2:latest` image and installs Python dependencies, including MediaPipe. Build with:

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select g1_teleop
```

The RealSense device and an X11-capable display are needed to verify the full live camera and RViz experience. `camera:=false` is useful for checking the robot visualization pipeline without a camera, but no physical arm control is implemented.
