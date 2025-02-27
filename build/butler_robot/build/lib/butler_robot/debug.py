import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

import rclpy
from rclpy.node import Node

class TFListener(Node):
    def __init__(self):
        super('tf_listener')
        self.tf_listener = self.create_subscription(TFListener, '/tf',10)
        self.timer = self.create_timer(1,self.listener_callback)
        
        print(self.tf_listener)
    


def main(): 
    tf = TFListener()
    
    rclpy.spin(tf)
    tf.destroy_node()
    rclpy.shutdown()
    

if __name__ == "__main__":
    main()