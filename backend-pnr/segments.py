import json
import numpy as np
import random
import re
import os
import traceback

def create_fp(song):
    """
    Create a filepath for the song JSON, fixing the path construction.
    """
    # Remove special characters and convert to lowercase for filename
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', song).lower()
    
    # Get the current directory where segments.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create path to songs directory relative to current file
    filepath = os.path.join(current_dir, "songs", f"{clean_name}.json")
    
    print(f"Looking for song at: {filepath}")
    return filepath

class SongWorkoutMapper:
    def __init__(self, artist, level):
        # Keep level parameter for backward compatibility
        self.level = level
        
        try:
            # Get current directory where this file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.json_file_path = os.path.join(current_dir, "artists", "artist_directory.json")
            
            print(f"Artist directory path: {self.json_file_path}")
            with open(self.json_file_path, 'r') as f:
                self.artist_data = json.load(f)

            print("Artist detected by FER:", artist)
            print("Available artists in JSON:", list(self.artist_data.keys()))

            if artist not in self.artist_data:
                print(f"Error: {artist} not found in artist directory!")
                # Default to first artist
                artist = list(self.artist_data.keys())[0]
                print(f"Using default artist: {artist}")

            # Just use the first song for this artist
            self.song_fp = self.artist_data[artist][0]
            print("Selected Song:", self.song_fp)

            self.filepath = create_fp(self.song_fp)
            print("Looking for song JSON at:", self.filepath)

            # Get the workouts file path
            self.workouts_fp = os.path.join(current_dir, "workouts", "workouts.json")
            print(f"Workouts file path: {self.workouts_fp}")

            # Load the song data but be very flexible with format
            try:
                with open(self.filepath, 'r') as f:
                    self.song_data = json.load(f)
                print(f"Successfully loaded song JSON: {self.filepath}")
                
                # Print song data structure to debug
                print("Song data keys:", list(self.song_data.keys()))
                
                # Try to access different structures that might contain sections
                self.sections = self._extract_sections(self.song_data)
                if not self.sections:
                    print("No sections found, using defaults")
                    self.sections = self._create_default_sections()
            except Exception as e:
                print(f"Error loading song JSON: {e}")
                print(traceback.format_exc())
                self.song_data = {}
                self.sections = self._create_default_sections()

            # Load workouts with error handling
            try:
                with open(self.workouts_fp, 'r') as f:
                    self.workouts = json.load(f)
            except Exception as e:
                print(f"Error loading workouts: {e}")
                # Default workouts if file can't be loaded
                self.workouts = {
                    "arm_raises": ["arms", "mid", "instructions", 1.3],
                    "jumping_jacks": ["cardio", "mid", "instructions", 1.8],
                    "squats": ["legs", "mid", "instructions", 2.0]
                }
            
            # Debug info about sections
            print(f"Song sections found: {len(self.sections)}")
            section_durations = [s.get('duration', 0) for s in self.sections]
            print(f"Section durations: {section_durations}")
            
        except Exception as e:
            print(f"Error in SongWorkoutMapper initialization: {e}")
            print(traceback.format_exc())
            # Set defaults for critical properties
            self.workouts = {}
            self.sections = self._create_default_sections()
    
    def _extract_sections(self, data):
        """
        Try to extract sections from various JSON structures.
        """
        # Try different possible locations for sections
        if isinstance(data, dict):
            # Direct sections key
            if 'sections' in data and isinstance(data['sections'], list):
                print("Found sections at top level")
                return data['sections']
            
            # Sections in track
            if 'track' in data and isinstance(data['track'], dict):
                if 'sections' in data['track'] and isinstance(data['track']['sections'], list):
                    print("Found sections in track")
                    return data['track']['sections']
            
            # Try to find any key that might contain sections
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Check if items in list have duration property
                    if isinstance(value[0], dict) and 'duration' in value[0]:
                        print(f"Found sections in key: {key}")
                        return value
                
                # Try to go one level deeper
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, list) and len(subvalue) > 0:
                            if isinstance(subvalue[0], dict) and 'duration' in subvalue[0]:
                                print(f"Found sections in nested key: {key}.{subkey}")
                                return subvalue
        
        # Handle case where data is directly a list of sections
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict) and 'duration' in data[0]:
                print("Data is directly a list of sections")
                return data
        
        print("Could not find sections in the JSON structure")
        return []
    
    def _create_default_sections(self):
        """Create default sections when none are found."""
        print("Creating default sections")
        return [
            {"duration": 30},
            {"duration": 40},
            {"duration": 20},
            {"duration": 35},
            {"duration": 25}
        ]
    
    def create_dance_sections(self):
        """
        Extract durations from each section of the song.
        """
        try:
            print("Creating dance sections from song JSON sections...")
            
            if not self.sections:
                print("No sections found in song data")
                return [30, 40, 20]
            
            # Extract durations from each section
            durations = []
            for section in self.sections:
                try:
                    # Try to get duration value, defaulting to 30 if not found
                    duration = int(section.get("duration", 30))
                    if duration >= 10:  # Filter out very short sections
                        durations.append(duration)
                    print(f"Added section duration: {duration}")
                except (ValueError, TypeError) as e:
                    print(f"Error processing section duration: {e}")
            
            # If no valid durations, use defaults
            if not durations:
                print("No valid durations found, using defaults")
                return [30, 40, 20]
            
            # Limit to a reasonable number of sections
            if len(durations) > 5:
                print(f"Too many sections ({len(durations)}), limiting to 5")
                durations = durations[:5]
            elif len(durations) < 3:
                print(f"Too few sections ({len(durations)}), duplicating")
                durations = durations * 3
                durations = durations[:3]
            
            print(f"Final dance sections: {durations}")
            return durations
        except Exception as e:
            print(f"Error in create_dance_sections: {e}")
            print(traceback.format_exc())
            return [30, 40, 20]

    def create_workout(self):
        """
        Generates a workout routine based on the song's section durations.
        """
        try:
            # Get durations from song sections
            durations = self.create_dance_sections()
            
            # Get all exercises
            available_exercises = list(self.workouts.keys())
            if not available_exercises:
                print("No exercises found in workouts.json, using defaults")
                available_exercises = ["arm_raises", "jumping_jacks", "squats"]
            
            # Ensure we have enough exercises
            if len(available_exercises) < len(durations):
                available_exercises = available_exercises * (len(durations) // len(available_exercises) + 1)
            
            # Shuffle exercises for variety
            random.shuffle(available_exercises)
            
            # Create workout pairs: (exercise, duration)
            routine = []
            for i in range(len(durations)):
                exercise = available_exercises[i % len(available_exercises)]
                duration = durations[i]
                routine.append((exercise, duration))
                print(f"Added exercise: {exercise} for {duration} seconds")
            
            print(f"Generated {len(routine)} workout segments with durations: {durations}")
            return routine
        except Exception as e:
            print(f"Error in create_workout: {e}")
            print(traceback.format_exc())
            # Return a safe default
            return [("arm_raises", 30), ("jumping_jacks", 30), ("squats", 30)]