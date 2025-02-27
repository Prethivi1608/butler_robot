import os
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Pose2D

class Movebase(Node):
    def __init__(self):
        super().__init__('move_robot')
        self.moveforward = self.create_publisher(Twist,'/cmd_vel',1)
        self.timer = self.create_timer(1,self.forward_callback)
       
        
    def forward_callback(self):
        self.speed =  Twist()
        self.speed.linear.x = 1.0
        self.speed.angular.z = 1.5 
        self.get_logger().info('Publishing to the topic. Robot Moving')
        self.moveforward.publish(self.speed)      
    


def main(): 
    rclpy.init()
    move_robot = Movebase()
    
    rclpy.spin(move_robot)
    move_robot.destroy_node()
    rclpy.shutdown()
    

if __name__ == "__main__":
    main()