"""
Bridges vehicle gps information with msight ui

BACKEND_HOST=192.168.1.50 EGO_UDP_PORT=4002 python3 gps_bridge.py
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
