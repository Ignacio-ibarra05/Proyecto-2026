import { useState } from 'react';
import Skeleton3D from './components/Skeleton3D';
import { API_URL } from './config';
import './App.css';

function App() {
  const [poseData, setPoseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Preview de la imagen
    const reader = new FileReader();
    reader.onload = (e) => setPreviewImage(e.target.result);
    reader.readAsDataURL(file);

    // Enviar al backend
    setLoading(true);
    setError(null);
    setPoseData(null);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/api/detect-pose`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.success) {
        setPoseData(data);
      } else {
        setError(data.error || 'Error al procesar la imagen');
      }
    } catch (err) {
      setError('Error de conexión con el servidor. Intenta de nuevo.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🎭 Generador de Esqueletos 3D</h1>
        <p>Sube una foto y genera un modelo 3D de la pose detectada</p>
      </header>

      <main>
        <div className="upload-section">
          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            id="file-input"
            style={{ display: 'none' }}
          />
          <label htmlFor="file-input" className="upload-button">
            📸 Seleccionar Imagen
          </label>
          
          {loading && (
            <div className="status">
              <div className="spinner"></div>
              <p>Procesando imagen...</p>
            </div>
          )}
          {error && <p className="error">{error}</p>}
        </div>

        <div className="content-grid">
          {previewImage && (
            <div className="preview-section">
              <h3>Imagen Original</h3>
              <img src={previewImage} alt="Preview" />
            </div>
          )}

          {poseData && (
            <div className="skeleton-section">
              <h3>Modelo 3D Generado</h3>
              <Skeleton3D poseData={poseData} />
              <p className="hint">💡 Arrastra para rotar • Scroll para zoom</p>
            </div>
          )}
        </div>

        {!previewImage && !loading && (
          <div className="instructions">
            <h3>📌 Instrucciones</h3>
            <ul>
              <li>Selecciona una imagen con una persona visible</li>
              <li>La imagen será procesada usando inteligencia artificial</li>
              <li>Se generará un modelo 3D interactivo de la pose</li>
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
