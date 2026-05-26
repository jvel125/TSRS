/* ── Camera & face-api.js wrapper ───────────────────────────────────────── */

const MODELS_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.12/model';

const FaceEngine = {
  loaded: false,

  async loadModels() {
    if (this.loaded) return;
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODELS_URL),
      faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODELS_URL),
      faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL),
    ]);
    this.loaded = true;
  },

  async startCamera(videoEl) {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: 'user' },
      audio: false,
    });
    videoEl.srcObject = stream;
    await new Promise(resolve => { videoEl.onloadedmetadata = resolve; });
    await videoEl.play();
    return stream;
  },

  stopCamera(stream) {
    if (stream) stream.getTracks().forEach(t => t.stop());
  },

  detectionOptions() {
    return new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 });
  },

  async detectFace(videoEl) {
    return faceapi
      .detectSingleFace(videoEl, this.detectionOptions())
      .withFaceLandmarks(true)
      .withFaceDescriptor();
  },

  drawOverlay(canvasEl, videoEl, detection) {
    const dims = { width: videoEl.videoWidth, height: videoEl.videoHeight };
    faceapi.matchDimensions(canvasEl, dims);
    canvasEl.getContext('2d').clearRect(0, 0, canvasEl.width, canvasEl.height);
    if (!detection) return;

    const resized = faceapi.resizeResults(detection, dims);
    faceapi.draw.drawDetections(canvasEl, resized);
    faceapi.draw.drawFaceLandmarks(canvasEl, resized);
  },
};

/**
 * High-level scan session.  Calls onStatus(msg), onDescriptor(Float32Array) or onError(msg).
 *
 * Returns { stop } to cancel the loop.
 */
function createScanSession({ videoEl, canvasEl, ringEl, onStatus, onDescriptor, onError }) {
  let running = true;
  let noFaceCount = 0;
  let captureCount = 0;
  const REQUIRED_CAPTURES = 3;  // require N consecutive frames with a good detection
  const descriptors = [];

  async function loop() {
    while (running) {
      try {
        const detection = await FaceEngine.detectFace(videoEl);
        FaceEngine.drawOverlay(canvasEl, videoEl, detection);

        if (!detection) {
          noFaceCount++;
          if (noFaceCount > 20) onStatus('Position your face in the circle', 'warn');
          descriptors.length = 0;
          captureCount = 0;
        } else {
          noFaceCount = 0;
          const score = detection.detection.score;
          if (score < 0.7) {
            onStatus('Move to better lighting…', 'info');
            descriptors.length = 0;
          } else {
            captureCount++;
            descriptors.push(Array.from(detection.descriptor));
            onStatus(`Scanning… ${Math.min(100, Math.round((captureCount / REQUIRED_CAPTURES) * 100))}%`, 'scanning');

            if (captureCount >= REQUIRED_CAPTURES) {
              running = false;
              // Average the descriptors for robustness
              const avg = descriptors[0].map((_, i) =>
                descriptors.reduce((s, d) => s + d[i], 0) / descriptors.length
              );
              onDescriptor(avg);
              return;
            }
          }
        }
      } catch (err) {
        onError(err.message || 'Camera error');
        return;
      }
      await new Promise(r => setTimeout(r, 150));
    }
  }

  loop();
  return { stop: () => { running = false; } };
}
