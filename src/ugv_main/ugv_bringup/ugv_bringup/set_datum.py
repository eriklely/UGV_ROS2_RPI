#!/usr/bin/env python3
"""set_datum.py — Optional helper utility to pre-set the navsat_transform_node datum.

Usage
-----
Run this script AFTER bringup_imu_ekf.launch.py with use_gps:=true is active.
It calls the /navsat_transform_node/set_datum service to lock the map-frame
origin to a known lat/lon/altitude when you explicitly want a fixed datum,
which is useful when:

  - You want repeatable map-frame coordinates across multiple runs.
  - Your robot starts indoors or in a GPS-denied area and you want to prime
    the datum before moving to an open area.
  - You are running a fleet of robots that must share the same map origin.

Quick start
-----------
  # Use a built-in named location:
  ros2 run ugv_bringup set_datum --location wavecrest_lab

  # Provide coordinates directly:
  ros2 run ugv_bringup set_datum --lat 52.3676 --lon 4.9041 --alt 0.0

  # Print available named locations:
  ros2 run ugv_bringup set_datum --list

Datum / service workflow
------------------------
1. Start the localization stack:
     ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true

2. Wait for navsat_transform_node to initialise (watch /odometry/gps topic).

3. Optionally call this script to lock the datum to a known origin:
     ros2 run ugv_bringup set_datum --lat 52.3676 --lon 4.9041

4. Verify the map origin:
     ros2 topic echo /odometry/global --once

After a successful call the map frame origin is fixed at the supplied
coordinates.  Subsequent GPS fixes will be expressed relative to this origin,
giving stable, reproducible map-frame positions across power cycles (as long
as you call set_datum at the same location each time).

Note: The default GPS startup path no longer depends on this service call.
      This utility remains available when you want repeatable coordinates
      across power cycles or a manually chosen map origin.
"""

import argparse
import sys

import rclpy
from rclpy.node import Node
from robot_localization.srv import SetDatum
from geographic_msgs.msg import GeoPose
from geometry_msgs.msg import Quaternion


# ---------------------------------------------------------------------------
# Reference datums for common UGV ROVER / BEAST operating locations.
# Add your own locations here using the format:
#   'location_key': (latitude_deg, longitude_deg, altitude_m, 'description')
# ---------------------------------------------------------------------------
KNOWN_LOCATIONS = {
    'wavecrest_lab': (
        52.3676, 4.9041, 0.0,
        'Wavecrest Lab, Amsterdam, Netherlands (example)'
    ),
    'tu_delft_campus': (
        51.9985, 4.3736, 0.0,
        'TU Delft main campus entrance, Delft, Netherlands (example)'
    ),
    'stanford_oval': (
        37.4348, -122.1720, 20.0,
        'Stanford Oval, Stanford CA, USA (example)'
    ),
    'mit_killian_court': (
        42.3601, -71.0942, 5.0,
        'MIT Killian Court, Cambridge MA, USA (example)'
    ),
    'eth_zentrum': (
        47.3769, 8.5417, 400.0,
        'ETH Zurich Zentrum, Switzerland (example)'
    ),
}


class DatumSetter(Node):
    """ROS 2 node that calls /navsat_transform_node/set_datum once and exits."""

    def __init__(self, lat: float, lon: float, alt: float):
        super().__init__('set_datum_client')
        self._lat = lat
        self._lon = lon
        self._alt = alt

    def call(self) -> bool:
        client = self.create_client(SetDatum, '/navsat_transform_node/set_datum')
        self.get_logger().info('Waiting for /navsat_transform_node/set_datum service…')

        if not client.wait_for_service(timeout_sec=10.0):
            self.get_logger().error(
                'Service not available after 10 s. '
                'Is bringup_imu_ekf.launch.py running with use_gps:=true?'
            )
            return False

        request = SetDatum.Request()
        geo_pose = GeoPose()
        geo_pose.position.latitude = self._lat
        geo_pose.position.longitude = self._lon
        geo_pose.position.altitude = self._alt
        # Identity quaternion — heading is handled by navsat_transform_node
        geo_pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        request.geo_pose = geo_pose

        self.get_logger().info(
            f'Setting datum: lat={self._lat:.6f}°, lon={self._lon:.6f}°, '
            f'alt={self._alt:.1f} m'
        )
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

        if future.result() is not None:
            self.get_logger().info('Datum set successfully.')
            return True
        else:
            self.get_logger().error(f'Service call failed: {future.exception()}')
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Set the navsat_transform_node datum via service call.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--location', metavar='NAME',
                       help='Use a named reference location (see --list).')
    group.add_argument('--lat', type=float, metavar='DEG',
                       help='Latitude in decimal degrees.')
    parser.add_argument('--lon', type=float, metavar='DEG',
                        help='Longitude in decimal degrees (required with --lat).')
    parser.add_argument('--alt', type=float, metavar='M', default=0.0,
                        help='Altitude in metres above WGS-84 ellipsoid (default: 0.0).')
    parser.add_argument('--list', action='store_true',
                        help='List available named locations and exit.')
    args = parser.parse_args()

    if args.list:
        print('Available named locations:')
        for key, (lat, lon, alt, desc) in KNOWN_LOCATIONS.items():
            print(f'  {key:25s}  lat={lat:.4f}  lon={lon:.4f}  alt={alt:.1f}  # {desc}')
        sys.exit(0)

    if args.location:
        if args.location not in KNOWN_LOCATIONS:
            print(f'Unknown location "{args.location}". Use --list to see options.',
                  file=sys.stderr)
            sys.exit(1)
        lat, lon, alt, _ = KNOWN_LOCATIONS[args.location]
    elif args.lat is not None:
        if args.lon is None:
            parser.error('--lon is required when --lat is provided.')
        lat, lon, alt = args.lat, args.lon, args.alt
    else:
        parser.print_help()
        sys.exit(1)

    rclpy.init()
    node = DatumSetter(lat, lon, alt)
    success = node.call()
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
