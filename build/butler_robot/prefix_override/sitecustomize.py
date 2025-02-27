import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/prethiviraj/ros2/workspaces/butler_robot/install/butler_robot'
