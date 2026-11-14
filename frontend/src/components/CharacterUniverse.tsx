import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { CharacterState } from '../types';

interface CharacterUniverseProps {
  state: CharacterState;
  audioLevel: number;
}

interface AvatarRig {
  root: THREE.Group;
  head: THREE.Group;
  eyes: THREE.Group[];
  brows: THREE.Mesh[];
  mouth: THREE.Mesh;
  arms: THREE.Group[];
  blinkAt: number;
  blinkFor: number;
}

const standard = (color: number, roughness = 0.72, metalness = 0) =>
  new THREE.MeshStandardMaterial({ color, roughness, metalness });

function makeBhoomi(): AvatarRig {
  const root = new THREE.Group();
  root.position.y = -0.75;

  const sari = standard(0x456f51, 0.82);
  const skin = standard(0xb87555, 0.84);
  const hair = standard(0x211c19, 0.74);
  const gold = standard(0xc69a4f, 0.42, 0.32);

  const torso = new THREE.Mesh(new THREE.SphereGeometry(0.78, 40, 28), sari);
  torso.position.set(0, 0.58, 0);
  torso.scale.set(1.13, 0.78, 0.62);
  torso.castShadow = true;
  root.add(torso);

  const blouse = new THREE.Mesh(new THREE.SphereGeometry(0.56, 32, 24), standard(0x2d523a, 0.78));
  blouse.position.set(0, 1.03, 0);
  blouse.scale.set(0.94, 0.57, 0.58);
  blouse.castShadow = true;
  root.add(blouse);

  const drapeShape = new THREE.Shape();
  drapeShape.moveTo(-0.49, 1.46);
  drapeShape.bezierCurveTo(-0.18, 1.32, 0.14, 1.21, 0.5, 1.06);
  drapeShape.bezierCurveTo(0.38, 0.82, 0.13, 0.44, -0.18, 0.1);
  drapeShape.bezierCurveTo(-0.39, 0.25, -0.53, 0.77, -0.49, 1.46);
  const drape = new THREE.Mesh(
    new THREE.ShapeGeometry(drapeShape, 24),
    new THREE.MeshStandardMaterial({ color: 0x739366, roughness: 0.88, side: THREE.DoubleSide }),
  );
  drape.position.z = 0.49;
  drape.castShadow = true;
  root.add(drape);

  const borderCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.49, 1.44, 0.51),
    new THREE.Vector3(-0.15, 1.28, 0.52),
    new THREE.Vector3(0.25, 1.15, 0.52),
    new THREE.Vector3(0.48, 1.04, 0.51),
    new THREE.Vector3(0.34, 0.63, 0.51),
    new THREE.Vector3(-0.18, 0.12, 0.51),
  ]);
  root.add(new THREE.Mesh(new THREE.TubeGeometry(borderCurve, 36, 0.018, 8, false), gold));

  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.22, 0.43, 28), skin);
  neck.position.set(0, 1.48, 0.02);
  neck.castShadow = true;
  root.add(neck);

  const head = new THREE.Group();
  head.position.set(0, 2.12, 0.03);
  root.add(head);
  const face = new THREE.Mesh(new THREE.SphereGeometry(0.62, 48, 36), skin);
  face.scale.set(0.84, 1.08, 0.78);
  face.castShadow = true;
  head.add(face);

  const jaw = new THREE.Mesh(new THREE.SphereGeometry(0.42, 36, 28), skin);
  jaw.position.set(0, -0.31, 0.06);
  jaw.scale.set(0.82, 0.55, 0.74);
  head.add(jaw);

  const hairCap = new THREE.Mesh(new THREE.SphereGeometry(0.64, 40, 28, 0, Math.PI * 2, 0, Math.PI * 0.4), hair);
  hairCap.position.set(0, 0.09, -0.04);
  hairCap.scale.set(0.98, 1.08, 0.94);
  hairCap.castShadow = true;
  head.add(hairCap);
  const backHair = new THREE.Mesh(new THREE.SphereGeometry(0.53, 32, 24), hair);
  backHair.position.set(0, -0.24, -0.28);
  backHair.scale.set(1.1, 1.13, 0.68);
  head.add(backHair);
  for (const side of [-1, 1]) {
    const lock = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.42, 5, 12), hair);
    lock.position.set(side * 0.47, -0.08, 0.02);
    lock.rotation.z = side * -0.08;
    head.add(lock);
  }

  const eyes: THREE.Group[] = [];
  const brows: THREE.Mesh[] = [];
  for (const x of [-0.19, 0.19]) {
    const eye = new THREE.Group();
    eye.position.set(x, 0.04, 0.46);
    const white = new THREE.Mesh(new THREE.SphereGeometry(0.066, 22, 16), standard(0xfaf5eb, 0.44));
    white.scale.set(1.12, 0.68, 0.3);
    eye.add(white);
    const iris = new THREE.Mesh(new THREE.SphereGeometry(0.032, 18, 14), standard(0x55372b, 0.36));
    iris.position.set(0, -0.005, 0.023);
    eye.add(iris);
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.015, 14, 10), standard(0x171311, 0.28));
    pupil.position.set(0, -0.003, 0.043);
    eye.add(pupil);
    const glint = new THREE.Mesh(new THREE.SphereGeometry(0.006, 10, 8), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    glint.position.set(-0.01, 0.011, 0.054);
    eye.add(glint);
    eyes.push(eye);
    head.add(eye);

    const brow = new THREE.Mesh(new THREE.CapsuleGeometry(0.016, 0.13, 3, 10), hair);
    brow.position.set(x, 0.15, 0.47);
    brow.rotation.z = x < 0 ? -0.11 : 0.11;
    brows.push(brow);
    head.add(brow);
  }

  for (const side of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.SphereGeometry(0.115, 20, 16), skin);
    ear.position.set(side * 0.51, -0.02, 0.01);
    ear.scale.set(0.55, 0.9, 0.56);
    head.add(ear);
    const earring = new THREE.Mesh(new THREE.SphereGeometry(0.046, 16, 12), gold);
    earring.position.set(side * 0.52, -0.2, 0.08);
    head.add(earring);
  }

  const noseBridge = new THREE.Mesh(new THREE.CapsuleGeometry(0.052, 0.14, 4, 12), skin);
  noseBridge.position.set(0, -0.07, 0.475);
  head.add(noseBridge);
  const noseTip = new THREE.Mesh(new THREE.SphereGeometry(0.067, 18, 14), skin);
  noseTip.position.set(0, -0.18, 0.51);
  noseTip.scale.set(0.86, 0.72, 0.7);
  head.add(noseTip);
  for (const side of [-1, 1]) {
    const nostril = new THREE.Mesh(new THREE.SphereGeometry(0.018, 12, 8), standard(0x754532));
    nostril.position.set(side * 0.035, -0.215, 0.54);
    head.add(nostril);
  }

  const mouth = new THREE.Mesh(
    new THREE.SphereGeometry(0.108, 24, 16),
    new THREE.MeshStandardMaterial({ color: 0x783c3b, roughness: 0.48 }),
  );
  mouth.position.set(0, -0.35, 0.45);
  mouth.scale.set(0.8, 0.15, 0.3);
  head.add(mouth);
  const lowerLip = new THREE.Mesh(new THREE.SphereGeometry(0.066, 18, 12), standard(0xa85d57, 0.52));
  lowerLip.position.set(0, -0.388, 0.45);
  lowerLip.scale.set(0.78, 0.33, 0.22);
  head.add(lowerLip);

  const bindi = new THREE.Mesh(
    new THREE.SphereGeometry(0.027, 14, 10),
    new THREE.MeshStandardMaterial({ color: 0x9b3d31, roughness: 0.38 }),
  );
  bindi.position.set(0, 0.3, 0.46);
  head.add(bindi);

  const necklaceCurve = new THREE.EllipseCurve(0, 0, 0.36, 0.2, Math.PI * 0.08, Math.PI * 0.92, false, 0);
  const necklacePoints = necklaceCurve.getPoints(48).map((point) => new THREE.Vector3(point.x, point.y + 1.18, 0.48));
  root.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(necklacePoints), 48, 0.015, 6, false), gold));

  const arms: THREE.Group[] = [];
  for (const side of [-1, 1]) {
    const arm = new THREE.Group();
    arm.position.set(side * 0.76, 0.9, 0);
    const sleeve = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.46, 5, 16), standard(0x3c6747));
    sleeve.position.set(side * 0.12, -0.26, 0);
    sleeve.rotation.z = side * -0.2;
    sleeve.castShadow = true;
    arm.add(sleeve);
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.14, 18, 14), skin);
    hand.position.set(side * 0.18, -0.58, 0.04);
    arm.add(hand);
    root.add(arm);
    arms.push(arm);
  }

  const necklacePendant = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 12), gold);
  necklacePendant.position.set(0, 0.98, 0.49);
  root.add(necklacePendant);

  return { root, head, eyes, brows, mouth, arms, blinkAt: 2.5, blinkFor: 0 };
}

export const CharacterUniverse: React.FC<CharacterUniverseProps> = ({ state, audioLevel }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ state, audioLevel });
  const [webGlFailed, setWebGlFailed] = React.useState(false);
  stateRef.current = { state, audioLevel };

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = canvas?.parentElement;
    if (!canvas || !container) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
      });
    } catch {
      setWebGlFailed(true);
      return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(29, 1, 0.1, 40);
    camera.position.set(0, 1.65, 6.7);
    camera.lookAt(0, 1.28, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.12;
    renderer.setClearColor(0x000000, 0);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    scene.add(new THREE.HemisphereLight(0xfff0da, 0x53463c, 2.0));

    const keyLight = new THREE.DirectionalLight(0xffe6c6, 3.2);
    keyLight.position.set(-3.7, 6, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);
    const fillLight = new THREE.PointLight(0xf4c994, 18, 12);
    fillLight.position.set(3.2, 2.7, 4);
    scene.add(fillLight);
    const rimLight = new THREE.PointLight(0xb3c98f, 12, 12);
    rimLight.position.set(-3, 2.5, -2);
    scene.add(rimLight);

    const avatar = makeBhoomi();
    scene.add(avatar.root);

    const resize = () => {
      const width = Math.max(container.clientWidth, 1);
      const height = Math.max(container.clientHeight, 1);
      camera.aspect = width / height;
      camera.position.z = width < 600 ? 7.2 : 5.9;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    resize();

    const clock = new THREE.Clock();
    let frameId = 0;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.elapsedTime;
      const current = stateRef.current;
      const active = current.state !== 'idle';

      avatar.root.position.y = -0.75 + Math.sin(elapsed * 1.15) * 0.025;
      avatar.head.rotation.x = current.state === 'thinking' ? -0.055 : current.state === 'listening' ? 0.035 : 0;
      avatar.head.rotation.y = Math.sin(elapsed * 0.4) * 0.055;
      avatar.head.rotation.z = current.state === 'listening' ? 0.03 : Math.sin(elapsed * 0.28) * 0.012;
      avatar.brows.forEach((brow, index) => {
        brow.position.y = 0.15 + (current.state === 'listening' ? 0.018 : current.state === 'thinking' && index === 0 ? 0.025 : 0);
      });
      avatar.mouth.scale.y = current.state === 'speaking'
        ? 0.15 + Math.min(Math.max(current.audioLevel, 0), 0.65) * 0.62
        : 0.15;
      avatar.arms[0].rotation.z = Math.sin(elapsed * 0.7) * 0.025;
      avatar.arms[1].rotation.z = current.state === 'speaking'
        ? -0.12 - Math.sin(elapsed * 2.4) * 0.11
        : Math.sin(elapsed * 0.6) * 0.018;

      if (elapsed > avatar.blinkAt) avatar.blinkFor = 0.16;
      if (avatar.blinkFor > 0) {
        const blink = Math.sin(Math.min(avatar.blinkFor / 0.16, 1) * Math.PI);
        avatar.eyes.forEach((eye) => { eye.scale.y = Math.max(0.12, 1 - blink * 0.86); });
        avatar.blinkFor -= delta;
        if (avatar.blinkFor <= 0) {
          avatar.blinkAt = elapsed + 2.2 + Math.random() * 3.2;
          avatar.eyes.forEach((eye) => { eye.scale.y = 1; });
        }
      }

      const breathing = Math.sin(elapsed * 1.25) * 0.012;
      avatar.root.scale.set(1 + breathing, 1 + breathing + (active ? 0.006 : 0), 1 + breathing);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((item) => item.dispose());
        }
      });
      renderer.dispose();
    };
  }, []);

  return (
    <>
      <canvas ref={canvasRef} className="character-universe-canvas" aria-label="Animated portrait of Bhoomi" role="img" />
      {webGlFailed && (
        <div className="avatar-fallback" role="img" aria-label="Illustrated portrait of Bhoomi">
          <div className="fallback-hair" />
          <div className="fallback-face">
            <i className="fallback-eye fallback-eye-left" />
            <i className="fallback-eye fallback-eye-right" />
            <i className="fallback-nose" />
            <i className="fallback-mouth" />
            <i className="fallback-bindi" />
          </div>
          <div className="fallback-sari" />
        </div>
      )}
    </>
  );
};
