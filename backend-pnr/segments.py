import json
import numpy as np
import random
import re

def create_fp(song):
    # Remove special characters to generate a consistent filepath
    song = re.sub(r'[^a-zA-Z0-9]', '', song)
    return f"songs/{song.lower()}.json"

class SongWorkoutMapper:
    def __init__(self, artist, level):
        self.level = level  # Still kept for song selection purposes only.
        # The mode and song_pick dictionaries are no longer used in the workout generation.
        self.mode = {"LOW": 1, "MED": 1.45, "HIGH": 1.9}
        self.song_pick = {"LOW": 0, "MED": 1, "HIGH": 2}
        self.json_file_path = "artists/artist_directory.json"

        with open(self.json_file_path, 'r') as f:
            self.artist_data = json.load(f)

        print("Artist detected by FER:", artist)
        print("Available artists in JSON:", list(self.artist_data.keys()))

        if artist not in self.artist_data:
            print(f"Error: {artist} not found in artist directory!")
            return

        try:
            self.song_fp = self.artist_data[artist][self.song_pick[level]]
        except IndexError:
            print(f"Warning: Not enough songs for {artist}, selecting the last available song.")
            self.song_fp = self.artist_data[artist][-1]
        
        print("Selected Song:", self.song_fp)

        self.filepath = create_fp(self.song_fp)
        print("Looking for song JSON at:", self.filepath)

        self.workouts_fp = "workouts/workouts.json"

        try:
            with open(self.filepath, 'r') as f:
                self.song_data = json.load(f)
            print("Successfully loaded song:", self.song_data['track']['name'])
        except FileNotFoundError:
            print("Error: Could not find song JSON at", self.filepath)
            return

        with open(self.workouts_fp, 'r') as f:
            self.workouts = json.load(f)

        self.duration = float(self.song_data['track'].get('duration', 0))
        self.tempo = self.song_data['track']['tempo']
        self.sections = self.song_data.get('sections', [])
    
    def create_workout(self):
        """
        Generates a workout routine based on the song's total duration.
        The routine is a random number of segments (between 2 and 6) whose durations sum to the song's duration.
        Returns a list of tuples: (exercise_name, segment_duration)
        """
        # Choose a random number of workout segments.
        num_segments = random.randint(5, 10)
        
        # Create random split points to partition the song's duration.
        # Generate (num_segments - 1) random time stamps between 0 and self.duration.
        splits = sorted([random.uniform(0, self.duration) for _ in range(num_segments - 1)])
        boundaries = [0] + splits + [self.duration]
        
        routine = []
        for i in range(num_segments):
            segment_duration = boundaries[i+1] - boundaries[i]
            exercise_choice = random.choice(list(self.workouts.keys()))
            routine.append((exercise_choice, segment_duration))
        
        print(f"Generated {num_segments} workout segments for the song duration of {self.duration} seconds.")
        return routine
