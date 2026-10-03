#!/usr/bin/env python3
"""
Spot-style wrist teleop visualization with RealSense (port of spot-teleop/dev
wrist_detector_zed.launch.py with sim:=false, plus Spot model in RViz).

  RealSense -> wrist_detector (body frame, no ArUco) -> TF body -> wrist_target
  spot_description (arm:=True) -> Spot model + body frame in RViz

Usage:
  ros2 launch g1_teleop spot_wrist_realsense.launch.py
  ros2 launch g1_teleop spot_wrist_realsense.launch.py show_window:=false
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('g1_teleop')
    rviz_cfg = os.path.join(share, 'config', 'spot_wrist.rviz')

    color = '/camera/camera/color/image_raw'
    depth = '/camera/camera/aligned_depth_to_color/image_raw'
    info = '/camera/camera/color/camera_info'

    args = [
        DeclareLaunchArgument('camera', default_value='true'),
        DeclareLaunchArgument('spot', default_value='true'),
        DeclareLaunchArgument('show_window', default_value='true'),
        DeclareLaunchArgument('gestures', default_value='true'),
    ]

    realsense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')),
        launch_arguments={
            'align_depth.enable': 'true',
            'rgb_camera.color_profile': '640x480x30',
            'depth_module.depth_profile': '640x480x30',
            'initial_reset': 'true',
        }.items(),
        condition=IfCondition(LaunchConfiguration('camera')),
    )

    spot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('spot_description'), 'launch', 'description.launch.py')),
        launch_arguments={'arm': 'True', 'gui': 'False', 'rviz': 'False'}.items(),
        condition=IfCondition(LaunchConfiguration('spot')),
    )

    wrist = Node(
        package='g1_teleop', executable='wrist_detector', name='wrist_detector',
        output='screen', emulate_tty=True,
        parameters=[{
            'color_topic': color, 'depth_topic': depth, 'camera_info_topic': info,
            'show_window': LaunchConfiguration('show_window'),
        }])

    orientation = Node(
        package='g1_teleop', executable='hand_orientation_estimator',
        name='hand_orientation_estimator', output='screen',
        parameters=[{'color_topic': color}],
        condition=IfCondition(LaunchConfiguration('gestures')))

    gestures = Node(
        package='g1_teleop', executable='hand_pose_estimator',
        name='hand_pose_estimator', output='screen',
        parameters=[{'color_topic': color}],
        condition=IfCondition(LaunchConfiguration('gestures')))

    rviz = Node(package='rviz2', executable='rviz2', name='rviz2',
                output='screen', arguments=['-d', rviz_cfg])

    return LaunchDescription(args + [realsense, spot, wrist, orientation, gestures, rviz])
