import json
import numpy as np
import random

import json

class SongWorkoutMapper:
    def __init__(self, artist, level):
        """
        Initialize the SongWorkoutMapper with the path to the song analysis JSON file.
        
        Args:
            json_file_path: Path to the song analysis JSON file
        """
        self.level = level
        self.mode = {"LOW":1, "MED":1.45, "HIGH":1.9}
        self.song_pick = {"LOW":0, "MED":1, "HIGH":2}
        self.json_file_path = "artists/artist_directory.json"
        with open(self.json_file_path, 'r') as f:
            self.artist_data = json.load(f)
        try:
            self.song_fp = self.artist_data[artist][self.song_pick[level]]
        except:
            try:
                self.song_fp = self.artist_data[artist][self.song_pick[level]-1]
            except:
                self.song_fp = self.artist_data[artist][self.song_pick[level]-2]
                
        def create_fp(song):
            song=song.replace("'","")
            song=song.replace(",","")
            song = song.replace(" ","")
            filepath = f"songs/{song.lower()}.json"
            return filepath
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
