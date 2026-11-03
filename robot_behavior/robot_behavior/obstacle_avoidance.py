"""Reactive LiDAR obstacle avoidance for the project robot."""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class ObstacleAvoidance(Node):
    """Drive forward when clear; turn toward the side with more clearance."""

    def __init__(self):
        super().__init__('obstacle_avoidance')
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('stop_distance', 0.90)
        self.declare_parameter('clear_distance', 1.20)
        self.declare_parameter('front_half_angle', 0.80)
        self.declare_parameter('forward_speed', 0.20)
        self.declare_parameter('turn_speed', 0.55)
        self.declare_parameter('scan_timeout', 0.5)
        # The test course runs along world +X; angles are in radians.
        self.declare_parameter('course_heading', 0.0)
        self.declare_parameter('heading_gain', 0.8)
        self.declare_parameter('max_course_deviation', math.pi / 2)

        self.stop_distance = float(self.get_parameter('stop_distance').value)
        self.clear_distance = float(self.get_parameter('clear_distance').value)
        self.front_half_angle = float(self.get_parameter('front_half_angle').value)
        self.forward_speed = float(self.get_parameter('forward_speed').value)
        self.turn_speed = float(self.get_parameter('turn_speed').value)
        self.scan_timeout = float(self.get_parameter('scan_timeout').value)
        self.course_heading = float(
            self.get_parameter('course_heading').value)
        self.heading_gain = float(self.get_parameter('heading_gain').value)
        self.max_course_deviation = float(
            self.get_parameter('max_course_deviation').value)
        self.last_scan_time = None
        self.turning = False
        self.turn_direction = 0.0
        self.turn_direction_switched = False
        self.current_yaw = None
        self.status_log_period = 0.5
        self.last_status_time = 0.0
        self.last_logged_mode = None
        self.latest_front = None
        self.latest_left = None
        self.latest_right = None
        self.latest_course_error = 0.0
        self.last_warning = None

        self.cmd_pub = self.create_publisher(
            Twist, self.get_parameter('cmd_vel_topic').value, 10)
        self.scan_sub = self.create_subscription(
            LaserScan,
            self.get_parameter('scan_topic').value,
            self.scan_callback,
            qos_profile_sensor_data,
        )
        self.odom_sub = self.create_subscription(
            Odometry,
            self.get_parameter('odom_topic').value,
            self.odom_callback,
            10,
        )
        # A lost/stalled scan stream must not leave the last forward command active.
        self.watchdog = self.create_timer(0.1, self.scan_watchdog)
        self.get_logger().info('Obstacle avoidance ready; waiting for /scan')

    @staticmethod
    def _angle_in_sector(angle, lower, upper):
        angle = math.atan2(math.sin(angle), math.cos(angle))
        return lower <= angle <= upper

    @staticmethod
    def _yaw_from_quaternion(q):
        return math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )

    def odom_callback(self, odom):
        self.current_yaw = self._yaw_from_quaternion(
            odom.pose.pose.orientation)

    def _course_error(self):
        return math.atan2(
            math.sin(self.course_heading - self.current_yaw),
            math.cos(self.course_heading - self.current_yaw),
        )

    @staticmethod
    def _valid_distance(value, range_min, range_max):
        # Positive infinity is the LaserScan convention for no return within range.
        if math.isinf(value) and value > 0:
            return range_max
        if not math.isfinite(value) or value < 0:
            return None
        return min(range_max, max(range_min, value))

    def _sector_minimum(self, scan, lower, upper):
        distances = []
        for index, raw_distance in enumerate(scan.ranges):
            angle = scan.angle_min + index * scan.angle_increment
            if self._angle_in_sector(angle, lower, upper):
                distance = self._valid_distance(
                    raw_distance, scan.range_min, scan.range_max)
                if distance is not None:
                    distances.append(distance)
        return min(distances) if distances else None

    def _sector_clearance(self, scan, lower, upper, percentile=0.65):
        """Score an escape side by its usable opening, not its single closest ray."""
        distances = []
        for index, raw_distance in enumerate(scan.ranges):
            angle = scan.angle_min + index * scan.angle_increment
            if self._angle_in_sector(angle, lower, upper):
                distance = self._valid_distance(
                    raw_distance, scan.range_min, scan.range_max)
                if distance is not None:
                    distances.append(distance)
        if not distances:
            return None
        distances.sort()
        rank = int((len(distances) - 1) * percentile)
        return distances[rank]

    def _warn_once(self, message):
        if message != self.last_warning:
            self.get_logger().warning(message)
            self.last_warning = message

    @staticmethod
    def _format_distance(value):
        return 'n/a' if value is None else f'{value:.2f}m'

    def _publish(self, linear=0.0, angular=0.0):
        if linear != 0.0 or angular != 0.0:
            self.last_warning = None
        command = Twist()
        command.linear.x = linear
        command.angular.z = angular
        self.cmd_pub.publish(command)

        now = time.monotonic()
        if self.turning:
            mode = 'avoid-left' if self.turn_direction > 0 else 'avoid-right'
        elif linear > 0.0:
            mode = 'course'
        elif angular != 0.0:
            mode = 'heading-recovery'
        elif (self.last_scan_time is None
                or now - self.last_scan_time > self.scan_timeout):
            mode = 'scan-timeout'
        else:
            mode = 'stopped'
        if (mode != self.last_logged_mode
                or now - self.last_status_time >= self.status_log_period):
            yaw = 'n/a' if self.current_yaw is None else f'{self.current_yaw:.2f}rad'
            odom_state = 'ready' if self.current_yaw is not None else 'waiting'
            self.get_logger().info(
                f'Motion mode={mode} v={linear:.2f}m/s '
                f'w={angular:.2f}rad/s '
                f'front={self._format_distance(self.latest_front)} '
                f'left={self._format_distance(self.latest_left)} '
                f'right={self._format_distance(self.latest_right)} '
                f'course_error={self.latest_course_error:.2f}rad '
                f'yaw={yaw} odom={odom_state}')
            self.last_status_time = now
            self.last_logged_mode = mode

    def scan_callback(self, scan):
        self.last_scan_time = time.monotonic()
        if self.current_yaw is None or self.course_heading is None:
            self._warn_once('Waiting for /odom; stopping until heading is known')
            self._publish()
            return

        if (not math.isfinite(scan.range_min)
                or not math.isfinite(scan.range_max)
                or scan.range_min < 0.0
                or scan.range_max <= scan.range_min
                or not math.isfinite(scan.angle_min)
                or not math.isfinite(scan.angle_increment)
                or scan.angle_increment == 0.0):
            self.get_logger().warning('Invalid LaserScan metadata; stopping')
            self._publish()
            return

        front = self._sector_minimum(
            scan, -self.front_half_angle, self.front_half_angle)
        if front is None:
            self.get_logger().warning('No usable front LiDAR returns; stopping')
            self._publish()
            return

        # Include near-front diagonals: openings in the test gates are ahead and
        # to one side, not necessarily perpendicular to the robot's current yaw.
        side_start = 0.25
        side_end = 1.50
        left = self._sector_clearance(scan, side_start, side_end)
        right = self._sector_clearance(scan, -side_end, -side_start)
        self.latest_front = front
        self.latest_left = left
        self.latest_right = right
        self.latest_course_error = self._course_error()

        if self.turning:
            # Keep the chosen direction until the wider front arc has cleared.
            if front >= self.clear_distance:
                self.turning = False
                self.turn_direction = 0.0
                self.turn_direction_switched = False
                self._publish_course_motion()
                return

            course_error = self._course_error()
            turn_clearance = left if self.turn_direction > 0 else right
            other_clearance = right if self.turn_direction > 0 else left
            other_direction = -self.turn_direction
            # Keep the selected side through this obstacle; scan noise must
            # not make the robot alternate left and right on successive scans.
            # Permit one emergency switch only when the chosen opening is
            # blocked and the opposite side has a clearly safe passage.
            if (turn_clearance is None
                    or turn_clearance <= self.stop_distance):
                can_switch = (
                    not self.turn_direction_switched
                    and turn_clearance is not None
                    and other_clearance is not None
                    and other_clearance >= self.clear_distance
                )
                if can_switch:
                    self.turn_direction = other_direction
                    self.turn_direction_switched = True
                    turn_clearance = other_clearance
                else:
                    self._warn_once(
                        'No safe passage on the selected side; stopping')
                    self._publish()
                    return

            if (abs(course_error) >= self.max_course_deviation
                    and self.turn_direction * course_error < 0.0):
                if front > self.stop_distance:
                    self._publish(linear=0.08, angular=0.0)
                else:
                    self._warn_once(
                        'Course heading limit reached; no safe forward clearance')
                    self._publish()
                return
            self._publish(angular=self.turn_direction * self.turn_speed)
            return

        if front <= self.stop_distance:
            if left is None or right is None:
                self.get_logger().warning('No usable side LiDAR returns; stopping')
                self._publish()
                return
            # Latch the direction to avoid switching sides on consecutive scans.
            self.turning = True
            self.turn_direction = 1.0 if left >= right else -1.0
            self.turn_direction_switched = False
            self._publish(angular=self.turn_direction * self.turn_speed)
        else:
            self._publish_course_motion()

    def _publish_course_motion(self):
        course_error = self._course_error()
        if abs(course_error) >= self.max_course_deviation:
            # Recover heading in place rather than driving against the course.
            angular = max(-self.turn_speed, min(
                self.turn_speed, self.heading_gain * course_error))
            self._publish(angular=angular)
            return

        # Keep forward speed steady and correct the course gently.
        linear = self.forward_speed
        angular = max(-0.16, min(
            0.16, 0.45 * self.heading_gain * course_error))
        self._publish(linear=linear, angular=angular)

    def scan_watchdog(self):
        if (self.last_scan_time is None
                or time.monotonic() - self.last_scan_time > self.scan_timeout):
            self._publish()


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # A launch-system shutdown may already have invalidated the ROS context.
        if rclpy.ok():
            node._publish()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
