import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from tf2_ros import Buffer, TransformListener
import math
from tf_transformations import euler_from_quaternion
import time
import tkinter as tk
from tkinter import messagebox
from threading import Thread
from time import sleep

class RobotMovement(Node):
    def __init__(self):
        super().__init__('robot_movement')

        # Positions of destinations (home will be set dynamically)
        self.kitchen_x, self.kitchen_y = -25.0746, -11.4507
        self.table1_x, self.table1_y = 22.0289, -20.9113
        self.table2_x, self.table2_y = 14.6836, -20.8355
        self.table3_x, self.table3_y = 19.0407, -4.63315

        self.goal_x, self.goal_y = None, None
        self.is_order_cancelled = False
        self.confirmation_received = False

        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(1.0, self.check_status)

        self.get_logger().info("RobotMovement Node has started.")

        # Initialize tf2 for transform lookup
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # IMU Subscriber
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        self.current_yaw = 0.0

        # Wait for initial robot pose and dynamically set home position
        self.current_x, self.current_y = 0.0, 0.0
        self.wait_for_robot_pose()

    def imu_callback(self, msg):
        orientation = msg.orientation
        (_, _, yaw) = euler_from_quaternion([orientation.x, orientation.y, orientation.z, orientation.w])
        self.current_yaw = yaw  # Update robot's yaw angle
    
    def wait_for_robot_pose(self):
        while not self.get_robot_pose():
            self.get_logger().info("Waiting for robot pose data...")
            sleep(1)

        # Dynamically set home position from first retrieved pose
        self.home_x, self.home_y = self.current_x, self.current_y
        self.get_logger().info(f"Home position set dynamically: ({self.home_x}, {self.home_y})")

    def get_robot_pose(self):
        try:
            transform = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            self.current_x = transform.transform.translation.x
            self.current_y = transform.transform.translation.y
            self.get_logger().info(f"Robot Pose: {self.current_x}, {self.current_y}, {self.current_yaw}")
            return True
        except Exception as e:
            self.get_logger().warn(f"Error getting robot pose: {str(e)}")
            return False

    def move_to_goal(self, x, y):
        while self.get_robot_pose():  # Continuously update position
            delta_x = x - self.current_x
            delta_y = y - self.current_y
            goal_angle = math.atan2(delta_y, delta_x)
            angle_diff = goal_angle - self.current_yaw
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

            twist = Twist()
            twist.angular.z = 0.5 * angle_diff
            if abs(angle_diff) < 0.1:
                twist.angular.z = 0.0
                twist.linear.x = 1.5

            self.cmd_vel_pub.publish(twist)

            distance_to_goal = math.sqrt(delta_x ** 2 + delta_y ** 2)
            if distance_to_goal < 0.1:
                break
            sleep(0.1)

        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)
        self.get_logger().info(f"Robot has arrived at goal ({x}, {y})")

    def move_to_kitchen(self):
        self.move_to_goal(self.kitchen_x, self.kitchen_y)

    def move_to_home(self):
        self.move_to_goal(self.home_x, self.home_y)

    def confirm_delivery(self):
        start_time = time.time()
        user_confirm = messagebox.askyesno("Confirmation", "Please confirm in Kitchen?")

        while time.time() - start_time < 60:
            if user_confirm:
                self.confirmation_received = True
                messagebox.showinfo("Delivery Status", "Order completed successfully.")
                return
            sleep(1)

        self.confirmation_received = False
        messagebox.showinfo("Delivery Status", "Order not completed. Returning to home.")
        self.move_to_home()

    def set_goal(self, goal_name):
        goals = {"Table1": (self.table1_x, self.table1_y),
                 "Table2": (self.table2_x, self.table2_y),
                 "Table3": (self.table3_x, self.table3_y)}

        if goal_name not in goals:
            messagebox.showerror("Invalid Goal", "Invalid goal selected.")
            return

        self.goal_x, self.goal_y = goals[goal_name]
        self.move_to_kitchen()
        sleep(5)
        self.confirm_delivery()

        if self.confirmation_received:
            self.move_to_goal(self.goal_x, self.goal_y)

    def cancel_order(self):
        self.is_order_cancelled = True
        self.get_logger().info("Order has been cancelled.")
        self.move_to_kitchen()
        self.move_to_home()
        messagebox.showinfo("Order Cancelled", "The order has been cancelled. Returning to home.")

    def check_status(self):
        if self.is_order_cancelled:
            self.move_to_home()
            self.is_order_cancelled = False

    def start_gui(self):
        def gui_thread():
            root = tk.Tk()
            root.title("Robot Goal Selection")
            tk.Label(root, text="Please select a goal destination:").pack(pady=10)
            tk.Button(root, text="Table1", command=lambda: self.set_goal("Table1")).pack(pady=5)
            tk.Button(root, text="Table2", command=lambda: self.set_goal("Table2")).pack(pady=5)
            tk.Button(root, text="Table3", command=lambda: self.set_goal("Table3")).pack(pady=5)
            tk.Button(root, text="Cancel Order", command=self.cancel_order).pack(pady=5)
            tk.Button(root, text="Quit", command=root.quit).pack(pady=20)
            root.mainloop()
        Thread(target=gui_thread).start()


def main(args=None):
    rclpy.init(args=args)
    robot_movement = RobotMovement()
    robot_movement.start_gui()
    rclpy.spin(robot_movement)
    robot_movement.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
