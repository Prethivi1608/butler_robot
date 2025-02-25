import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
import xacro

def main():

    robotXacroName = 'butler_robot' #name of the robot xacro name

    namePackage = 'butler_robot' #name of the package

    modelFileRelativePath = 'robot.xacro' #path of the mxacrofile

    worldFileRelativePath = 'cafe.world' #path of the worldfile

    pathModelFile = os.path.join(get_package_share_directory(namePackage),modelFileRelativePath)

    pathWorldFile = os.path.join(get_package_share_directory(namePackage),worldFileRelativePath)

    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('butler_robot'),
                         ('launch/navigation_launch.py'))),
    
    )

    print(bringup_launch)
    print(os.path.join(get_package_share_directory('butler_robot'),
                         ('launch/navigation_launch.py')))


if __name__ == "__main__":
    main()