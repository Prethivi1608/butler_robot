import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import PoseStamped
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

        # Coordinates for the different positions
        self.home_x, self.home_y = 0.0, 0.0  # Home position (origin)
        self.kitchen_x, self.kitchen_y = -25.0746, -11.4507  # Kitchen position
        self.table1_x, self.table1_y = 22.0289, -20.9113  # Table1 position
        self.table2_x, self.table2_y = 14.6836, -20.8355  # Table2 position
        self.table3_x, self.table3_y = 19.0407, -4.63315  # Table3 position

        self.goal_x, self.goal_y = None, None
        self.is_order_cancelled = False
        self.confirmation_received = False

        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(1.0, self.check_status)

        self.get_logger().info("RobotMovement Node has started.")

        # Initialize the tf2 buffer and listener
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # GUI control variables
        self.gui_running = True
        self.goal_selected = False

        # Wait until the robot's pose is available
        self.wait_for_robot_pose()

    def wait_for_robot_pose(self):
        # Wait until we can get the transform from the map frame to the base_link (robot frame)
        while not self.get_robot_pose():
            self.get_logger().info("Waiting for robot pose data...")
            sleep(1)  # Sleep to prevent overloading the CPU while waiting

    def get_robot_pose(self):
        try:
            # Get the transform from 'map' to 'base_link'
            transform = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())

            # Extract the position (x, y) and orientation (quaternion)
            robot_position = transform.transform.translation
            robot_orientation = transform.transform.rotation

            # Convert quaternion to Euler angles
            (roll, pitch, yaw) = euler_from_quaternion(
                [robot_orientation.x, robot_orientation.y, robot_orientation.z, robot_orientation.w]
            )

            # Update the robot pose
            self.current_pose = robot_position
            self.current_yaw = yaw

            self.get_logger().info(f"Robot Pose: {self.current_pose.x}, {self.current_pose.y}, {self.current_yaw}")
            return True
        except Exception as e:
            self.get_logger().warn(f"Error getting robot pose: {str(e)}")
            return False

    def get_current_yaw(self):
        return self.current_yaw if hasattr(self, 'current_yaw') else 0.0

    def move_to_goal(self, x, y):
        twist = Twist()

        # Get the robot's current orientation (yaw)
        current_angle = self.get_current_yaw()

        # Calculate angle to the goal
        delta_x = x - self.current_pose.x
        delta_y = y - self.current_pose.y
        goal_angle = math.atan2(delta_y, delta_x)  # Angle to the goal

        # Calculate the difference in angles
        angle_diff = goal_angle - current_angle

        # Normalize the angle difference to [-pi, pi]
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        # Rotate the robot to face the goal
        twist.angular.z = 0.5 * angle_diff  # Adjust the rotation speed if needed

        # If the robot is facing the goal (angle difference is small), move forward
        if abs(angle_diff) < 0.1:
            twist.angular.z = 0.0  # Stop rotating
            twist.linear.x = 1.5  # Move forward

        self.cmd_vel_pub.publish(twist)

        # Wait until the robot moves forward
        distance_to_goal = math.sqrt(delta_x ** 2 + delta_y ** 2)
        while distance_to_goal > 0.1:  # Stop when the robot is near the goal
            self.cmd_vel_pub.publish(twist)
            # Update the distance to the goal
            delta_x = x - self.current_pose.x
            delta_y = y - self.current_pose.y
            distance_to_goal = math.sqrt(delta_x ** 2 + delta_y ** 2)
            sleep(0.1)  # Small delay to prevent fast looping
        
        # Stop the robot once it is close to the goal
        twist.linear.x = 0.0  # Stop moving forward
        twist.angular.z = 0.0  # Stop rotating
        self.cmd_vel_pub.publish(twist)

        self.get_logger().info(f"Robot has arrived at goal ({x}, {y})")

    def move_to_kitchen(self):
        self.move_to_goal(self.kitchen_x, self.kitchen_y)

    def move_to_home(self):
        self.move_to_goal(self.home_x, self.home_y)

    def confirm_delivery(self):
        if not self.gui_running or not self.goal_selected:
            return

        start_time = time.time()
        user_confirm = messagebox.askyesno("Confirmation", "Please confirm in Kitchen?")

        # Allow user 1 minute to confirm
        while time.time() - start_time < 60:
            if user_confirm:
                self.confirmation_received = True
                messagebox.showinfo("Delivery Status", "Order completed successfully.")
                return
            sleep(1)

        # If confirmation is not received within 60 seconds, return to home
        self.confirmation_received = False
        messagebox.showinfo("Delivery Status", "Order not completed. Returning to home.")
        self.move_to_home()  # Return to home if the delivery is not confirmed

    def set_goal(self, goal_name):
        if goal_name == "Table1":
            self.goal_x, self.goal_y = self.table1_x, self.table1_y
        elif goal_name == "Table2":
            self.goal_x, self.goal_y = self.table2_x, self.table2_y
        elif goal_name == "Table3":
            self.goal_x, self.goal_y = self.table3_x, self.table3_y
        else:
            messagebox.showerror("Invalid Goal", "Invalid goal selected.")
            return

        self.goal_selected = True
        self.move_to_kitchen()  # Move to kitchen first

        # Wait for 5 seconds before confirmation prompt
        sleep(5)

        # Intimate user to confirm within 1 minute
        self.confirm_delivery()

        # If confirmation is received, move to the selected goal
        if self.confirmation_received:
            self.move_to_goal(self.goal_x, self.goal_y)

    def cancel_order(self):
        self.is_order_cancelled = True
        self.get_logger().info("Order has been cancelled.")
        self.move_to_kitchen()  # Move to kitchen first
        self.move_to_home()  # Then return to home position
        messagebox.showinfo("Order Cancelled", "The order has been cancelled. The robot is returning to home.")

    def check_status(self):
        if self.is_order_cancelled:
            self.move_to_home()  # Ensure the robot returns home after cancellation
            self.is_order_cancelled = False  # Reset the cancellation flag

    def start_gui(self):
        def gui_thread():
            root = tk.Tk()
            root.title("Robot Goal Selection")

            tk.Label(root, text="Please select a goal destination:").pack(pady=10)

            button_table1 = tk.Button(root, text="Table1", command=lambda: self.set_goal("Table1"))
            button_table1.pack(pady=5)

            button_table2 = tk.Button(root, text="Table2", command=lambda: self.set_goal("Table2"))
            button_table2.pack(pady=5)

            button_table3 = tk.Button(root, text="Table3", command=lambda: self.set_goal("Table3"))
            button_table3.pack(pady=5)

            button_cancel = tk.Button(root, text="Cancel Order", command=self.cancel_order)
            button_cancel.pack(pady=5)

            tk.Button(root, text="Quit", command=root.quit).pack(pady=20)

            # Run the Tkinter event loop
            root.mainloop()

        # Start GUI in a separate thread so ROS and Tkinter can run concurrently
        gui_thread_instance = Thread(target=gui_thread)
        gui_thread_instance.start()


def main(args=None):
    rclpy.init(args=args)

    robot_movement = RobotMovement()

    # Start the GUI in the background
    robot_movement.start_gui()

    rclpy.spin(robot_movement)

    robot_movement.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
