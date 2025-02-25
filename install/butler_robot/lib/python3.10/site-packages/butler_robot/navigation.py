import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Pose, Point, Twist
from std_msgs.msg import ColorRGBA
from nav_msgs.msg import OccupancyGrid
import math
import heapq
from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import TransformStamped

class MarkerPublisher(Node):
    def __init__(self, goal_x, goal_y):
        super().__init__('marker_publisher')
        
        self.marker_pub = self.create_publisher(MarkerArray, '/visualization_marker_array', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(1.0, self.publish_markers)
        self.map_subscriber = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10
        )
        
        # TF listener for getting the robot's current position
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        self.map_data = None
        self.get_logger().info("Marker Publisher Node has been started.")
        
        self.marker_array = MarkerArray()
        self.marker_id = 0
        self.spacing = 10.0
        self.origin = None
        self.resolution = None
        self.marker_positions = []
        
        self.unvisited = set()
        self.visited = set()
        self.path = set()
        
        self.start_x = 0.0
        self.start_y = 0.0
        
        self.get_initial_robot_position()
        
        # Goal position in terms of x and y
        self.goal_x = goal_x
        self.goal_y = goal_y

        self.start_index = None
        self.goal_index = None

        self.smoothened_path = []
    
    def get_initial_robot_position(self):
        try:
            transform = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            
            # Extract the robot's position (x, y)
            self.start_x = transform.transform.translation.x
            self.start_y = transform.transform.translation.y
            
            self.get_logger().info(f"Initial Position: x={self.start_x}, y={self.start_y}")
        except Exception as e:
            self.get_logger().error(f"Failed to get transform: {str(e)}")

    def map_callback(self, msg):
        self.map_data = msg
        self.origin = self.map_data.info.origin.position
        self.resolution = self.map_data.info.resolution
        self.get_logger().info("Received map data and origin.")
        
        # Convert start and goal (x, y) positions to indices
        self.get_robot_position()
        self.start_index = self.get_index_from_position(self.start_x, self.start_y)
        self.goal_index = self.get_index_from_position(self.goal_x, self.goal_y)

    def get_robot_position(self):
        try:
            transform: TransformStamped = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            
            # Extract the robot's position in the map frame
            self.start_x = transform.transform.translation.x
            self.start_y = transform.transform.translation.y
            
            self.get_logger().info(f"Robot's current position: ({self.start_x}, {self.start_y})")
            
        except Exception as e:
            self.get_logger().error(f"Could not get transform: {e}")

    def get_index_from_position(self, x, y):
        """
        Convert x, y coordinates to the corresponding index in the grid.
        """
        i = int((x - self.origin.x) / self.resolution / self.spacing)
        j = int((y - self.origin.y) / self.resolution / self.spacing)
        index = j * 120 + i
        return index

    def create_marker(self, marker_id, pose, size=0.15, color=ColorRGBA(r=1.0, g=0.0, b=0.0, a=1.0)):
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "markers"
        marker.id = marker_id
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose = pose
        marker.scale.x = size
        marker.scale.y = size
        marker.scale.z = size
        marker.color = color
        return marker
    
    def create_line_marker(self, marker_id, points, color=ColorRGBA(r=0.0, g=0.0, b=0.0, a=1.0)):
        line_marker = Marker()
        line_marker.header.frame_id = "map"
        line_marker.header.stamp = self.get_clock().now().to_msg()
        line_marker.ns = "lines"
        line_marker.id = marker_id
        line_marker.type = Marker.LINE_LIST
        line_marker.action = Marker.ADD
        line_marker.scale.x = 0.05
        line_marker.color = color
        
        for p1, p2 in zip(points[:-1], points[1:]):
            line_marker.points.append(p1)
            line_marker.points.append(p2)
        
        return line_marker
    
    def publish_markers(self):
        if not self.map_data or self.origin is None or self.resolution is None:
            self.get_logger().info("Waiting for map data and origin...")
            return
        
        self.marker_array.markers.clear()
        self.marker_positions.clear()
        self.unvisited.clear()
        
        marker_id = 0
        for i in range(120):
            for j in range(75):
                pose = Pose()
                pose.position.x = self.origin.x + i * self.spacing * self.resolution
                pose.position.y = self.origin.y + j * self.spacing * self.resolution
                pose.position.z = 0.0
                
                self.marker_positions.append(pose.position)
                self.unvisited.add(marker_id)
                
                if self.is_obstacle(i, j):
                    obstacle_marker = self.create_marker(marker_id, pose, size=0.2, color=ColorRGBA(r=0.0, g=0.0, b=0.0, a=1.0))
                    self.marker_array.markers.append(obstacle_marker)
                else:
                    marker = self.create_marker(marker_id, pose)
                    self.marker_array.markers.append(marker)
                
                marker_id += 1
        
        line_points = []
        for i in range(120):
            for j in range(75):
                if i < 119:
                    p1 = self.marker_array.markers[i * 75 + j].pose.position
                    p2 = self.marker_array.markers[(i + 1) * 75 + j].pose.position
                    line_points.append(p1)
                    line_points.append(p2)
                if j < 74:
                    p1 = self.marker_array.markers[i * 75 + j].pose.position
                    p2 = self.marker_array.markers[i * 75 + (j + 1)].pose.position
                    line_points.append(p1)
                    line_points.append(p2)
        
        line_marker = self.create_line_marker(marker_id, line_points)
        self.marker_array.markers.append(line_marker)
        
        self.a_star_algorithm()
        self.marker_pub.publish(self.marker_array)
        self.get_logger().info(f"Published {len(self.marker_array.markers)}")
    
    def is_obstacle(self, i, j):

        index = j * 120 + i
        if self.map_data.data[index] == 100:  # Obstacle
            return True
        return False
    
    def heuristic(self, pos1, pos2):
        return math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)
    
    def a_star_algorithm(self):
        open_set = [(0, self.start_index)]
        heapq.heapify(open_set)
        came_from = {}
        g_score = {index: float('inf') for index in self.unvisited}
        g_score[self.start_index] = 0
        f_score = {index: float('inf') for index in self.unvisited}
        f_score[self.start_index] = self.heuristic(self.marker_positions[self.start_index], self.marker_positions[self.goal_index])
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == self.goal_index:
                self.reconstruct_path(came_from)
                return
            
            self.unvisited.discard(current)
            self.visited.add(current)
            
            neighbors = [current - 1, current + 1, current - 75, current + 75]
            neighbors = [n for n in neighbors if n in self.unvisited and not self.is_obstacle(*self.get_coords_from_index(n))]
            
            for neighbor in neighbors:
                tentative_g_score = g_score[current] + self.heuristic(self.marker_positions[current], self.marker_positions[neighbor])
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self.heuristic(self.marker_positions[neighbor], self.marker_positions[self.goal_index])
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
    def get_coords_from_index(self, index):
        """
        Convert grid index to (i, j) coordinates.
        """
        i = index % 120
        j = index // 120
        return i, j
    
    def reconstruct_path(self, came_from):
        current = self.goal_index
        path_points = []
        while current in came_from:
            path_points.append(self.marker_positions[current])
            self.path.add(current)
            current = came_from[current]
        path_points.append(self.marker_positions[self.start_index])
        path_points.reverse()
        
        # Apply path smoothing
        self.smoothened_path = self.smooth_path(path_points)
        
        # Create and publish the smoothed path marker (highlighted in green)
        smoothened_path_marker = self.create_line_marker(9999, self.smoothened_path, ColorRGBA(r=0.0, g=1.0, b=0.0, a=1.0))
        self.marker_array.markers.append(smoothened_path_marker)

    def smooth_path(self, path_points):
        """
        Simple smoothing of the path by averaging adjacent points.
        """
        smoothened_path = [path_points[0]]  # Keep the start point
        
        for i in range(1, len(path_points) - 1):
            prev_point = path_points[i - 1]
            current_point = path_points[i]
            next_point = path_points[i + 1]
            
            # Averaging the points to smoothen the path
            smoothed_x = (prev_point.x + current_point.x + next_point.x) / 3.0
            smoothed_y = (prev_point.y + current_point.y + next_point.y) / 3.0
            smoothened_path.append(Point(x=smoothed_x, y=smoothed_y, z=0.0))
        
        smoothened_path.append(path_points[-1])  # Keep the goal point
        return smoothened_path

    def follow_path(self):
     
        if self.smoothened_path:
            for i in range(1, len(self.smoothened_path)):
                target_point = self.smoothened_path[i]
                current_position = self.get_robot_position()

                # Move towards the next point
                move_cmd = Twist()
                move_cmd.linear.x = target_point.x - current_position.x
                move_cmd.linear.y = target_point.y - current_position.y
                self.cmd_vel_pub.publish(move_cmd)
                
                self.get_logger().info(f"Moving to point: ({target_point.x}, {target_point.y})")

    def get_robot_position(self):
        try:
            transform: TransformStamped = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            
            # Extract the robot's position in the map frame
            return transform.transform.translation
            
        except Exception as e:
            self.get_logger().error(f"Could not get transform: {e}")
            return Point()

def main(args=None):
    rclpy.init(args=args)
    
    # Goal position in x, y coordinates
    goal_x, goal_y = -25.0746, -11.4507
    
    marker_publisher = MarkerPublisher(goal_x, goal_y)
    
    rclpy.spin(marker_publisher)
    marker_publisher.follow_path()  # Start following the smoothened path after path is constructed
    marker_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
