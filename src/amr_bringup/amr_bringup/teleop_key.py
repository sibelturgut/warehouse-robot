import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray
from pynput import keyboard as kb

HELP = """
-- AMR Teleop --  hold keys to combine (e.g. W+A for arc)
  W / S      forward / back
  A / D      turn left / right
  SPACE      stop
  R          lift up
  F          lift down
  H          hold lift
  Q / ESC    quit
"""

class TeleopKey(Node):
    def __init__(self):
        super().__init__('teleop_key')
        self.cmd_pub  = self.create_publisher(Twist, '/cmd_vel', 10)
        self.lift_pub = self.create_publisher(
            Float64MultiArray, '/lift_position_controller/commands', 10)

        self.pressed = set()
        self.running = True
        self.create_timer(0.05, self.publish_cmd)  # 20 Hz

        self.listener = kb.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        try:
            ch = key.char
        except AttributeError:
            ch = None

        if ch == 'q' or key == kb.Key.esc:
            self.running = False
            return False

        if key == kb.Key.space:
            self.pressed.clear()
            return

        if ch:
            self.pressed.add(ch)
            if ch == 'r':
                self._pub_lift(200.0)
            elif ch == 'f':
                self._pub_lift(0.0)
            elif ch == 'h':
                self._pub_lift(39.2)

    def on_release(self, key):
        try:
            self.pressed.discard(key.char)
        except AttributeError:
            pass

    def _pub_lift(self, effort):
        msg = Float64MultiArray()
        msg.data = [effort]
        self.lift_pub.publish(msg)

    def publish_cmd(self):
        if not self.running:
            rclpy.shutdown()
            return
        msg = Twist()
        if 'w' in self.pressed:
            msg.linear.x =  0.3
        if 's' in self.pressed:
            msg.linear.x = -0.3
        if 'a' in self.pressed:
            msg.angular.z =  0.5
        if 'd' in self.pressed:
            msg.angular.z = -0.5
        self.cmd_pub.publish(msg)

def main():
    rclpy.init()
    node = TeleopKey()
    print(HELP)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()

if __name__ == '__main__':
    main()
