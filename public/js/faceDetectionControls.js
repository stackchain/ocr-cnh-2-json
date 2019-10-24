const SSD_MOBILENETV1 = 'ssd_mobilenetv1'
const TINY_FACE_DETECTOR = 'tiny_face_detector'
const MTCNN = 'mtcnn'
const MODELS = '/models'

let selectedFaceDetector = SSD_MOBILENETV1

// ssd_mobilenetv1 options
let minConfidence = 0.01

// tiny_face_detector options
let inputSize = 240
let scoreThreshold = 0.5

//mtcnn options
let minFaceSize = 20

function getFaceDetectorOptions() {
  return selectedFaceDetector === SSD_MOBILENETV1
    ? new faceapi.SsdMobilenetv1Options({ minConfidence })
    : (
      selectedFaceDetector === TINY_FACE_DETECTOR
        ? new faceapi.TinyFaceDetectorOptions({ inputSize, scoreThreshold })
        : new faceapi.MtcnnOptions({ minFaceSize })
    )
}

async function loadFaceDetector() {
    new faceapi.SsdMobilenetv1Options({ minConfidence })
    await faceapi.nets.ssdMobilenetv1.load(MODELS);
    await faceapi.loadFaceLandmarkModel(MODELS);
    await faceapi.loadFaceRecognitionModel(MODELS);
}
