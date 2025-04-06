import json
import numpy as np
import random
import re
import json

def create_fp(song):
    song = re.sub(r'[^a-zA-Z0-9]', '', song)  # Keep only letters and numbers
    return f"songs/{song.lower()}.json"

class SongWorkoutMapper:
    def __init__(self, artist, level):
        self.level = level
        self.mode = {"LOW":1, "MED":1.45, "HIGH":1.9}
        self.song_pick = {"LOW":0, "MED":1, "HIGH":2}
        self.json_file_path = "artists/artist_directory.json"

        with open(self.json_file_path, 'r') as f:
            self.artist_data = json.load(f)

        # Debugging Prints
        print("Artist detected by FER:", artist)
        print("Available artists in JSON:", list(self.artist_data.keys()))

        # Check if artist is in the dictionary
        if artist not in self.artist_data:
            print(f"Error: {artist} not found in artist directory!")
            return

        # Try selecting a song
        try:
            self.song_fp = self.artist_data[artist][self.song_pick[level]]
        except IndexError:
            print(f"Warning: Not enough songs for {artist}, selecting the last available song.")
            self.song_fp = self.artist_data[artist][-1]
        
        print("Selected Song:", self.song_fp)  # Debugging print

        # Generate filepath
        self.filepath = create_fp(self.song_fp)
        print("Looking for song JSON at:", self.filepath)  # Debugging print

        self.workouts_fp = "workouts/workouts.json"

        # Load song and workout data
        try:
            with open(self.filepath, 'r') as f:
                self.song_data = json.load(f)
            print("Successfully loaded song:", self.song_data['track']['name'])  # Debugging print
        except FileNotFoundError:
            print("Error: Could not find song JSON at", self.filepath)

        with open(self.workouts_fp, 'r') as f:
            self.workouts = json.load(f)

        def get_song(self):
            return self.song_fp

        self.filepath = create_fp(self.song_fp)
        
        self.workouts_fp = "workouts/workouts.json" ###check filepaths functioning
        with open(self.filepath, 'r') as f:
            self.song_data = json.load(f)
        with open(self.workouts_fp, 'r') as f:
            self.workouts = json.load(f)
        
        # Extract useful song properties
        self.duration = self.song_data['track']['duration']
        self.tempo = self.song_data['track']['tempo']
        self.beats = self.song_data['beats']
        self.sections = self.song_data['sections']

        
    def create_dance_sections(self,max_section = 45):
        data = self.song_data
        
        time=[]
        for section in data['sections']:
            if float(section['duration'])<=max_section:
                time.append(section['start'])
            else:
                n = int(np.floor(float(section['duration']))/max_section)+1
                piece = float(section['duration'])/n
                initial = float(section['start'])
                for i in list(range(n)):
                    time.append(initial+i*piece)
        time.append(data['track']['duration'])
        return time

    def create_workout(self, stamina = 45):
        """
        LEVELS CAN BE LOW, MED, HIGH
        Creates a song cut by selecting and repeating sections to match the desired length
        while maintaining musical coherence.
        
        Args:
            sections: List of time intervals from create_dance_sections()
            
        Returns:
            List of tuples representing the final song cut with repeated sections

        """
        factor = self.mode[self.level]
        sections = self.create_dance_sections(stamina)
        routine = []
        #print(list(self.workouts.keys()))
        for i in list(range(len(sections)-1)):
            length = sections[i+1]-sections[i]
            if i == 0:
                choice =random.choice(list(self.workouts.keys()))
            else:
                #print(routine[i-1][0])
                cond_1 = self.workouts[routine[i-1][0]][0]
                filtered = list(filter(lambda k: not cond_1 in self.workouts[k], self.workouts))
                choice = random.choice(filtered)
            routine.append((choice, np.ceil(factor*length/self.workouts[choice][-1])))
        return routine
