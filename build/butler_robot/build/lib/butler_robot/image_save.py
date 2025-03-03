import cv2
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
import time

from sensor_msgs.msg import Image


class CameraSubscriber(Node):
    def __init__(self):
        super().__init__('camera_subscriber')
        
        self.bridge = CvBridge()
        
        
        
        self.topicname = '/camera/image_raw'
        
        self.queue = 10
        
        self.cam_sub = self.create_subscription(Image,self.topicname,self.camera_callback,self.queue)
        
    
    def camera_callback(self,Imagemsg):
        
        num_img = 1000
        
        path = '/home/prethiviraj/ros2/workspaces/butler_robot/camera_images/'
        
        
        for i in range(num_img):
            image = self.bridge.imgmsg_to_cv2(Imagemsg)
            filename = f"{path}image_{i}.jpg"
            cv2.imwrite(filename,image)
            self.get_logger().info(f'Saved {i} images')
            time.sleep(0.1)
        rclpy.shutdown()
            
        
def main():
    rclpy.init()
    
    camera_subscriber = CameraSubscriber()
    
    rclpy.spin(camera_subscriber)
    
    camera_subscriber.destroy_node()
    
    rclpy.shutdown()
    
if __name__ == '__main__':
    main()
    
            
        
        
        
        
        