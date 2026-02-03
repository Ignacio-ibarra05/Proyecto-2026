import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

export default function Skeleton3D({ poseData }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const animationIdRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !poseData) return;

    // Limpiar escena anterior si existe
    if (rendererRef.current) {
      cancelAnimationFrame(animationIdRef.current);
      if (containerRef.current.contains(rendererRef.current.domElement)) {
        containerRef.current.removeChild(rendererRef.current.domElement);
      }
      rendererRef.current.dispose();
    }

    // Setup de Three.js
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      75,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(0, 0, 3);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(
      containerRef.current.clientWidth,
      containerRef.current.clientHeight
    );
    rendererRef.current = renderer;
    containerRef.current.appendChild(renderer.domElement);

    // Controles
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controlsRef.current = controls;

    // Iluminación
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    const backLight = new THREE.DirectionalLight(0x4444ff, 0.3);
    backLight.position.set(-5, 0, -5);
    scene.add(backLight);

    // Crear esqueleto
    createSkeleton(scene, poseData);

    // Grid de referencia
    const gridHelper = new THREE.GridHelper(2, 10, 0x444444, 0x222222);
    gridHelper.position.y = -1;
    scene.add(gridHelper);

    // Animación
    function animate() {
      animationIdRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    // Manejo de resize
    const handleResize = () => {
      if (!containerRef.current) return;
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationIdRef.current);
      if (containerRef.current && rendererRef.current?.domElement) {
        if (containerRef.current.contains(rendererRef.current.domElement)) {
          containerRef.current.removeChild(rendererRef.current.domElement);
        }
      }
      controls.dispose();
      renderer.dispose();
    };
  }, [poseData]);

  function createSkeleton(scene, data) {
    const { landmarks, connections } = data;

    // Material para articulaciones
    const jointMaterial = new THREE.MeshStandardMaterial({ 
      color: 0xffffff,
      emissive: 0x666666,
      metalness: 0.3,
      roughness: 0.7
    });

    // Material para huesos
    const boneMaterial = new THREE.MeshStandardMaterial({ 
      color: 0xeeeeee,
      metalness: 0.2,
      roughness: 0.8
    });

    // Crear articulaciones
    const jointGeometry = new THREE.SphereGeometry(0.03, 16, 16);
    
    landmarks.forEach((landmark) => {
      if (landmark.visibility > 0.5) {
        const joint = new THREE.Mesh(jointGeometry, jointMaterial);
        joint.position.set(landmark.x, -landmark.y, -landmark.z);
        scene.add(joint);
      }
    });

    // Crear huesos (conexiones)
    connections.forEach(([startIdx, endIdx]) => {
      const start = landmarks[startIdx];
      const end = landmarks[endIdx];

      if (start.visibility > 0.5 && end.visibility > 0.5) {
        const startVec = new THREE.Vector3(start.x, -start.y, -start.z);
        const endVec = new THREE.Vector3(end.x, -end.y, -end.z);
        
        const direction = new THREE.Vector3().subVectors(endVec, startVec);
        const length = direction.length();
        
        const boneGeometry = new THREE.CylinderGeometry(0.015, 0.015, length, 8);
        const bone = new THREE.Mesh(boneGeometry, boneMaterial);
        
        bone.position.copy(startVec.clone().add(direction.clone().multiplyScalar(0.5)));
        bone.quaternion.setFromUnitVectors(
          new THREE.Vector3(0, 1, 0),
          direction.clone().normalize()
        );
        
        scene.add(bone);
      }
    });
  }

  return (
    <div 
      ref={containerRef} 
      style={{ 
        width: '100%', 
        height: '600px', 
        borderRadius: '12px',
        overflow: 'hidden'
      }}
    />
  );
}
