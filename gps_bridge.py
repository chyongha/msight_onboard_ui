"""
Bridges vehicle gps information with msight ui

Where sub_veh_ros2.py's callback writes a CSV row, this one's callback sends
the fix as UDP/JSON to msight_onboard_ui's backend, which relays it to the
frontend as an 'ego' Socket.IO event (see backend/udp_listener.py's
start_ego_listener - same shape as the existing ICA/RSA and tracking
listeners).

Still doesn't import backend/config.py, even though it's a sibling now -
this script needs to run on a real ROS2 environment to reach the actual
/ins/nav_sat_fix topic (almost certainly the vehicle's onboard computer),
which is very likely a *different machine* than wherever the Flask backend
itself runs - config.py's own defaults (e.g. BACKEND_HOST defaulting to
127.0.0.1) are written from the backend's own point of view, not this
script's. Point it at the real backend with env vars instead:

    BACKEND_HOST=192.168.1.50 EGO_UDP_PORT=4002 python3 gps_bridge.py

mock_sender.py's ego_loop() and mock_sender_gps_tests.py send the exact
same {lat, lon, timestamp} JSON to the same port - testing against those
(no ROS2/vehicle needed) exercises the identical backend+frontend code path
this script feeds for real.
"""
import json
import os
import socket

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix

BACKEND_HOST = os.environ.get('BACKEND_HOST', '127.0.0.1')
EGO_UDP_PORT = int(os.environ.get('EGO_UDP_PORT', '4002'))


class GpsBridge:
    def __init__(self, parent_node: Node):
        self.node = parent_node
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (BACKEND_HOST, EGO_UDP_PORT)

        # identical subscription mechanism to sub_veh_ros2.py's proven one
        self.node.create_subscription(
            NavSatFix,
            '/ins/nav_sat_fix',
            self._on_fix,
            10
        )
        self.node.get_logger().info(f'Forwarding GPS fixes to {BACKEND_HOST}:{EGO_UDP_PORT}')

    def _on_fix(self, msg):
        timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        payload = {
            'lat': msg.latitude,
            'lon': msg.longitude,
            'timestamp': timestamp,
        }
        self.sock.sendto(json.dumps(payload).encode('utf-8'), self.target)

    def close(self):
        self.sock.close()


def main(args=None):
    rclpy.init(args=args)
    node = Node('gps_bridge_node')
    bridge = GpsBridge(node)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
