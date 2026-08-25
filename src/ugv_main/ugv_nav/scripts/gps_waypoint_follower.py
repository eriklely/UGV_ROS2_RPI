#!/usr/bin/env python3
"""GPS waypoint follower node.

Reads waypoints from a YAML file (parameter: waypoints_file), converts each
lat/lon pair to a map-frame pose via the robot_localization fromLL service,
and sends sequential NavigateToPose action goals to Nav2.
"""

import sys

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup

import yaml

from nav2_msgs.action import NavigateToPose
from robot_localization.srv import FromLL
from geographic_msgs.msg import GeoPoint
from geometry_msgs.msg import PoseStamped


class GpsWaypointFollower(Node):

    def __init__(self):
        super().__init__('gps_waypoint_follower')

        self.declare_parameter('waypoints_file', '')
        waypoints_file = self.get_parameter('waypoints_file').get_parameter_value().string_value

        if not waypoints_file:
            self.get_logger().error('Parameter "waypoints_file" is not set. Exiting.')
            sys.exit(1)

        self._waypoints = self._load_waypoints(waypoints_file)
        self._cb_group = ReentrantCallbackGroup()

        self._from_ll_client = self.create_client(
            FromLL, '/fromLL', callback_group=self._cb_group
        )
        self._nav_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose', callback_group=self._cb_group
        )

    def _load_waypoints(self, path):
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            waypoints = data.get('waypoints', [])
            self.get_logger().info(f'Loaded {len(waypoints)} waypoint(s) from {path}')
            return waypoints
        except Exception as e:
            self.get_logger().error(f'Failed to load waypoints file "{path}": {e}')
            sys.exit(1)

    def run(self):
        self.get_logger().info('Waiting for /fromLL service...')
        if not self._from_ll_client.wait_for_service(timeout_sec=30.0):
            self.get_logger().error('/fromLL service not available after 30 s. Exiting.')
            return

        self.get_logger().info('Waiting for navigate_to_pose action server...')
        if not self._nav_client.wait_for_server(timeout_sec=30.0):
            self.get_logger().error('navigate_to_pose action server not available after 30 s. Exiting.')
            return

        for i, wp in enumerate(self._waypoints):
            name = wp.get('name', f'Waypoint_{i + 1}')
            lat = wp.get('latitude', 0.0)
            lon = wp.get('longitude', 0.0)

            self.get_logger().info(
                f'[{i + 1}/{len(self._waypoints)}] Navigating to "{name}" '
                f'(lat={lat}, lon={lon})'
            )

            map_pose = self._convert_ll_to_map(lat, lon)
            if map_pose is None:
                self.get_logger().warn(
                    f'Could not convert "{name}" to map frame. Skipping.'
                )
                continue

            success = self._navigate_to_pose(map_pose, name)
            if not success:
                self.get_logger().warn(
                    f'Navigation to "{name}" failed or was aborted. Continuing to next waypoint.'
                )
            else:
                self.get_logger().info(f'Reached "{name}".')

        self.get_logger().info('All waypoints processed.')

    def _convert_ll_to_map(self, latitude, longitude):
        req = FromLL.Request()
        req.ll_point = GeoPoint()
        req.ll_point.latitude = float(latitude)
        req.ll_point.longitude = float(longitude)
        req.ll_point.altitude = 0.0

        future = self._from_ll_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is None:
            self.get_logger().error('fromLL service call failed.')
            return None

        map_point = future.result().map_point

        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = map_point.x
        pose.pose.position.y = map_point.y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0

        return pose

    def _navigate_to_pose(self, pose_stamped, name):
        goal = NavigateToPose.Goal()
        goal.pose = pose_stamped

        future = self._nav_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().warn(f'Goal for "{name}" was rejected by Nav2.')
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        from action_msgs.msg import GoalStatus
        status = result_future.result().status
        return status == GoalStatus.STATUS_SUCCEEDED


def main(args=None):
    rclpy.init(args=args)
    node = GpsWaypointFollower()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
