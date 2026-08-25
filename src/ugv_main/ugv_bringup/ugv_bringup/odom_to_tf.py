"""Odometry-to-TF bridge.

Subscribes to a nav_msgs/Odometry topic and re-publishes the pose as a
dynamic TF transform.  Used to bridge the global EKF output
(/odometry/global) into the TF tree as map→odom when GPS mode is active.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros


class OdomToTf(Node):

    def __init__(self):
        super().__init__('odometry_to_tf_node')

        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('child_frame_id', 'odom')

        self._frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        self._child_frame_id = (
            self.get_parameter('child_frame_id').get_parameter_value().string_value
        )

        self._broadcaster = tf2_ros.TransformBroadcaster(self)

        self._sub = self.create_subscription(
            Odometry,
            'odom',
            self._odom_cb,
            10,
        )

        self.get_logger().info(
            f'odometry_to_tf_node started: publishing {self._frame_id}→{self._child_frame_id} '
            f'TF from topic "{self._sub.topic_name}"'
        )

    def _odom_cb(self, msg: Odometry) -> None:
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = self._frame_id
        t.child_frame_id = self._child_frame_id
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self._broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
