import os
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _setup(context):
    pkg = get_package_share_directory('g1_teleop')
    model = LaunchConfiguration('model').perform(context)
    urdf_file = os.path.join(pkg, 'urdf', model)
    root = ET.parse(urdf_file).getroot()
    by_name = {joint.get('name'): joint for joint in root.findall('joint')}
    shoulder = by_name.get('right_shoulder_pitch_joint')
    if shoulder is None:
        raise RuntimeError(f'{model} has no right_shoulder_pitch_joint')
    xyz = [float(v) for v in shoulder.find('origin').get('xyz', '0 0 0').split()]
    # Estimate reach from the translations along the arm chain in this exact URDF.
    child_joints = {j.find('child').get('link'): j for j in root.findall('joint') if j.find('child') is not None}
    current, offsets = 'right_wrist_yaw_link', []
    while current != 'torso_link':
        joint = child_joints.get(current)
        if joint is None:
            raise RuntimeError(f'{model} has no torso_link to right_wrist_yaw_link chain')
        child = joint.find('child').get('link')
        parent = joint.find('parent').get('link')
        if joint is not shoulder:
            pos = [float(v) for v in joint.find('origin').get('xyz', '0 0 0').split()]
            offsets.append(sum(v * v for v in pos) ** 0.5)
        current = parent
    reach = sum(offsets)
    if reach <= 0.0:
        raise RuntimeError('Could not derive nonzero arm reach from URDF')
    color_topic = '/camera/camera/color/image_raw'
    depth_topic = '/camera/camera/aligned_depth_to_color/image_raw'
    info_topic = '/camera/camera/color/camera_info'
    with open(urdf_file, 'r') as f:
        robot_desc = f.read()
    rviz_cfg = os.path.join(pkg, 'config', 'g1_wrist.rviz')
    realsense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')),
        launch_arguments={'align_depth.enable': 'true', 'rgb_camera.color_profile': '640x480x30',
                          'depth_module.depth_profile': '640x480x30', 'initial_reset': 'true'}.items(),
        condition=IfCondition(LaunchConfiguration('camera')))
    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher',
               name='robot_state_publisher', output='screen',
               parameters=[{'robot_description': robot_desc}],
               remappings=[('/joint_states', '/g1_visualization/joint_states')])
    detector = Node(package='g1_teleop', executable='wrist_detector', name='wrist_detector',
                    output='screen', emulate_tty=True,
                    parameters=[{'color_topic': color_topic, 'depth_topic': depth_topic,
                                 'camera_info_topic': info_topic,
                                 'show_window': LaunchConfiguration('show_window'),
                                 'output_frame': 'torso_link', 'robot_reach': reach,
                                 'scale_factor': reach / 0.65, 'shoulder_offset': xyz}])
    ik = Node(package='g1_teleop', executable='g1_arm_ik_node', name='g1_arm_ik_node',
              output='screen', parameters=[{'urdf_path': urdf_file, 'base_frame': 'torso_link'}])
    orientation = Node(package='g1_teleop', executable='hand_orientation_estimator',
                       name='hand_orientation_estimator', output='screen',
                       parameters=[{'color_topic': color_topic}],
                       condition=IfCondition(LaunchConfiguration('gestures')))
    gestures = Node(package='g1_teleop', executable='hand_pose_estimator', name='hand_pose_estimator',
                    output='screen', parameters=[{'color_topic': color_topic}],
                    condition=IfCondition(LaunchConfiguration('gestures')))
    rviz = Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
                arguments=['-d', rviz_cfg])
    return [realsense, rsp, detector, ik, orientation, gestures, rviz]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('model', default_value='g1_29dof_rev_1_0.urdf',
                              description='URDF filename from g1_teleop/urdf; select the variant matching your G1'),
        DeclareLaunchArgument('camera', default_value='true', description='Launch RealSense camera node'),
        DeclareLaunchArgument('show_window', default_value='true', description='Show OpenCV window'),
        DeclareLaunchArgument('gestures', default_value='true', description='Launch gesture and orientation nodes'),
        OpaqueFunction(function=_setup),
    ])
