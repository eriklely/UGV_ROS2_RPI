#!/usr/bin/env python
# encoding: utf-8
import sys, select, termios, tty
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState

msg = """
Control Your Car + Pan-Tilt!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%
t/T : x and y speed switch
s/S : stop keyboard control
space key, k : force stop

Pan-Tilt (Arrow keys):
   ↑ / ↓  : tilt up / down
   ← / →  : pan left / right
   p      : center camera

CTRL-C to quit
"""

moveBindings = {
    'i': (1, 0),
    'o': (1, -1),
    'j': (0, 1),
    'l': (0, -1),
    'u': (1, 1),
    ',': (-1, 0),
    '.': (-1, 1),
    'm': (-1, -1),
    'I': (1, 0),
    'O': (1, -1),
    'J': (0, 1),
    'L': (0, -1),
    'U': (1, 1),
    'M': (-1, -1),
}

speedBindings = {
    'Q': (1.1, 1.1),
    'Z': (.9, .9),
    'W': (1.1, 1),
    'X': (.9, 1),
    'E': (1, 1.1),
    'C': (1, .9),
    'q': (1.1, 1.1),
    'z': (.9, .9),
    'w': (1.1, 1),
    'x': (.9, 1),
    'e': (1, 1.1),
    'c': (1, .9),
}

class ugv_Keyboard(Node):
    def __init__(self, name):
        super().__init__(name)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 1)
        self.pt_pub = self.create_publisher(JointState, '/ugv/joint_commands', 10)

        self.declare_parameter("linear_speed_limit", 1.0)
        self.declare_parameter("angular_speed_limit", 1.0)

        self.linenar_speed_limit = self.get_parameter("linear_speed_limit").get_parameter_value().double_value
        self.angular_speed_limit = self.get_parameter("angular_speed_limit").get_parameter_value().double_value

        self.settings = termios.tcgetattr(sys.stdin)

        # Pan-tilt state
        self.pan = 0.0
        self.tilt = 0.0
        self.pt_step = 0.08

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
            # Handle arrow keys (they send 3 bytes)
            if key == '\x1b':
                key += sys.stdin.read(2)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def vels(self, speed, turn):
        return "currently:\tspeed %s\tturn %s " % (speed, turn)

    def publish_pt(self):
        msg = JointState()
        msg.name = ['pt_base_link_to_pt_link1', 'pt_link1_to_pt_link2']
        msg.position = [float(self.pan), float(self.tilt)]
        self.pt_pub.publish(msg)

def main():
    rclpy.init()
    ugv_keyboard = ugv_Keyboard("keyboard_ctrl")

    xspeed_switch = True
    (speed, turn) = (0.2, 0.5)
    (x, th) = (0, 0)
    status = 0
    stop = False
    count = 0
    twist = Twist()

    try:
        print(msg)
        print(ugv_keyboard.vels(speed, turn))

        while True:
            key = ugv_keyboard.getKey()

            # ---------- Pan-Tilt (Arrow keys + p) ----------
            if key == '\x1b[A':          # Up arrow
                ugv_keyboard.tilt += ugv_keyboard.pt_step
            elif key == '\x1b[B':        # Down arrow
                ugv_keyboard.tilt -= ugv_keyboard.pt_step
            elif key == '\x1b[D':        # Left arrow
                ugv_keyboard.pan -= ugv_keyboard.pt_step
            elif key == '\x1b[C':        # Right arrow
                ugv_keyboard.pan += ugv_keyboard.pt_step
            elif key == 'p' or key == 'P':
                ugv_keyboard.pan = 0.0
                ugv_keyboard.tilt = 0.0
                print("Camera centered")

            # Clamp values
            ugv_keyboard.pan = max(-3.0, min(3.0, ugv_keyboard.pan))
            ugv_keyboard.tilt = max(-0.7, min(1.4, ugv_keyboard.tilt))
            ugv_keyboard.publish_pt()

            # ---------- Original driving code ----------
            if key == "t" or key == "T":
                xspeed_switch = not xspeed_switch
            elif key == "s" or key == "S":
                print("stop keyboard control: {}".format(not stop))
                stop = not stop

            if key in moveBindings.keys():
                x = moveBindings[key][0]
                th = moveBindings[key][1]
                count = 0
            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn = turn * speedBindings[key][1]
                count = 0
                if speed > ugv_keyboard.linenar_speed_limit:
                    speed = ugv_keyboard.linenar_speed_limit
                    print("Linear speed limit reached!")
                if turn > ugv_keyboard.angular_speed_limit:
                    turn = ugv_keyboard.angular_speed_limit
                    print("Angular speed limit reached!")
                print(ugv_keyboard.vels(speed, turn))
                if status == 14:
                    print(msg)
                status = (status + 1) % 15
            elif key == ' ':
                (x, th) = (0, 0)
            else:
                count = count + 1
                if count > 4:
                    (x, th) = (0, 0)
                if key == '\x03':
                    break

            if xspeed_switch:
                twist.linear.x = speed * x
            else:
                twist.linear.y = speed * x
            twist.angular.z = turn * th

            if not stop:
                ugv_keyboard.pub.publish(twist)
            else:
                ugv_keyboard.pub.publish(Twist())

    except Exception as e:
        print(e)
    finally:
        ugv_keyboard.pub.publish(Twist())
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, ugv_keyboard.settings)
        ugv_keyboard.destroy_node()
        rclpy.shutdown()
