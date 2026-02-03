# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mediapipe as mp
import cv2
import numpy as np
from io import BytesIO
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pose Detection API",
    description="API para detección de pose 3D usando MediaPipe",
    version="1.0.0"
)

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio: ["https://tu-usuario.github.io"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=2,
    enable_segmentation=False,
    min_detection_confidence=0.5
)

# Tamaño máximo de archivo (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

@app.get("/")
def read_root():
    """Endpoint de health check"""
    return {
        "message": "API de detección de pose 3D funcionando",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Endpoint adicional para monitoreo"""
    return {"status": "healthy"}

@app.post("/api/detect-pose")
async def detect_pose(file: UploadFile = File(...)):
    """
    Detecta la pose de una persona en una imagen y retorna landmarks 3D
    
    Args:
        file: Imagen en formato JPG, PNG, etc.
    
    Returns:
        JSON con landmarks 3D y conexiones entre articulaciones
    """
    
    # Validar tipo de archivo
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
                detail=f"La imagen es demasiado grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Decodificar imagen
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="No se pudo decodificar la imagen. Asegúrate de que sea un formato válido."
            )
        
        # Log información de la imagen
        logger.info(f"Procesando imagen: {file.filename}, Tamaño: {image.shape}")
        
        # Procesar con MediaPipe
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
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
                "x": float(landmark.x),  # Asegurar que sean floats serializables
                "y": float(landmark.y),
                "z": float(landmark.z),
                "visibility": float(landmark.visibility)
            })
        
        # Definir conexiones (huesos)
        connections = [
            [int(conn[0]), int(conn[1])] for conn in mp_pose.POSE_CONNECTIONS
        ]
        
        logger.info(f"Pose detectada exitosamente: {len(landmarks)} landmarks")
        
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
        logger.error(f"Error procesando imagen: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al procesar la imagen: {str(e)}"
        )

@app.on_event("shutdown")
def shutdown_event():
    """Cerrar recursos al apagar el servidor"""
    pose.close()
    logger.info("API cerrada correctamente")
