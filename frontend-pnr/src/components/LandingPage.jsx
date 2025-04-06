import React, { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import popOff from '../assets/popOff.png';
import letsgo from '../assets/letsgo.png';

const LandingPage = () => {
  const canvasRef = useRef(null);
  const contextRef = useRef(null);
  const animationFrameRef = useRef(null);
  const [audioInitialized, setAudioInitialized] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const isHoveringRef = useRef(isHovering);
  const navigate = useNavigate();

  useEffect(() => {
    isHoveringRef.current = isHovering;
  }, [isHovering]);

  const waveParams = {
    backgroundColor: '#ffffff',
    barCount: 64,
    barWidth: 8,
    barSpacing: 2,
    barMinHeight: 2,
    noiseAmount: 0.3,
    glitchProbability: 0.1,
    glitchAmount: 1,
    showGrid: true,
    gridSize: 30,
    gridOpacity: 0.15,
    gridColor: '#888888',
    barDecay: 100,
    animationSpeed: 0.0001,
  };

  const normalColors = {
    primaryColor: '#FF5042',
    secondaryColor: '#FFEB3B',
    gradientStart: '#ffcc00',
    gradientEnd: '#ff0000',
  };

  const hoverColors = {
    primaryColor: '#00ffff',
    secondaryColor: '#ff00ff',
    gradientStart: '#FF00FF',
    gradientEnd: '#00F2F2',
  };

  const getCurrentWaveParams = () => {
    const currentParams = { ...waveParams };
    if (isHoveringRef.current) {
      currentParams.primaryColor = hoverColors.primaryColor;
      currentParams.secondaryColor = hoverColors.secondaryColor;
      currentParams.gradientStart = hoverColors.gradientStart;
      currentParams.gradientEnd = hoverColors.gradientEnd;
    } else {
      currentParams.primaryColor = normalColors.primaryColor;
      currentParams.secondaryColor = normalColors.secondaryColor;
      currentParams.gradientStart = normalColors.gradientStart;
      currentParams.gradientEnd = normalColors.gradientEnd;
    }
    return currentParams;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext('2d', { willReadFrequently: true });
    contextRef.current = context;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const currentParams = getCurrentWaveParams();
    const barHeights = new Array(currentParams.barCount).fill(0);
    const targetBarHeights = new Array(currentParams.barCount).fill(0);

    const animateNoAudio = () => {
      const canvas = canvasRef.current;
      const context = contextRef.current;
      if (!canvas || !context) return;

      const params = getCurrentWaveParams();
      context.fillStyle = params.backgroundColor;
      context.fillRect(0, 0, canvas.width, canvas.height);

      if (params.showGrid) {
        drawGrid(context, canvas.width, canvas.height);
      }

      const now = Date.now() * 0.001;
      for (let i = 0; i < params.barCount; i++) {
        const normalizedPos = i / params.barCount;
        const centerBias = 1 - Math.abs((i - params.barCount / 2) / (params.barCount / 2));
        const edgeBoost = 1 + (1 - centerBias) * 1.5;
        const timeOffset = Math.sin(Date.now() * 0.0005 + i) * 0.01;
        let baseHeight = 0.15 + Math.sin(normalizedPos * Math.PI + timeOffset) * 0.2;
        let flickerAmount = 0.4 + baseHeight * 0.1;
        let randomFlicker = (Math.random() * flickerAmount - flickerAmount * 0.55) * edgeBoost;
        if (Math.random() < 0.1) randomFlicker *= 1.5;
        let value = Math.max(0.1, Math.min(1.0, baseHeight + randomFlicker));
        value *= edgeBoost;
        targetBarHeights[i] = value;
        barHeights[i] += (targetBarHeights[i] - barHeights[i]) * 0.03;
      }

      drawBars(context, canvas.width, canvas.height, barHeights, params);
      drawRetroEffects(context, canvas.width, canvas.height, now);

      if (Math.random() < params.glitchProbability) {
        applyGlitchEffect(context, canvas.width, canvas.height, params);
      }

      animationFrameRef.current = requestAnimationFrame(animateNoAudio);
    };

    animateNoAudio();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const drawGrid = (ctx, width, height) => {
    const currentParams = getCurrentWaveParams();
    ctx.strokeStyle = `rgba(136, 136, 136, ${currentParams.gridOpacity})`;
    ctx.lineWidth = 0.5;
    for (let x = 0; x < width; x += currentParams.gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += currentParams.gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  };

  const drawBars = (ctx, width, height, barHeights, params) => {
    const barCount = params.barCount;
    const totalSpacing = width * 0.05;
    const availableWidth = width - totalSpacing;
    const barWidth = availableWidth / barCount;
    const spacing = totalSpacing / (barCount - 1);
    const startX = 0;
    const barMaxHeight = height * 0.35;
    const bottomY = height;

    for (let i = 0; i < barCount; i++) {
      const x = startX + i * (barWidth + spacing);
      const amplitude = barHeights[i];
      const barHeight = Math.max(amplitude * barMaxHeight, params.barMinHeight);
      const grd = ctx.createLinearGradient(x, bottomY, x, bottomY - barHeight);
      grd.addColorStop(0, params.gradientEnd);
      grd.addColorStop(1, params.gradientStart);
      ctx.fillStyle = grd;
      ctx.fillRect(x, bottomY - barHeight, barWidth, barHeight);
      ctx.fillStyle = `${params.primaryColor}33`;
      ctx.fillRect(x - 1, bottomY - barHeight, barWidth + 2, barHeight + 2);
      ctx.fillStyle = `${params.secondaryColor}22`;
      ctx.fillRect(x, bottomY, barWidth, barHeight * 0.3);
    }
  };

  const drawRetroEffects = (ctx, width, height, time) => {
    ctx.fillStyle = 'rgba(200, 200, 200, 0.03)';
    for (let y = 0; y < height; y += 4) {
      ctx.fillRect(0, y, width, 1);
    }
    const gradient = ctx.createRadialGradient(
      width / 2, height / 2, height * 0.25,
      width / 2, height / 2, height
    );
    gradient.addColorStop(0, 'rgba(255, 255, 255, 0)');
    gradient.addColorStop(1, 'rgba(200, 200, 200, 0.4)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
  };

  const applyGlitchEffect = (ctx, width, height, params) => {
    const glitchType = Math.floor(Math.random() * 3);
    if (glitchType === 0) {
      const imageData = ctx.getImageData(0, 0, width, height);
      const data = imageData.data;
      const shiftAmount = Math.floor(Math.random() * params.glitchAmount);
      for (let y = 0; y < height; y++) {
        const rowOffset = y * width * 4;
        for (let x = 0; x < width; x++) {
          const offset = rowOffset + x * 4;
          if (x + shiftAmount < width) {
            data[offset] = data[offset + shiftAmount * 4];
          }
          if (x - shiftAmount >= 0) {
            data[offset + 2] = data[offset - shiftAmount * 4 + 2];
          }
        }
      }
      ctx.putImageData(imageData, 0, 0);
    }
  };

  // Changed this to navigate to "/fer" instead of "/livefeed"
  const navigateToFER = () => {
    if (!audioInitialized) {
      console.log('Audio initialized');
      setAudioInitialized(true);
    }
    navigate('/fer');
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 1 }}>
        <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: '100%' }} />
      </div>
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            cursor: 'pointer',
            filter: 'drop-shadow(0 0 10px rgba(102, 0, 255, 0.5))',
            transition: 'all 1s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
            transform: isHovering ? 'scale(1.1)' : 'scale(1)',
          }}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          onClick={navigateToFER} // Changed to navigateToFER
        >
          <img
            src={isHovering ? letsgo : popOff}
            alt={isHovering ? "Let's Go" : "Pop Off"}
            width="233"
            height="200"
          />
        </div>
      </div>
    </div>
  );
};

export default LandingPage;