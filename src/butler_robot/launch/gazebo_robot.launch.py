import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

import launch_ros
import launch

from launch_ros.actions import Node
import xacro

def generate_launch_description():
    
    robotXacroName = 'butler_robot' #name of the robot xacro name
    
    namePackage = 'butler_robot' #name of the package

    modelFileRelativePath = 'model/robot.xacro' #path of the mxacrofile

    worldFileRelativePath = 'world/french_cafe.world' #path of the worldfile

    pathModelFile = os.path.join(get_package_share_directory(namePackage),modelFileRelativePath)

    pathWorldFile = os.path.join(get_package_share_directory(namePackage),worldFileRelativePath)

    robotDescription = xacro.process_file(pathModelFile).toxml()

    gazebo_rosPackageLaunch = PythonLaunchDescriptionSource(
    PathJoinSubstitution([
        FindPackageShare('gazebo_ros'),
        'launch',
        'gazebo.launch.py'
    ])
)

    gazeboLaunch=IncludeLaunchDescription(gazebo_rosPackageLaunch,launch_arguments={'world': pathWorldFile}.items())

    spawnModelNode = Node(package='gazebo_ros',executable="spawn_entity.py", 
                          arguments=['-topic','robot_description','-entity',robotXacroName])
    

    nodeRobotStatePublisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robotDescription,
                     'use_sim_time':True}],
    )

    slam_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource([
        PathJoinSubstitution([FindPackageShare('butler_robot'),'launch','online_async_launch.py'])]),
        launch_arguments={
            
            'slam_params_file':PathJoinSubstitution([FindPackageShare('butler_robot'),'config','mapper_params_online_async.yaml']),'use_sim_time':'true'}.items()
        
        )

    bringup_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([
            FindPackageShare('butler_robot'),
            'launch',
            'navigation_launch.py'
        ])
    )
)
    rviz_Node = Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    output='screen',
    arguments=['-d',PathJoinSubstitution([
        FindPackageShare('butler_robot'), 'config', 'navigation_config.rviz'
    ])]
)
    
    Ui_Node = Node(
    package='butler_robot',
    executable='bt',
    name='bt',
    output='screen',

)


    static_transformNode = Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=["0", "0", "0", "0", "0", "0", "map", "base_footprint"],
            output="screen"
    )
    

    launchDescriptionObject = LaunchDescription()

    #launchDescriptionObject.add_action(static_transformNode)
    
    launchDescriptionObject.add_action(bringup_launch)
    
    launchDescriptionObject.add_action(rviz_Node)

    launchDescriptionObject.add_action(gazeboLaunch)

    launchDescriptionObject.add_action(spawnModelNode)

    launchDescriptionObject.add_action(nodeRobotStatePublisher)

    launchDescriptionObject.add_action(slam_launch)
    
    
    #launchDescriptionObject.add_action(Ui_Node)


    return launchDescriptionObject
