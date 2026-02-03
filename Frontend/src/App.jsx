// frontend/src/App.jsx
import { useState } from 'react';
import Skeleton3D from './components/Skeleton3D';
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
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/detect-pose', {
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
      setError('Error de conexión con el servidor');
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
          
          {loading && <p className="status">Procesando imagen...</p>}
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
              <p className="hint">💡 Arrastra para rotar, scroll para zoom</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
