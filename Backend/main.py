# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pose Detection API",
    description="API para detección de pose 3D usando MediaPipe",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar MediaPipe Tasks API (nueva versión)
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Inicializar el detector de pose
try:
    BaseOptions = python.BaseOptions
    PoseLandmarker = vision.PoseLandmarker
    PoseLandmarkerOptions = vision.PoseLandmarkerOptions
    VisionRunningMode = vision.RunningMode

    # Crear opciones
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path='https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task'
        ),
        running_mode=VisionRunningMode.IMAGE,
        num_poses=1
    )

    detector = PoseLandmarker.create_from_options(options)
    logger.info("✓ MediaPipe detector inicializado correctamente")
    
except Exception as e:
    logger.error(f"Error inicializando MediaPipe: {e}")
    detector = None

# Conexiones de pose (definidas manualmente)
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5),
    (5, 6), (6, 8), (9, 10), (11, 12), (11, 13),
    (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
    (18, 20), (11, 23), (12, 24), (23, 24), (23, 25),
    (24, 26), (25, 27), (26, 28), (27, 29), (28, 30),
    (29, 31), (30, 32), (27, 31), (28, 32)
]

MAX_FILE_SIZE = 10 * 1024 * 1024

@app.get("/")
def read_root():
    return {
        "message": "API de detección de pose 3D funcionando",
        "status": "online",
        "version": "1.0.0",
        "detector_ready": detector is not None
    }

@app.get("/health")
def health_check():
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector no inicializado")
    return {"status": "healthy", "detector": "ready"}

@app.post("/api/detect-pose")
async def detect_pose(file: UploadFile = File(...)):
    """
    Detecta la pose de una persona en una imagen y retorna landmarks 3D
    """
    
    if detector is None:
        raise HTTPException(
            status_code=503,
            detail="El detector de pose no está disponible"
        )
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail="El archivo debe ser una imagen (JPG, PNG, etc.)"
        )
    
    try:
        # Leer imagen
        contents = await file.read()
        
        # Validar tamaño
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"La imagen es demasiado grande. Máximo 10MB"
            )
        
        # Decodificar imagen
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="No se pudo decodificar la imagen. Formato inválido."
            )
        
        logger.info(f"Procesando imagen: {file.filename}, Shape: {image.shape}")
        
        # Convertir BGR a RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Crear MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Detectar pose
        detection_result = detector.detect(mp_image)
        
        # Verificar si se detectó alguna pose
        if not detection_result.pose_world_landmarks or len(detection_result.pose_world_landmarks) == 0:
            return {
                "success": False,
                "error": "No se detectó ninguna persona en la imagen",
                "tip": "Asegúrate de que la imagen tenga una persona visible de cuerpo completo"
            }
        
        # Extraer landmarks 3D de la primera persona detectada
        landmarks = []
        world_landmarks = detection_result.pose_world_landmarks[0]
        
        for idx, landmark in enumerate(world_landmarks):
            landmarks.append({
                "id": idx,
                "x": float(landmark.x),
                "y": float(landmark.y),
                "z": float(landmark.z),
                "visibility": float(landmark.visibility) if hasattr(landmark, 'visibility') else 1.0
            })
        
        # Convertir conexiones
        connections = [[int(conn[0]), int(conn[1])] for conn in POSE_CONNECTIONS]
        
        logger.info(f"✓ Pose detectada: {len(landmarks)} landmarks")
        
        return {
            "success": True,
            "landmarks": landmarks,
            "connections": connections,
            "total_landmarks": len(landmarks),
            "image_dimensions": {
                "width": image.shape[1],
                "height": image.shape[0]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando imagen: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

@app.on_event("shutdown")
def shutdown_event():
    """Cerrar recursos al apagar"""
    try:
        if detector:
            detector.close()
        logger.info("Recursos cerrados correctamente")
    except:
        pass
