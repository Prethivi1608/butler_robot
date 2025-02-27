import os
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped, TransformStamped
import rclpy.time
from tf2_ros import TransformListener, Buffer 
import tkinter as tk
from threading import Thread
import time
from tkinter import messagebox
from time import sleep

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
        
    
        

class Butler_Robot(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        
        self.kitchen_x = -28.4204 
        self.kitchen_y = -0.051482
        self.table1_x = 17.0289
        self.table1_y = 17.9113
        self.table2_x = 10.6836
        self.table2_y = -13.8355
        self.table3_x = 17.0407
        self.table3_y = -3.63315
        self.home_x = 0
        self.home_y = 0
        
        self.is_order_cancelled = False
        self.confirmation_received = False
        
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer,self)
        self.timer = self.create_timer(1,self.robot_pose)
        
        
        self.goal_pose = self.create_publisher(PoseStamped,'/goal_pose',10)
        # self.timer = self.create_timer(200,self.send_goal())
        
    
        
    def robot_pose(self):
        self.transform = TransformStamped()
        self.transform = self.buffer.lookup_transform('map','base_link',rclpy.time.Time())
        
        self.current_x = self.transform.transform.translation.x
        self.current_y = self.transform.transform.translation.y
        self.current_z = self.transform.transform.translation.z
        
        
        self.get_logger().info(f'Robot Position : x :{self.current_x},y: {self.current_y}, z:{self.current_z}')
        
    
    def send_goal(self,goal_x,goal_y):
        self.goal_msg = PoseStamped()
        self.goal_msg.header.frame_id = 'map'
        self.goal_msg.header.stamp = self.get_clock().now().to_msg()
        self.goal_x = goal_x
        self.goal_y = goal_y
        
        
        self.goal_msg.pose.position.x = self.goal_x
        self.goal_msg.pose.position.y = self.goal_y
        
        
        self.goal_pose.publish(self.goal_msg)
        self.get_logger().info('Published goal')
        
        
    def start_gui(self):
        def gui_thread():
            root = tk.Tk()
            root.title("Robot Goal Selection")
            tk.Label(root, text="Please select a goal destination:").pack(pady=10)
            tk.Button(root, text="Table1", command=self.move_to_table1).pack(pady=5)
            tk.Button(root, text="Table2", command=self.move_to_table2).pack(pady=5)
            tk.Button(root, text="Table3", command=self.move_to_table3).pack(pady=5)
            tk.Button(root, text="Cancel Order", command=self.cancel_order).pack(pady=5)
            tk.Button(root, text="Quit", command=root.quit).pack(pady=20)
            root.mainloop()
        Thread(target=gui_thread).start()
            
    def move_to_table1(self):
        self.get_logger().info('Moving to Table1.')
        self.move_to_kitchen()
        if self.has_reached_goal(self.kitchen_x, self.kitchen_y):
            self.confirm_delivery()
        if self.confirmation_received == True:
            self.send_goal(self.table1_x, self.table1_y)
            if self.has_reached_goal(self.table1_x, self.table1_y) == True:
                self.get_logger().info('Goal has been reached.')
                self.move_to_home()
    
    
    def move_to_table2(self):
        self.move_to_kitchen()
        if self.has_reached_goal(self.kitchen_x, self.kitchen_y):
            self.confirm_delivery()
        if self.confirmation_received == True:
            self.send_goal(self.table2_x, self.table2_y)
            if self.has_reached_goal(self.table2_x, self.table2_y) == True:
                self.get_logger().info('Goal has been reached.')
                self.move_to_home()
        
    def move_to_table3(self):
        self.move_to_kitchen()
        if self.has_reached_goal(self.kitchen_x, self.kitchen_y):
            self.confirm_delivery()
        if self.confirmation_received == True:
            self.send_goal(self.table3_x, self.table3_y)
            if self.has_reached_goal(self.table3_x, self.table3_y) == True:
                self.get_logger().info('Goal has been reached.')
                self.move_to_home()
        

    def has_reached_goal(self, reach_x,reach_y):
        distance_to_x = reach_x - self.current_x
        distance_to_y = reach_y - self.current_y
        
        if distance_to_x and distance_to_y < 5:
            return True

    
    def move_to_kitchen(self):
        self.send_goal(self.kitchen_x, self.kitchen_y)

    def move_to_home(self):
        self.send_goal(self.home_x, self.home_y)
    
    def cancel_order(self):
        self.is_order_cancelled = True
        self.get_logger().info("Order has been cancelled.")
        self.move_to_kitchen()
        self.move_to_home()
        messagebox.showinfo("Order Cancelled", "The order has been cancelled. Returning to home.")

        
    def confirm_delivery(self):
        start_time = time.time()
        user_confirm = messagebox.askyesno("Confirmation", "Please confirm in Kitchen?")

        while time.time() - start_time < 60:
            if user_confirm:
                self.confirmation_received = True
                messagebox.showinfo("Going to the Table")
                return
            sleep(1)

        self.confirmation_received = False
        messagebox.showinfo("Delivery Status", "Order not completed. Returning to home.")
        self.move_to_home()
        
        
        
def main(): 
    rclpy.init()
    #move_robot = Movebase()

    
    go_to_goal = Butler_Robot()
    go_to_goal.start_gui()
    
    rclpy.spin(go_to_goal)
    go_to_goal.destroy_node()
    rclpy.shutdown()
    

if __name__ == "__main__":
    main()
    
    