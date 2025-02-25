from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'butler_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name,'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name,'model'), glob('model/*.xacro')),
        (os.path.join('share', package_name,'model'), glob('model/*.gazebo')),
        (os.path.join('share', package_name,'world'), glob('world/*.world')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='prethiviraj',
    maintainer_email='prethiviraj@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'goal_publisher = butler_robot.navigation:main',
            'bt = butler_robot.bt:main',
        ],
    },
)
