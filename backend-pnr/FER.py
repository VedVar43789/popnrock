import cv2
import joblib
import numpy as np
import time
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity

def get_artist_name():
# Start webcam
    cap = cv2.VideoCapture(0)

    model = joblib.load('model.pickle')
    model.prepare(ctx_id=0)
    celeb_embeddings_female = joblib.load('cef.pickle')
    celeb_embeddings_male = joblib.load('cem.pickle')
    celeb_names_female = joblib.load('cnf.pickle')
    celeb_names_male = joblib.load('cnm.pickle')

    start_time = time.time()
    name_counts = defaultdict(int)

    while True:
        current_time = time.time()
        if current_time - start_time > 5:
            break

        ret, frame = cap.read()
        if not ret:
            break

        faces = model.get(frame)

        for face in faces:
            gender = "Male" if face.gender == 1 else "Female"

            (x1, y1, x2, y2) = face.bbox.astype(int)
            emb = face.embedding
            face_vector = emb.reshape(1, -1)

            if gender == "Male":
                all_vectors = np.array(celeb_embeddings_male)
                similarities = cosine_similarity(face_vector, all_vectors)[0]
                best_idx = np.argmax(similarities)
                name = celeb_names_male[best_idx]
            else:
                all_vectors = np.array(celeb_embeddings_female)
                similarities = cosine_similarity(face_vector, all_vectors)[0]
                best_idx = np.argmax(similarities)
                name = celeb_names_female[best_idx]

            name_counts[name] += 1

    cap.release()
    cv2.destroyAllWindows()

    most_frequent_name = max(name_counts, key=name_counts.get)
    return most_frequent_name

