#!/usr/bin/env python3
"""
ROS 2 Inverse Kinematics (IK) Node for Unitree G1 Right Arm.
Subscribes to target wrist pose (/wrist_pose) and solves 7-DoF IK in real-time (30 Hz).
Publishes solved joint positions to /joint_states so RViz2 updates the G1 robot arm!

Subscribed Topics:
    /wrist_pose (geometry_msgs/PoseStamped): Target hand wrist pose

Published Topics:
    /joint_states (sensor_msgs/JointState): G1 joint positions for RViz2
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
import numpy as np
import scipy.optimize as opt


def rpy_to_R(roll, pitch, yaw):
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def make_tf(xyz, rpy):
    T = np.eye(4)
    T[:3, :3] = rpy_to_R(*rpy)
    T[:3, 3] = xyz
    return T


def joint_tf(axis, q):
    T = np.eye(4)
    if axis == 'x':
        T[:3, :3] = rpy_to_R(q, 0, 0)
    elif axis == 'y':
        T[:3, :3] = rpy_to_R(0, q, 0)
    elif axis == 'z':
        T[:3, :3] = rpy_to_R(0, 0, q)
    return T


class G1ArmIKNode(Node):
    def __init__(self):
        super().__init__('g1_arm_ik_node')

        # Joint Names for G1 Right Arm (7-DoF)
        self.joint_names = [
            'right_shoulder_pitch_joint',
            'right_shoulder_roll_joint',
            'right_shoulder_yaw_joint',
            'right_elbow_joint',
            'right_wrist_roll_joint',
            'right_wrist_pitch_joint',
            'right_wrist_yaw_joint'
        ]

        # Kinematic Chain Transforms (from URDF)
        self.T_orig = [
            make_tf([0.0039563, -0.10021, 0.23778], [-0.27931, 5.4949e-5, 0.00019159]),
            make_tf([0, -0.038, -0.013831], [0.27925, 0, 0]),
            make_tf([0, -0.00624, -0.1032], [0, 0, 0]),
            make_tf([0.015783, 0, -0.080518], [0, 0, 0]),
            make_tf([0.100, -0.00188791, -0.010], [0, 0, 0]),
            make_tf([0.038, 0, 0], [0, 0, 0]),
            make_tf([0.046, 0, 0], [0, 0, 0])
        ]
        self.axes = ['y', 'x', 'z', 'y', 'x', 'y', 'z']
        self.bounds = [
            (-3.0892, 2.6704),
            (-2.2515, 1.5882),
            (-2.618, 2.618),
            (-1.0472, 2.0944),
            (-1.9722, 1.9722),
            (-1.6144, 1.6144),
            (-1.6144, 1.6144)
        ]

        self.current_q = np.zeros(7)

        # Subscribers & Publishers
        self.target_sub = self.create_subscription(
            PoseStamped,
            '/wrist_pose',
            self.target_callback,
            10
        )
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)

        self.get_logger().info('G1 Arm IK Node Started! Solving 7-DoF IK for RViz2...')

    def forward_kinematics(self, q):
        T = np.eye(4)
        for i in range(7):
            T = T @ self.T_orig[i] @ joint_tf(self.axes[i], q[i])
        return T[:3, 3]

    def target_callback(self, msg: PoseStamped):
        target_p = np.array([
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z
        ])

        def cost_fn(q):
            p = self.forward_kinematics(q)
            # Position error + joint regularization (smoothness)
            return np.sum((p - target_p)**2) + 0.001 * np.sum((q - self.current_q)**2)

        res = opt.minimize(
            cost_fn,
            self.current_q,
            bounds=self.bounds,
            method='L-BFGS-B',
            options={'maxiter': 25}
        )

        if res.success:
            self.current_q = res.x

            js = JointState()
            js.header.stamp = self.get_clock().now().to_msg()
            js.name = self.joint_names
            js.position = list(self.current_q)
            self.joint_pub.publish(js)


def main(args=None):
    rclpy.init(args=args)
    node = G1ArmIKNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
