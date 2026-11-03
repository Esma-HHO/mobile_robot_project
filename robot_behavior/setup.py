from setuptools import find_packages, setup

package_name = 'robot_behavior'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Esma',
    maintainer_email='esmah.2004@gmail.com',
    description='LiDAR based reactive obstacle avoidance for the mobile robot.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'obstacle_avoidance = robot_behavior.obstacle_avoidance:main',
        ],
    },
)
