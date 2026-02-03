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

# Importar MediaPipe de forma correcta para versiones nuevas
try:
    # Intentar importar la API nueva primero
    from mediapipe.python.solutions import pose as mp_pose_module
    from mediapipe.python.solutions import drawing_utils as mp_drawing
    
    # Inicializar el detector
    pose_detector = mp_pose_module.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.5
    )
    
    # Obtener las conexiones
    POSE_CONNECTIONS = mp_pose_module.POSE_CONNECTIONS
    
    logger.info("MediaPipe cargado con API legacy (python.solutions)")
    
except (ImportError, AttributeError):
    logger.error("No se pudo cargar MediaPipe")
    raise

MAX_FILE_SIZE = 10 * 1024 * 1024

@app.get("/")
def read_root():
    return {
        "message": "API de detección de pose 3D funcionando",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/detect-pose")
async def detect_pose(file: UploadFile = File(...)):
    """
    Detecta la pose de una persona en una imagen y retorna landmarks 3D
    """
    
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
        
        # Procesar con MediaPipe
        results = pose_detector.process(image_rgb)
        
        if not results.pose_world_landmarks:
            return {
                "success": False,
                "error": "No se detectó ninguna persona en la imagen",
                "tip": "Asegúrate de que la imagen tenga una persona visible de cuerpo completo"
            }
        
        # Extraer landmarks 3D
        landmarks = []
        for idx, landmark in enumerate(results.pose_world_landmarks.landmark):
            landmarks.append({
                "id": idx,
                "x": float(landmark.x),
                "y": float(landmark.y),
                "z": float(landmark.z),
                "visibility": float(landmark.visibility)
            })
        
        # Definir conexiones (huesos)
        connections = [
            [int(conn[0]), int(conn[1])] for conn in POSE_CONNECTIONS
        ]
        
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
        pose_detector.close()
        logger.info("Recursos cerrados correctamente")
    except:
        pass
