import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('g1_teleop')
    urdf_file = os.path.join(pkg_share, 'urdf', 'g1_29dof.urdf')
    rviz_cfg = os.path.join(pkg_share, 'config', 'g1_wrist.rviz')

    color_topic = '/camera/camera/color/image_raw'
    depth_topic = '/camera/camera/aligned_depth_to_color/image_raw'
    info_topic = '/camera/camera/color/camera_info'

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    args = [
        DeclareLaunchArgument('camera', default_value='true', description='Launch RealSense camera node'),
        DeclareLaunchArgument('show_window', default_value='true', description='Show OpenCV window'),
        DeclareLaunchArgument('gestures', default_value='true', description='Launch gesture and orientation nodes'),
    ]

    realsense_launch = IncludeLaunchDescription(
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

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc}]
    )

    wrist_detector_node = Node(
        package='g1_teleop',
        executable='wrist_detector',
        name='wrist_detector',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'color_topic': color_topic,
            'depth_topic': depth_topic,
            'camera_info_topic': info_topic,
            'show_window': LaunchConfiguration('show_window'),
            'output_frame': 'torso_link',
            'robot_reach': 0.60,
            'shoulder_offset': [0.0, -0.17, 0.25],
        }]
    )

    ik_node = Node(
        package='g1_teleop',
        executable='g1_arm_ik_node',
        name='g1_arm_ik_node',
        output='screen'
    )

    orientation_node = Node(
        package='g1_teleop',
        executable='hand_orientation_estimator',
        name='hand_orientation_estimator',
        output='screen',
        parameters=[{'color_topic': color_topic}],
        condition=IfCondition(LaunchConfiguration('gestures'))
    )

    gestures_node = Node(
        package='g1_teleop',
        executable='hand_pose_estimator',
        name='hand_pose_estimator',
        output='screen',
        parameters=[{'color_topic': color_topic}],
        condition=IfCondition(LaunchConfiguration('gestures'))
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_cfg]
    )

    return LaunchDescription(args + [
        realsense_launch,
        robot_state_publisher_node,
        wrist_detector_node,
        ik_node,
        orientation_node,
        gestures_node,
        rviz_node
    ])
