import cv2
import mediapipe as mp
import numpy as np
import time
import math
from segments import SongWorkoutMapper

class ExerciseDetector:
    """
    Class that handles exercise detection using MediaPipe Pose.
    Integrates with the FastAPI server to process frames and track exercise progress.
    """
    def __init__(self):
        # Initialize MediaPipe Pose
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose()
        
        # Set default schedule
        self.time_intervals = [30, 30, 30]  # Default: 30 seconds per exercise
        self.exercises = ["arm_raises", "jumping_jacks", "squats"]  # Default exercises
        
        # Initialize counters for each exercise
        self.counters = {
            "arm_raises": 0,
            "jumping_jacks": 0,
            "squats": 0,
            "toe_touch_front": 0,
            "lunges": {"left": 0, "right": 0},
            "toe_touches_sides": 0,
            "arm_stretches": 0,
            "cross_standing_crunches": 0,
            "side_standing_crunches": 0
        }
        
        # Initialize state variables for each exercise
        self.states = {
            "arm_raises": {"up": False},
            "jumping_jacks": {"open_state": False},
            "squats": {"squat_down": False},
            "toe_touch_front": {"touching": False},
            "lunges": {"left_down": False, "right_down": False},
            "toe_touches_sides": {"touching": False},
            "arm_stretches": {"stretched": False},
            "cross_standing_crunches": {"crunching": False},
            "side_standing_crunches": {"crunching": False}
        }
        
        # Keep track of time
        self.start_time = time.time()
        self.current_interval = 0
        self.intervals_cumulative = [sum(self.time_intervals[:i+1]) for i in range(len(self.time_intervals))]
    
    def set_schedule(self, time_intervals, exercises):
        """Update the exercise schedule with new time intervals and exercises."""
        self.time_intervals = time_intervals
        self.exercises = exercises
        self.start_time = time.time()
        self.current_interval = 0
        self.intervals_cumulative = [sum(self.time_intervals[:i+1]) for i in range(len(self.time_intervals))]

    def get_current_exercise(self):
        """Get the name of the current exercise in the schedule."""
        elapsed = time.time() - self.start_time
        for i, total_time in enumerate(self.intervals_cumulative):
            if elapsed < total_time:
                self.current_interval = i
                if i < len(self.exercises):
                    return self.exercises[i]
                break
        return None
    
    # In ExerciseDetector.get_time_remaining
    def get_time_remaining(self):
        """Get the time remaining for the current exercise in seconds."""
        elapsed = time.time() - self.start_time
        if self.current_interval >= len(self.intervals_cumulative):
            print(f"Current interval {self.current_interval} out of range {len(self.intervals_cumulative)}")
            return 0
        
        time_remaining = self.intervals_cumulative[self.current_interval] - elapsed
        print(f"Time remaining: {max(0, int(time_remaining))}s for exercise {self.exercises[self.current_interval] if self.current_interval < len(self.exercises) else 'None'}")
        return max(0, int(time_remaining))
    
    def get_all_counters(self):
        """Get all exercise counters."""
        return self.counters
    
    def reset_counters(self):
        """Reset all exercise counters to zero."""
        for exercise in self.counters:
            if isinstance(self.counters[exercise], dict):
                for key in self.counters[exercise]:
                    self.counters[exercise][key] = 0
            else:
                self.counters[exercise] = 0
        return {"message": "All counters reset to zero"}
    
    def process_frame(self, frame):
        """
        Process a frame with the current exercise detection algorithm.
        Returns the processed frame with annotations and exercise data.
        """
        current_exercise = self.get_current_exercise()
        if current_exercise is None:
            # If no current exercise (workout finished), return original frame
            return frame, {
                "exercise": "None",
                "counter": 0,
                "time_remaining": 0,
                "all_counters": self.get_all_counters()
            }
        
        # Map variations of exercise names
        exercise_mapping = {
            "arm_raises": "arm_raises",
            "arms_raise": "arm_raises",
            "jumping_jacks": "jumping_jacks",
            "squats": "squats",
            "toe_touch_front": "toe_touch_front",
            "lunges": "lunges",
            "toe_touches_sides": "toe_touches_sides",
            "toe_touch_intersected": "toe_touches_sides",
            "arm_stretches": "arm_stretches",
            "arms_stretching": "arm_stretches",
            "cross_standing_crunches": "cross_standing_crunches",
            "standing_crunch_cross": "cross_standing_crunches",
            "side_standing_crunches": "side_standing_crunches",
            "standing_crunch_side": "side_standing_crunches"
        }
        
        # Standardize exercise name
        std_exercise = exercise_mapping.get(current_exercise, current_exercise)
        
        # Process frame based on current exercise
        if std_exercise == "arm_raises":
            frame, self.states["arm_raises"]["up"], self.counters["arm_raises"] = self._detect_arms_raise(
                frame, self.states["arm_raises"]["up"], self.counters["arm_raises"]
            )
            counter = self.counters["arm_raises"]
            
        elif std_exercise == "jumping_jacks":
            frame, self.states["jumping_jacks"]["open_state"], self.counters["jumping_jacks"] = self._detect_jumping_jacks(
                frame, self.states["jumping_jacks"]["open_state"], self.counters["jumping_jacks"]
            )
            counter = self.counters["jumping_jacks"]
            
        elif std_exercise == "squats":
            frame, self.states["squats"]["squat_down"], self.counters["squats"] = self._detect_squats(
                frame, self.states["squats"]["squat_down"], self.counters["squats"]
            )
            counter = self.counters["squats"]
            
        elif std_exercise == "toe_touch_front":
            frame, self.states["toe_touch_front"]["touching"], self.counters["toe_touch_front"] = self._detect_toe_touch_front(
                frame, self.states["toe_touch_front"]["touching"], self.counters["toe_touch_front"]
            )
            counter = self.counters["toe_touch_front"]
            
        elif std_exercise == "lunges":
            frame, self.states["lunges"]["left_down"], self.states["lunges"]["right_down"], \
            self.counters["lunges"]["left"], self.counters["lunges"]["right"] = self._detect_lunges(
                frame, self.states["lunges"]["left_down"], self.states["lunges"]["right_down"],
                self.counters["lunges"]["left"], self.counters["lunges"]["right"]
            )
            counter = self.counters["lunges"]["left"] + self.counters["lunges"]["right"]
            
        elif std_exercise == "toe_touches_sides":
            frame, self.states["toe_touches_sides"]["touching"], self.counters["toe_touches_sides"] = self._detect_toe_touch_intersected(
                frame, self.states["toe_touches_sides"]["touching"], self.counters["toe_touches_sides"]
            )
            counter = self.counters["toe_touches_sides"]
            
        elif std_exercise == "arm_stretches":
            frame, self.states["arm_stretches"]["stretched"], self.counters["arm_stretches"] = self._detect_arms_stretching(
                frame, self.states["arm_stretches"]["stretched"], self.counters["arm_stretches"]
            )
            counter = self.counters["arm_stretches"]
            
        elif std_exercise == "cross_standing_crunches":
            frame, self.states["cross_standing_crunches"]["crunching"], self.counters["cross_standing_crunches"] = self._detect_standing_crunch_cross(
                frame, self.states["cross_standing_crunches"]["crunching"], self.counters["cross_standing_crunches"]
            )
            counter = self.counters["cross_standing_crunches"]
            
        elif std_exercise == "side_standing_crunches":
            frame, self.states["side_standing_crunches"]["crunching"], self.counters["side_standing_crunches"] = self._detect_standing_crunch_side_by_side(
                frame, self.states["side_standing_crunches"]["crunching"], self.counters["side_standing_crunches"]
            )
            counter = self.counters["side_standing_crunches"]
            
        else:
            # Unknown exercise
            cv2.putText(frame, "Unknown Exercise", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            counter = 0
        
        # Add exercise name and time remaining to frame
        cv2.putText(frame, f"Exercise: {current_exercise}", (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Time: {self.get_time_remaining()}s", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Prepare exercise data to return
        exercise_data = {
            "exercise": current_exercise,
            "counter": counter,
            "time_remaining": self.get_time_remaining(),
            "all_counters": self.get_all_counters()
        }
        
        return frame, exercise_data

    # ----------------- Utility Functions ----------------- #

    def _calculate_angle(self, a, b, c):
        """Calculate the angle (in degrees) between three points."""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def _euclidean_distance(self, pt1, pt2):
        """Return the Euclidean distance between two points."""
        return math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

    # ----------------- Exercise Detection Functions ----------------- #

    def _detect_arms_raise(self, frame, up, counter):
        """Detect arms raise by checking if the right elbow is above the right shoulder."""
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            points = {}
            for id, lm in enumerate(results.pose_landmarks.landmark):
                h, w, _ = frame.shape
                points[id] = (int(lm.x * w), int(lm.y * h))
            if all(k in points for k in [11, 12, 13, 14]):
                cv2.circle(frame, points[12], 15, (255, 0, 0), cv2.FILLED)
                cv2.circle(frame, points[14], 15, (255, 0, 0), cv2.FILLED)
                cv2.circle(frame, points[11], 15, (255, 0, 0), cv2.FILLED)
                cv2.circle(frame, points[13], 15, (255, 0, 0), cv2.FILLED)
                if not up and points[14][1] + 40 < points[12][1]:
                    up = True
                    counter += 1
                    print("Arms Raise - Up")
                elif points[14][1] > points[12][1]:
                    up = False
        cv2.putText(frame, f"Count: {counter}", (100, 150),
                    cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
        return frame, up, counter

    def _detect_jumping_jacks(self, frame, open_state, counter):
        """Detect jumping jacks by checking if arms are up and legs are apart."""
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            points = {}
            for id, lm in enumerate(results.pose_landmarks.landmark):
                h, w, _ = frame.shape
                points[id] = (int(lm.x * w), int(lm.y * h))
            required_ids = [11, 12, 15, 16, 23, 24, 25, 26]
            if all(k in points for k in required_ids):
                arms_up = points[15][1] < points[11][1] and points[16][1] < points[12][1]
                knee_distance = abs(points[25][0] - points[26][0])
                hip_distance = abs(points[23][0] - points[24][0])
                legs_apart = knee_distance > hip_distance
                if arms_up and legs_apart and not open_state:
                    open_state = True
                    print("Jumping Jacks - Open")
                elif open_state and not (arms_up and legs_apart):
                    open_state = False
                    counter += 1
                    print("Jumping Jacks - Rep Count:", counter)
        cv2.putText(frame, f"Count: {counter}", (100, 150),
                    cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
        return frame, open_state, counter

    def _detect_squats(self, frame, squat_down, counter):
        """Detect squats using the angle between hip, knee, and ankle (right side)."""
        frame = cv2.resize(frame, (1280, 720))
        imageRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imageRGB)
        
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark
            h, w, _ = frame.shape
            hip = [landmarks[24].x * w, landmarks[24].y * h]
            knee = [landmarks[26].x * w, landmarks[26].y * h]
            ankle = [landmarks[28].x * w, landmarks[28].y * h]
            knee_angle = self._calculate_angle(hip, knee, ankle)
            cv2.putText(frame, str(int(knee_angle)), tuple(np.array(knee, dtype=int)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if knee_angle < 100:
                squat_down = True
                cv2.putText(frame, "Down", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
            if squat_down and knee_angle > 160:
                squat_down = False
                counter += 1
                cv2.putText(frame, "Up", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Reps: {counter}", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2, cv2.LINE_AA)
        return frame, squat_down, counter

    def _detect_toe_touch_front(self, frame, touching, counter):
        """Detect toe touches from the front by comparing the average positions of wrists and ankles."""
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        touch_threshold = 150
        margin = 30
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            h, w, _ = frame.shape
            landmarks = results.pose_landmarks.landmark
            points = {}
            for id, lm in enumerate(landmarks):
                points[id] = (int(lm.x * w), int(lm.y * h))
            if all(k in points for k in [15, 16, 27, 28]):
                left_wrist = points[15]
                right_wrist = points[16]
                left_ankle = points[27]
                right_ankle = points[28]
                avg_wrist = ((left_wrist[0] + right_wrist[0]) // 2,
                            (left_wrist[1] + right_wrist[1]) // 2)
                avg_ankle = ((left_ankle[0] + right_ankle[0]) // 2,
                            (left_ankle[1] + right_ankle[1]) // 2)
                cv2.circle(frame, avg_wrist, 10, (255, 0, 0), cv2.FILLED)
                cv2.circle(frame, avg_ankle, 10, (0, 255, 0), cv2.FILLED)
                dist = self._euclidean_distance(avg_wrist, avg_ankle)
                cv2.putText(frame, f"Dist: {int(dist)}", (50, 100),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                if not touching and dist < touch_threshold:
                    touching = True
                    print("Toe Touch Down")
                elif touching and dist > touch_threshold + margin:
                    touching = False
                    counter += 1
                    print("Stand Up - Count:", counter)
        cv2.putText(frame, f"Count: {counter}", (100, 150),
                    cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
        return frame, touching, counter

    def _detect_lunges(self, frame, left_lunge_down, right_lunge_down, left_counter, right_counter):
        """Detect lunges by calculating knee angles for both legs."""
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        lunge_down_angle = 110
        lunge_up_angle = 160
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            h, w, _ = frame.shape
            landmarks = results.pose_landmarks.landmark
            left_hip = (int(landmarks[23].x * w), int(landmarks[23].y * h))
            left_knee = (int(landmarks[25].x * w), int(landmarks[25].y * h))
            left_ankle = (int(landmarks[27].x * w), int(landmarks[27].y * h))
            right_hip = (int(landmarks[24].x * w), int(landmarks[24].y * h))
            right_knee = (int(landmarks[26].x * w), int(landmarks[26].y * h))
            right_ankle = (int(landmarks[28].x * w), int(landmarks[28].y * h))
            left_knee_angle = self._calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = self._calculate_angle(right_hip, right_knee, right_ankle)
            cv2.putText(frame, str(int(left_knee_angle)), left_knee,
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            cv2.putText(frame, str(int(right_knee_angle)), right_knee,
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            if not left_lunge_down and left_knee_angle < lunge_down_angle:
                left_lunge_down = True
                print("Left Lunge Down")
            elif left_lunge_down and left_knee_angle > lunge_up_angle:
                left_lunge_down = False
                left_counter += 1
                print("Left Lunge Up - Count:", left_counter)
            if not right_lunge_down and right_knee_angle < lunge_down_angle:
                right_lunge_down = True
                print("Right Lunge Down")
            elif right_lunge_down and right_knee_angle > lunge_up_angle:
                right_lunge_down = False
                right_counter += 1
                print("Right Lunge Up - Count:", right_counter)
            total_counter = left_counter + right_counter
            cv2.putText(frame, f"Total Lunges: {total_counter}", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        return frame, left_lunge_down, right_lunge_down, left_counter, right_counter

    def _detect_toe_touch_intersected(self, frame, touching, counter):
        """Detect toe touches using an intersected method (left wrist to right ankle and vice versa)."""
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        touch_threshold = 100
        margin = 30
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            h, w, _ = frame.shape
            landmarks = results.pose_landmarks.landmark
            left_wrist = (int(landmarks[15].x * w), int(landmarks[15].y * h))
            right_wrist = (int(landmarks[16].x * w), int(landmarks[16].y * h))
            left_ankle = (int(landmarks[27].x * w), int(landmarks[27].y * h))
            right_ankle = (int(landmarks[28].x * w), int(landmarks[28].y * h))
            cv2.circle(frame, left_wrist, 10, (255,0,0), cv2.FILLED)
            cv2.circle(frame, right_wrist, 10, (255,0,0), cv2.FILLED)
            cv2.circle(frame, left_ankle, 10, (0,255,0), cv2.FILLED)
            cv2.circle(frame, right_ankle, 10, (0,255,0), cv2.FILLED)
            left_touch_distance = self._euclidean_distance(left_wrist, right_ankle)
            right_touch_distance = self._euclidean_distance(right_wrist, left_ankle)
            cv2.putText(frame, f"Ldist: {int(left_touch_distance)}", (50, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (0,255,255), 2)
            cv2.putText(frame, f"Rdist: {int(right_touch_distance)}", (50, 100),
                        cv2.FONT_HERSHEY_PLAIN, 2, (0,255,255), 2)
            touch_detected = (left_touch_distance < touch_threshold) or (right_touch_distance < touch_threshold)
            if not touching and touch_detected:
                touching = True
                print("Touch detected")
            elif touching and (left_touch_distance > touch_threshold + margin and right_touch_distance > touch_threshold + margin):
                touching = False
                counter += 1
                print("Rep counted:", counter)
        cv2.putText(frame, f"Count: {counter}", (100, 150),
                    cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
        return frame, touching, counter

    def _detect_arms_stretching(self, frame, stretched, counter):
        """Detect arms stretching by checking if both wrists are above the nose and then lowered."""
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            h, w, _ = frame.shape
            landmarks = results.pose_landmarks.landmark
            left_wrist = (int(landmarks[15].x * w), int(landmarks[15].y * h))
            right_wrist = (int(landmarks[16].x * w), int(landmarks[16].y * h))
            nose = (int(landmarks[0].x * w), int(landmarks[0].y * h))
            left_shoulder = (int(landmarks[11].x * w), int(landmarks[11].y * h))
            right_shoulder = (int(landmarks[12].x * w), int(landmarks[12].y * h))
            cv2.circle(frame, left_wrist, 10, (255,0,0), cv2.FILLED)
            cv2.circle(frame, right_wrist, 10, (255,0,0), cv2.FILLED)
            cv2.circle(frame, nose, 10, (0,255,0), cv2.FILLED)
            cv2.circle(frame, left_shoulder, 10, (0,0,255), cv2.FILLED)
            cv2.circle(frame, right_shoulder, 10, (0,0,255), cv2.FILLED)
            shoulder_y = (left_shoulder[1] + right_shoulder[1]) // 2
            if not stretched and left_wrist[1] < nose[1] and right_wrist[1] < nose[1]:
                stretched = True
                print("Stretch position reached")
            elif stretched and left_wrist[1] > shoulder_y + 20 and right_wrist[1] > shoulder_y + 20:
                stretched = False
                counter += 1
                print("Returned to start - Count:", counter)
            cv2.putText(frame, f"Count: {counter}", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
        return frame, stretched, counter

    def _detect_standing_crunch_cross(self, frame, crunching, counter):
        """
        Detect a standing crunch (Cross version) where the person is expected to bring each elbow toward its own knee.
        Uses a higher distance threshold (350 pixels) for detection.
        """
        # Parameters for cross detection.
        distance_threshold = 350  
        margin = 20
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            h, w, _ = frame.shape
            landmarks = results.pose_landmarks.landmark
            # Retrieve same-side landmarks.
            left_elbow = (int(landmarks[13].x * w), int(landmarks[13].y * h))
            right_elbow = (int(landmarks[14].x * w), int(landmarks[14].y * h))
            left_knee = (int(landmarks[25].x * w), int(landmarks[25].y * h))
            right_knee = (int(landmarks[26].x * w), int(landmarks[26].y * h))
            cv2.circle(frame, left_elbow, 10, (0,255,0), cv2.FILLED)
            cv2.circle(frame, right_elbow, 10, (0,255,0), cv2.FILLED)
            cv2.circle(frame, left_knee, 10, (0,255,0), cv2.FILLED)
            cv2.circle(frame, right_knee, 10, (0,255,0), cv2.FILLED)
            # Compute distances on each side.
            left_distance = self._euclidean_distance(left_elbow, left_knee)
            right_distance = self._euclidean_distance(right_elbow, right_knee)
            cv2.putText(frame, f"Left: {int(left_distance)}", (50,50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255,255,0), 2)
            cv2.putText(frame, f"Right: {int(right_distance)}", (50,80),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255,255,0), 2)
            # Check if the person is standing.
            avg_shoulder_y = (landmarks[11].y + landmarks[12].y) / 2
            avg_hip_y = (landmarks[23].y + landmarks[24].y) / 2
            standing = avg_shoulder_y < avg_hip_y
            if standing:
                if not crunching and left_distance < distance_threshold and right_distance < distance_threshold:
                    crunching = True
                    print("Standing Crunch (Cross) - Crunch Down")
                elif crunching and left_distance > distance_threshold + margin and right_distance > distance_threshold + margin:
                    crunching = False
                    counter += 1
                    print("Standing Crunch (Cross) - Stand Up - Count:", counter)
            else:
                crunching = False
                cv2.putText(frame, "Not Standing", (50,120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        cv2.putText(frame, f"Count: {counter}", (100,150),
                cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
        return frame, crunching, counter

    def _detect_standing_crunch_side_by_side(self, frame, crunching, counter):
        """
        Detect a standing crunch (Side-by-Side version) where the detection requires checking both same-side and cross distances.
        For example, one condition might be: left elbow-to-left knee is below threshold while the cross distance (left elbow-to-right knee) is above threshold.
        """
        # Parameters for side-by-side detection.
        distance_threshold = 100  
        margin = 20
        frame = cv2.resize(frame, (1280, 720))
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(imgRGB)
        if results.pose_landmarks:
            self.mpDraw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            h, w, _ = frame.shape
            landmarks = results.pose_landmarks.landmark
            # Retrieve same-side landmarks.
            left_elbow = (int(landmarks[13].x * w), int(landmarks[13].y * h))
            right_elbow = (int(landmarks[14].x * w), int(landmarks[14].y * h))
            left_knee = (int(landmarks[25].x * w), int(landmarks[25].y * h))
            right_knee = (int(landmarks[26].x * w), int(landmarks[26].y * h))
            # Compute same-side distances.
            left_distance = self._euclidean_distance(left_elbow, left_knee)
            right_distance = self._euclidean_distance(right_elbow, right_knee)
            # Compute cross distances.
            lh_rk_distance = self._euclidean_distance(left_elbow, right_knee)
            rh_lk_distance = self._euclidean_distance(right_elbow, left_knee)
            cv2.putText(frame, f"Left: {int(left_distance)}", (50,50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255,255,0), 2)
            cv2.putText(frame, f"Right: {int(right_distance)}", (50,80),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255,255,0), 2)
            # Check if standing.
            avg_shoulder_y = (landmarks[11].y + landmarks[12].y) / 2
            avg_hip_y = (landmarks[23].y + landmarks[24].y) / 2
            standing = avg_shoulder_y < avg_hip_y
            if standing:
                # Example logic: if left side is "crunched" (left_distance < threshold)
                # while the cross distance (left elbow to right knee) is greater than threshold,
                # or vice versa on the right side.
                if not crunching and ((left_distance < distance_threshold and lh_rk_distance > distance_threshold) or 
                                    (right_distance < distance_threshold and rh_lk_distance > distance_threshold)):
                    crunching = True
                    print("Standing Crunch (Side-by-Side) - Crunch Down")
                elif crunching and left_distance > distance_threshold + margin and right_distance > distance_threshold + margin:
                    crunching = False
                    counter += 1
                    print("Standing Crunch (Side-by-Side) - Stand Up - Count:", counter)
            else:
                crunching = False
                cv2.putText(frame, "Not Standing", (50,120),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        cv2.putText(frame, f"Count: {counter}", (100,150),
                    cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
        return frame, crunching, counter


def create_workout_with_mapper(artist, intensity):
    """
    Use the SongWorkoutMapper class to create a workout routine based on artist and intensity.
    
    Args:
        artist (str): Artist name to use for generating the workout
        intensity (str): Workout intensity level ("LOW", "MEDIUM", or "HIGH")
        
    Returns:
        tuple: (time_intervals, exercises) - Lists of time intervals and corresponding exercises
    """
    # Normalize intensity value to match what SongWorkoutMapper expects
    if intensity.upper() == "MEDIUM":
        normalized_intensity = "MED"
    else:
        normalized_intensity = intensity.upper()
    
    print(f"Creating workout for artist: {artist}, intensity: {normalized_intensity}")
    
    try:
        # Create a SongWorkoutMapper instance
        mapper = SongWorkoutMapper(artist, normalized_intensity)
        
        # Generate time intervals and exercises
        time_intervals = mapper.create_dance_sections()
        workout_pairs = mapper.create_workout()
        
        # Extract just the exercise names from the workout pairs
        exercises = [exercise for exercise, _ in workout_pairs]
        
        print(f"Successfully created workout for {artist} with {len(exercises)} exercises")
        return time_intervals, exercises
    
    except Exception as e:
        print(f"Error creating workout: {e}")
        # Return a default workout in case of error
        return [30, 30, 30], ["arm_raises", "jumping_jacks", "squats"]