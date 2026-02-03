// frontend/src/components/Skeleton3D.jsx
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

export default function Skeleton3D({ poseData }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !poseData) return;

    // Setup básico de Three.js
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      75,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(
      containerRef.current.clientWidth,
      containerRef.current.clientHeight
    );
    containerRef.current.appendChild(renderer.domElement);

    // Controles de órbita
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    // Iluminación
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    // Crear esqueleto
    createSkeleton(scene, poseData);

    // Animación
    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    // Cleanup
    return () => {
      if (containerRef.current && renderer.domElement) {
        containerRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [poseData]);

  function createSkeleton(scene, data) {
    const { landmarks, connections } = data;

    // Crear esferas para las articulaciones
    const jointGeometry = new THREE.SphereGeometry(0.02, 16, 16);
    const jointMaterial = new THREE.MeshStandardMaterial({ 
      color: 0xffffff,
      emissive: 0x444444
    });

    landmarks.forEach((landmark) => {
      if (landmark.visibility > 0.5) {
        const joint = new THREE.Mesh(jointGeometry, jointMaterial);
        joint.position.set(landmark.x, -landmark.y, -landmark.z);
        scene.add(joint);
      }
    });

    // Crear cilindros para los huesos
    connections.forEach(([startIdx, endIdx]) => {
      const start = landmarks[startIdx];
      const end = landmarks[endIdx];

      if (start.visibility > 0.5 && end.visibility > 0.5) {
        const startVec = new THREE.Vector3(start.x, -start.y, -start.z);
        const endVec = new THREE.Vector3(end.x, -end.y, -end.z);
        
        const direction = new THREE.Vector3().subVectors(endVec, startVec);
        const length = direction.length();
        
        const boneGeometry = new THREE.CylinderGeometry(0.01, 0.01, length, 8);
        const boneMaterial = new THREE.MeshStandardMaterial({ 
          color: 0xeeeeee 
        });
        const bone = new THREE.Mesh(boneGeometry, boneMaterial);
        
        bone.position.copy(startVec.clone().add(direction.clone().multiplyScalar(0.5)));
        bone.quaternion.setFromUnitVectors(
          new THREE.Vector3(0, 1, 0),
          direction.clone().normalize()
        );
        
        scene.add(bone);
      }
    });

    // Grid de referencia
    const gridHelper = new THREE.GridHelper(2, 10, 0x444444, 0x222222);
    scene.add(gridHelper);
  }

  return (
    <div 
      ref={containerRef} 
      style={{ width: '100%', height: '600px', borderRadius: '8px' }}
    />
  );
}
