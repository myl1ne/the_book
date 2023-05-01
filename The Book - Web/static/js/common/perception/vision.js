import "https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"
import "https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"
import {
    FaceDetector,
    GestureRecognizer,
    FilesetResolver
} from "https://cdn.skypack.dev/@mediapipe/tasks-vision@0.1.0-alpha-11";

export class Vision {
    constructor(detectFace = true, detectHands = true) {
        this.gestureRecognizer = GestureRecognizer;
        this.detectFace = detectFace;
        this.detectHands = detectHands;
    }

    async initialize(liveViewID, videoID, canvasID, gestureOutputID, webcamButtonID) {
        this.liveView = document.getElementById(liveViewID);
        this.video = document.getElementById(videoID);
        this.canvasElement = document.getElementById(canvasID);
        this.canvasCtx = this.canvasElement.getContext("2d");
        this.gestureOutput = document.getElementById(gestureOutputID);
        this.liveViewChildren = [];
        if (this.hasGetUserMedia()) {
            this.enableWebcamButton = document.getElementById(webcamButtonID);
            this.enableWebcamButton.addEventListener("click", (event) => { this.enableCam(event); });
          } else {
            console.warn("getUserMedia() is not supported by your browser");
        }       
        await this.loadModels();   
    }

    async loadModels() {
        this.vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.1.0-alpha-11/wasm");
        if (this.detectHands){
            console.log("GestureRecognizer loading");
            this.gestureRecognizer = await GestureRecognizer.createFromOptions(this.vision, {
                baseOptions: {
                    modelAssetPath: "https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/gesture_recognizer.task"
                },
                runningMode: "VIDEO"
            });
            console.log("GestureRecognizer loaded");
        }
        if (this.detectFace) {
            console.log("Face Detection loaded");
            this.faceDetector = await FaceDetector.createFromOptions(this.vision, {
                baseOptions: {
                modelAssetPath: `https://storage.googleapis.com/mediapipe-assets/face_detection_short_range.tflite?generation=1677044301978921`
                },
                runningMode: "VIDEO"
            });
            console.log("Face Detection loaded");
        }
        const modelLoadedEvent = new CustomEvent("SpoonVisionLoaded", {
            detail: {
              message: "The model has been loaded successfully.",
              // Add any additional data you need here
            },
          });
          document.dispatchEvent(modelLoadedEvent);
    };

    hasGetUserMedia() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    enableCam(event) {
        if (this.detectHands && !this.gestureRecognizer) {
          alert("Please wait for gestureRecognizer to load");
          return;
        }
        if (this.detectFace && !this.faceDetector) {
          alert("Please wait for faceDetector to load");
          return;
        }
      
        if (this.webcamRunning === true) {
            this.webcamRunning = false;
            this.enableWebcamButton.innerText = "📹 Turn on";
            this.enableWebcamButton.classList.remove("active");
        } else {
            this.webcamRunning = true;
            this.enableWebcamButton.innerText = "📹 Turn off";
            this.enableWebcamButton.classList.add("active");
        }
      
        // getUsermedia parameters.
        const constraints = {
          video: true
        };
      
        // Activate the webcam stream.
        navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
          this.video.srcObject = stream;
            this.video.addEventListener("loadeddata", (event) => {
                this.video.width = event.target.videoWidth;
                this.video.height = event.target.videoHeight;
                this.predictWebcam();
            });
        });
    }

    async predictWebcam() {
        this.webcamElement = document.getElementById("webcam");
        let nowInMs = Date.now();

        //Faces
        if (this.detectFace){
        const faces = this.faceDetector.detectForVideo(this.video, nowInMs).detections;
        this.displayFaceDetections(faces);
        }

        //Hands
        if (this.detectHands) {
            const hands = this.gestureRecognizer.recognizeForVideo(this.video, nowInMs);
            this.displayHandsDetections(hands);
        }

        // Call this function again to keep predicting when the browser is ready.
        if (this.webcamRunning === true) {
            window.requestAnimationFrame(() => { this.predictWebcam(); });
        }
    }

    displayFaceDetections(detections) {
        for (let child of this.liveViewChildren) {
            this.liveView.removeChild(child);
        }
        this.liveViewChildren.splice(0);
    
        // Iterate through predictions and draw them to the live view
        for (let detection of detections) {
            // Bounding Box
            const highlighter = document.createElement("div");
            highlighter.setAttribute("class", "highlighter");
            const scaleFactor = this.video.offsetWidth / this.video.width;
            //console.log(`scaleFactor=${scaleFactor}, canvasElement.offsetWidth=${this.canvasElement.offsetWidth}", canvasElement.width=${this.canvasElement.width}`);
            //console.log(`video.offsetWidth=${this.video.offsetWidth}, video.width=${this.video.width}`);
            highlighter.style.top = `${detection.boundingBox.originY * scaleFactor}px`;
            highlighter.style.left = `${
                this.video.offsetWidth -
                detection.boundingBox.width * scaleFactor -
                detection.boundingBox.originX * scaleFactor
            }px`;
            highlighter.style.width = `${(detection.boundingBox.width * scaleFactor - 10)}px`;
            highlighter.style.height = `${detection.boundingBox.height * scaleFactor}px`;
            this.liveView.appendChild(highlighter);
            this.liveViewChildren.push(highlighter);
    
            // Keypoints
            for (let keypoint of detection.keypoints) {
                const keypointEl = document.createElement("span");
                keypointEl.className = "key-point";
                keypointEl.style.top = `${keypoint.y * this.video.offsetHeight - 3}px`;
                keypointEl.style.left = `${this.video.offsetWidth-(keypoint.x * this.video.offsetWidth)  - 3}px`;
                this.liveView.appendChild(keypointEl);
                this.liveViewChildren.push(keypointEl);
            }
        }
    }

    displayHandsDetections(detections) {
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        if (detections.landmarks) {
          for (const landmarks of detections.landmarks) {
            drawConnectors(this.canvasCtx, landmarks, HAND_CONNECTIONS, {
              color: "#00FF00",
              lineWidth: 5
            });
            drawLandmarks(this.canvasCtx, landmarks, { color: "#FF0000", lineWidth: 2 });
          }
        }
        this.canvasCtx.restore();
        let gestureName = "None";
        if (detections.gestures.length > 0) {
          this.gestureOutput.style.display = "block";
          this.gestureOutput.style.width = this.videoWidth;
          gestureName = detections.gestures[0][0].categoryName;
          //const categoryScore = parseFloat(
          //  detections.gestures[0][0].score * 100
          //  ).toFixed(2);
        }
        this.gestureOutput.innerText = this.getEmojiForGesture(gestureName);
    }
    
    getEmojiForGesture(gestureName) {
        switch (gestureName) {
          case "None":
            return "❔";
          case "Closed_Fist":
            return "✊";
          case "Open_Palm":
            return "🖐️";
          case "Pointing_Up":
            return "☝️";
          case "Thumb_Down":
            return "👎";
          case "Thumb_Up":
            return "👍";
          case "Victory":
            return "✌️";
          case "ILoveYou":
            return "🤟";
          default:
            return "";
        }
      }
}