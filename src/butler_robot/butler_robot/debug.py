import os
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped, TransformStamped
import rclpy.time
from tf2_ros import TransformListener, Buffer 

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
        

class RobotPose(Node):
    def __init__(self):
        super().__init__('listener')
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer,self)
        self.timer = self.create_timer(1,self.robot_pose)
        
    def robot_pose(self):
        self.transform = TransformStamped()
        self.transform = self.buffer.lookup_transform('map','base_link',rclpy.time.Time())
        
        self.x = self.transform.transform.translation.x
        self.y = self.transform.transform.translation.y
        self.z = self.transform.transform.translation.z
        
        
        self.get_logger().info(f'Robot Position : x :{self.x},y: {self.y}, z:{self.z}')
        

class MovetoGoal(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        
        
        self.goal_pose = self.create_publisher(PoseStamped,'/goal_pose',10)
        self.timer = self.create_timer(200,self.send_goal())
        self.position = RobotPose()
    
    def send_goal(self):
        self.goal_msg = PoseStamped()
        self.goal_msg.header.frame_id = 'map'
        self.goal_msg.header.stamp = self.get_clock().now().to_msg()
        
        self.goal_msg.pose.position.x = -25.0746 
        self.goal_msg.pose.position.y = -11.4507
        self.goal_msg.pose.position.z = 0.00
        
        self.goal_msg.pose.orientation.w = 1.0
        
        self.goal_pose.publish(self.goal_msg)
        self.get_logger().info('Published goal')
        
        # self.get_logger().info(f'Robot Position : x :{self.position.x},y: {self.position.y}, z:{self.position.z}')
        
        
def main(): 
    rclpy.init()
    #move_robot = Movebase()

    
    go_to_goal = MovetoGoal()
    
    
    rclpy.spin(go_to_goal)
    go_to_goal.destroy_node()
    rclpy.shutdown()
    

if __name__ == "__main__":
    main()