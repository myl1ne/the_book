import "https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"
import { NativeBridge } from "./native_bridge.js"

export class UnityCanvas {

    constructor(parentElement, containerId, is_development = false) {
        // Config (which could be passed as parameter)
        this.config = {};

        //Find the "local domain" where the script is executed
        this.config.executionUrl = new URL(import.meta.url);

        //Config that could come from Unity Build
        this.config.projectName = "unity";
        this.config.companyName = "Ghostless Shell";
        this.config.productName = "The Book";
        this.config.productVersion = "0.1";
        
        this.config.buildUrl = "static/unity/Build";

        this.config.dataUrl = this.config.buildUrl + "/"+this.config.projectName+".data"+(is_development?"":".gz");
        this.config.frameworkUrl = this.config.buildUrl + "/"+this.config.projectName+".framework.js"+(is_development?"":".gz");
        this.config.codeUrl = this.config.buildUrl + "/"+this.config.projectName+".wasm"+(is_development?"":".gz");
        this.config.streamingAssetsUrl = this.config.executionUrl.origin + "/StreamingAssets";
        this.config.loaderUrl = this.config.buildUrl + "/"+this.config.projectName+".loader.js";

        //Main container for overlay
        this.parentElement = parentElement;
        this.applyStyles();

        //Canvas for loading the Unity solution
        this.unityCanvas = document.createElement('canvas');
        this.unityCanvas.id = `${containerId}-UnityCanvas`;
        this.unityCanvas.style.width = "100%";
        this.unityCanvas.style.height = "100%";
        this.unityCanvas.style.position = "absolute";
        this.unityCanvas.style.top = "0";
        this.unityCanvas.style.left = "0";
        this.unityCanvas.style.opacity = "0";
        this.parentElement.appendChild(this.unityCanvas);

        this.mainScript = document.createElement("script");
        this.mainScript.src = this.config.loaderUrl;
        this.mainScript.onload = () => {
            createUnityInstance(this.unityCanvas, this.config, (progress) => {
                //progressBarFull.style.width = 100 * progress + "%";
            }).then((unityInstance) => {
                this.unityInstance = unityInstance;

                setTimeout(() => {
                    this.unityCanvas.classList.remove("fade-out");
                    this.unityCanvas.classList.add("fade-in");
                },
                2500);

                // Instantiate the NativeBridge
                this.nativeBridge = new NativeBridge(this.unityInstance);

                // Detect DOM changes so we can destroy the canvas if it's removed
                this.initDOMObserver();

                 const serializedEvent = new CustomEvent("SpoonCanvasLoaded", {
                    detail: {
                        canvas: this
                    }
                });
                window.dispatchEvent(serializedEvent);

            }).catch((message) => {
                alert(message);
            });            
        }
        this.onMouseMove = this.onMouseMove.bind(this);
        this.parentElement.appendChild(this.mainScript);
    }

    applyStyles() {
        const style = document.createElement("style");
        style.textContent = `
          .fade-in {
            animation: fadeIn 1s ease-in forwards;
          }
          
          .fade-out {
            animation: fadeOut 1s ease-out forwards;
          }
          
          @keyframes fadeIn {
            0% {
              opacity: 0;
            }
            100% {
              opacity: 1;
            }
          }
          
          @keyframes fadeOut {
            0% {
              opacity: 1;
            }
            100% {
              opacity: 0;
            }
          }
          `;
        this.parentElement.appendChild(style);
    }

    initDOMObserver() {
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    if (
                        Array.from(mutation.removedNodes).includes(this.unityCanvas) ||
                        Array.from(mutation.removedNodes).some((node) => node.contains && node.contains(this.unityCanvas))
                    ) {
                        
                        //The canvas has been removed from DOM but unity is still running
                        //We save it until Quit is called
                        console.log("Unity Canvas removed from DOM...");
                        this.unityCanvas.style.display = "None";
                        document.body.appendChild(this.unityCanvas);
                        this.destroy();
                    }
                }
            });
        });
      
        this.observer.observe(document, { childList: true, subtree: true });
    }

    destroy() {
        console.log("Destroying SpoonCanvas: " + this.unityCanvas.id);
        console.log("Removing Listeners");
        document.removeEventListener("mousemove", this.onMouseMove);
        if (this.observer) {
            this.observer.disconnect();
        }
        
        console.log("Quitting Unity (commented out for now)");
        /*
        this.unityInstance.Quit().then(function() {
            console.log("Unity quitted!");
            document.body.removeChild(this.unityCanvas);
        });
        */
    }  
    
    update() {
        // We can store periodic logic here
    }

    onMouseMove(e) {
        const inWorldWidth = 100.0;
        const inWorldHeight = 30.0;

        // On comment below: camera position depends on the scene, so we need to get it from Unity

        //camera is at 0, 1.94, -15.66 in Unity, adding that to the position of the cursor
        // In theory we could read the camera position / rotation and apply it to the formula
        // const cameraPosition = this.nativeBridge.world_GetCameraPosition();
        // const cameraRotation = this.nativeBridge.world_GetCameraRotation();
        // const cursorPosition = new THREE.Vector3(
        //    inWorldWidth * (-0.5 + (e.pageX / $(window).width())),
        //    -1 * inWorldHeight * (-0.5 + (e.pageY / $(window).height())),
        //    0
        //);
        //cursorPosition.applyQuaternion(cameraRotation);
        //cursorPosition.add(cameraPosition);

        this.nativeBridge.world_CreateOrUpdateEntity(
            "Cursor",
            null,
            "ThreeD",
            {
                x: inWorldWidth * (-0.5 + (e.pageX / $(window).width())),
                y: 1.94 + -1 * inWorldHeight * (-0.5 + (e.pageY / $(window).height())),
                z: -26.0
            },
            {
                x: 0.1,
                y: 0.1,
                z: 0.1
            }
        );
    }

    //Listen to broswer events of interest (e.g mouse move) and forward those to unity
    forwardCursorToUnity() {
        document.addEventListener("mousemove", this.onMouseMove);
    }
}