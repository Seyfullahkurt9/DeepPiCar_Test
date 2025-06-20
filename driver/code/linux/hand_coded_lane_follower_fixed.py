import cv2
import numpy as np
import logging
import math
import sys
import os

_SHOW_IMAGE = False


class HandCodedLaneFollower(object):

    def __init__(self, car=None):
        logging.info('Creating a HandCodedLaneFollower...')
        self.car = car
        self.curr_steering_angle = 90

    def follow_lane(self, frame):
        # Main entry point of the lane follower
        # Tell the car to follow the lane
        lane_lines, frame = detect_lane(frame)
        final_frame = self.steer(frame, lane_lines)
        return final_frame

    def steer(self, frame, lane_lines):
        logging.debug('steering...')
        if len(lane_lines) == 0:
            logging.error('No lane lines detected, nothing to do.')
            return frame

        new_steering_angle = compute_steering_angle(frame, lane_lines)
        self.curr_steering_angle = stabilize_steering_angle(self.curr_steering_angle, new_steering_angle, len(lane_lines))

        if self.car is not None:
            self.car.front_wheels.turn(self.curr_steering_angle)
        curr_heading_image = display_heading_line(frame, self.curr_steering_angle)
        show_image("heading", curr_heading_image)

        return curr_heading_image


############################
# Frame processing functions
############################
def detect_lane(frame):
    logging.debug('detecting lane lines...')

    cropped_frame = crop_roi(frame)
    show_image("cropped", cropped_frame)

    binary_frame = detect_edges(cropped_frame)
    show_image("edges", binary_frame)

    line_segments = detect_line_segments(binary_frame)
    line_segment_image = display_lines(cropped_frame, line_segments)
    show_image("line_segments", line_segment_image)

    lane_lines = average_slope_intercept(cropped_frame, line_segments)
    lane_lines_image = display_lines(cropped_frame, lane_lines)
    show_image("lane_lines", lane_lines_image)

    return lane_lines, lane_lines_image


def crop_roi(frame):
    """
    Crop the image to region of interest to limit the lane detection area
    to the bottom half of the screen
    """
    height, width = frame.shape[:2]
    
    # Define polygon coordinates for ROI (region of interest)
    polygons = np.array([
        [(0, height * 1 // 2), (width, height * 1 // 2), (width, height), (0, height)]
    ], np.int32)
    
    mask = np.zeros_like(frame)
    cv2.fillPoly(mask, polygons, 255)
    cropped_frame = cv2.bitwise_and(frame, mask)
    return cropped_frame


def detect_edges(frame):
    # filter for blue lane lines
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    show_image("hsv", hsv)
    lower_blue = np.array([30, 40, 0])
    upper_blue = np.array([150, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    show_image("blue_mask", mask)

    # detect edges
    edges = cv2.Canny(mask, 200, 400)

    return edges


def detect_line_segments(cropped_edges):
    # tuning min_threshold, minLineLength, maxLineGap is a trial and error process by hand
    rho = 1  # precision in pixel, i.e. 1 pixel
    angle = np.pi / 180  # precision in angle, i.e. 1 degree
    min_threshold = 10  # minimal of votes
    line_segments = cv2.HoughLinesP(cropped_edges, rho, angle, min_threshold, np.array([]), minLineLength=8,
                                    maxLineGap=4)

    if line_segments is not None:
        for line_segment in line_segments:
            logging.debug('detected line_segment:')
            logging.debug("%s of length %s" % (line_segment, length_of_line_segment(line_segment[0])))

    return line_segments


def average_slope_intercept(frame, line_segments):
    """
    This function combines line segments into one or two lane lines
    If all line segments belong to the same lane, then we compute the average slope and intercept.
    If line segments belong to two lanes, then we separate them by their slope (i.e. slope < 0 for left lane and slope > 0 for right lane).
    We then compute the average slope and intercept for each of the lanes.
    """
    if line_segments is None:
        logging.info('No line_segments segments detected')
        return []

    height, width, _ = frame.shape
    left_fit = []
    right_fit = []

    boundary = 1/3
    left_region_boundary = width * (1 - boundary)  # left lane line segment should be on left 2/3 of the screen
    right_region_boundary = width * boundary # right lane line segment should be on left 2/3 of the screen

    for line_segment in line_segments:
        for x1, y1, x2, y2 in line_segment:
            if x1 == x2:
                logging.info('skipping vertical line segment (slope=inf): %s' % line_segment)
                continue
            fit = np.polyfit((x1, x2), (y1, y2), 1)
            slope = fit[0]
            intercept = fit[1]
            if slope < 0:
                if x1 < left_region_boundary and x2 < left_region_boundary:
                    left_fit.append((slope, intercept))
            else:
                if x1 > right_region_boundary and x2 > right_region_boundary:
                    right_fit.append((slope, intercept))

    left_fit_average = np.average(left_fit, axis=0)
    if len(left_fit) > 0:
        lane_lines.append(make_points(frame, left_fit_average))

    right_fit_average = np.average(right_fit, axis=0)
    if len(right_fit) > 0:
        lane_lines.append(make_points(frame, right_fit_average))

    logging.debug('lane lines: %s' % lane_lines)  # [[[316, 720, 484, 432]], [[1009, 720, 718, 432]]]

    return lane_lines


def compute_steering_angle(frame, lane_lines):
    """ Find the steering angle based on lane line coordinate
        We assume that camera is calibrated to point to dead center
    """
    if len(lane_lines) == 0:
        logging.info('No lane lines detected, do nothing')
        return -90

    height, width, _ = frame.shape
    if len(lane_lines) == 1:
        logging.debug('Only detected one lane line, just follow it. %s' % lane_lines[0])
        x1, _, x2, _ = lane_lines[0][0]
        x_offset = x2 - x1
    else:
        camera_mid_offset_percent = 0.02 # 0.0 means car pointing to center, -0.03: car is centered to left, +0.03 means car pointing to right
        mid_x = int(width / 2 * (1 + camera_mid_offset_percent))
        left_x2 = lane_lines[0][0][2]
        right_x2 = lane_lines[1][0][2]
        lane_center = int((left_x2 + right_x2) / 2)
        x_offset = lane_center - mid_x

    # find the steering angle, which is angle between navigation direction to end of center line
    y_offset = int(height / 2)

    # angle (in radian) to center vertical line
    angle_to_mid_radian = math.atan(x_offset / y_offset)
    # angle (in degrees) to center vertical line
    angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / math.pi)
    # this is the steering angle needed by picar front wheel
    steering_angle = angle_to_mid_deg + 90

    logging.debug('new steering angle: %s' % steering_angle)
    return steering_angle


def stabilize_steering_angle(curr_steering_angle, new_steering_angle, num_of_lane_lines, max_angle_deviation_two_lines=5, max_angle_deviation_one_lane=1):
    """
    Using last steering angle to stabilize the steering angle
    This can be improved to use last N angles, etc
    if new angle is too different from current angle, only turn by max_angle_deviation degrees
    """
    if num_of_lane_lines == 2 :
        # if both lane lines detected, then we can deviate more
        max_angle_deviation = max_angle_deviation_two_lines
    else :
        # if only one lane detected, don't deviate too much
        max_angle_deviation = max_angle_deviation_one_lane
    
    angle_deviation = new_steering_angle - curr_steering_angle

    if abs(angle_deviation) > max_angle_deviation:
        stabilized_steering_angle = int(curr_steering_angle
                                        + max_angle_deviation * angle_deviation / abs(angle_deviation))
    else:
        stabilized_steering_angle = new_steering_angle
    logging.info('Proposed angle: %s, stabilized angle: %s' % (new_steering_angle, stabilized_steering_angle))
    return stabilized_steering_angle


def display_lines(frame, lines, line_color=(0, 255, 0), line_width=10):
    line_image = np.zeros_like(frame)
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), line_color, line_width)
    line_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)
    return line_image


def display_heading_line(frame, steering_angle, line_color=(0, 0, 255), line_width=5, ):
    heading_image = np.zeros_like(frame)
    height, width, _ = frame.shape

    # figure out the heading line from steering angle
    # heading line (x1,y1) is always center bottom of the screen
    # (x2, y2) requires a bit of trigonometry

    # Note: the steering angle of:
    # 0-89 degree: turn left
    # 90 degree: going straight
    # 91-180 degree: turn right 
    steering_angle_radian = steering_angle / 180.0 * math.pi
    x1 = int(width / 2)
    y1 = height
    x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
    y2 = int(height / 2)

    cv2.line(heading_image, (x1, y1), (x2, y2), line_color, line_width)
    heading_image = cv2.addWeighted(frame, 0.8, heading_image, 1, 1)

    return heading_image


def length_of_line_segment(line):
    x1, y1, x2, y2 = line
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def show_image(title, frame, show=_SHOW_IMAGE):
    if show:
        cv2.imshow(title, frame)


def make_points(frame, line):
    """
    FIXED VERSION: Windows'ta bulduğumuz sıfıra bölme hatasını düzelttik
    """
    height, width, _ = frame.shape
    slope, intercept = line
    y1 = height  # bottom of the frame
    y2 = int(y1 * 1 / 2)  # make points from middle of the frame down

    # CRITICAL FIX: Windows'ta bulduğumuz sıfıra bölme kontrolü
    if abs(slope) < 0.001:  # slope sıfıra çok yakınsa
        logging.info('Detected near-vertical line, using center vertical line')
        return [[int(width/2), y1, int(width/2), y2]]  # dikey çizgi döndür

    # bound the coordinates within the frame
    try:
        x1 = max(-width, min(2 * width, int((y1 - intercept) / slope)))
        x2 = max(-width, min(2 * width, int((y2 - intercept) / slope)))
        return [[x1, y1, x2, y2]]
    except (ZeroDivisionError, OverflowError):
        logging.warning('Mathematical error in make_points, using fallback')
        return [[int(width/2), y1, int(width/2), y2]]


############################
# Test Functions
############################
def test_photo(file):
    lane_follower = HandCodedLaneFollower()
    frame = cv2.imread(file)
    if frame is None:
        logging.error('Could not load image: %s' % file)
        return
    combo_image = lane_follower.follow_lane(frame)
    show_image('final', combo_image, True)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def test_video(video_file):
    lane_follower = HandCodedLaneFollower()
    
    # Try different camera indices for Raspberry Pi
    camera_indices = [0, 1, '/dev/video0', '/dev/video1']
    cap = None
    
    for idx in camera_indices:
        try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                logging.info('Successfully opened camera at index: %s' % idx)
                break
            cap.release()
        except Exception as e:
            logging.debug('Failed to open camera at index %s: %s' % (idx, e))
            continue
    
    if cap is None or not cap.isOpened():
        logging.error('Could not open any camera')
        return

    try:
        logging.info('Press q to quit')
        while True:
            ret, frame = cap.read()
            if not ret:
                logging.error('Failed to read frame from camera')
                break
                
            combo_image = lane_follower.follow_lane(frame)
            cv2.imshow('Lane Following', combo_image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        test_photo(sys.argv[1])
    else:
        test_video(None) 