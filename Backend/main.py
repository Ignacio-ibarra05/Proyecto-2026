# backend/main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import mediapipe as mp
import cv2
import numpy as np
from io import BytesIO

app = FastAPI()

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=2,
    enable_segmentation=False,
    min_detection_confidence=0.5
)

@app.post("/api/detect-pose")
async def detect_pose(file: UploadFile = File(...)):
    # Leer imagen
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Procesar con MediaPipe
    results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    if not results.pose_world_landmarks:
        return {"error": "No se detectó ninguna persona en la imagen"}
    
    # Extraer landmarks 3D
    landmarks = []
    for idx, landmark in enumerate(results.pose_world_landmarks.landmark):
        landmarks.append({
            "id": idx,
            "x": landmark.x,
            "y": landmark.y,
            "z": landmark.z,
            "visibility": landmark.visibility
        })
    
    # Definir conexiones (huesos)
    connections = [
        [conn[0], conn[1]] for conn in mp_pose.POSE_CONNECTIONS
    ]
    
    return {
        "landmarks": landmarks,
        "connections": connections,
        "success": True
    }

@app.get("/")
def read_root():
    return {"message": "API de detección de pose 3D funcionando"}
