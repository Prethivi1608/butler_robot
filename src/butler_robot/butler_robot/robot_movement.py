import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class RobotMovement(Node):
    def __init__(self):
        super().__init__('move_robot')
        self.velocity_pub = self.create_publisher(Twist,'/cmd_vel',10)
        self.timer = self.create_timer(0.5,self.velocity_callback)
    
    def velocity_callback(self):
        self.msg = Twist()
        self.msg.linear.x = 0.0
        self.msg.angular.z = 0.0

        self.velocity_pub.publish(self.msg)
        self.get_logger().info(f'Publishing: Linear={self.msg.linear.x}, Angular={self.msg.angular.z}')

def main():
    rclpy.init()
    move_node = RobotMovement()
    rclpy.spin(move_node)
    move_node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()




