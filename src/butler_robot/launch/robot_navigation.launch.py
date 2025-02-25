
from launch import LaunchDescription

from launch_ros.actions import Node

def generate_launch_description():

    navigationNode = Node(
        package='butler_robot',
        executable='goal_publisher',
        name='navigation',
        output='screen',
        remappings=[('/cmd_vel','diff_cont/cmd_vel_unstamped')]
        
    )


    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(navigationNode)


    return launchDescriptionObject
