import { UnityCanvas } from "./unity_canvas.js";
import { Vision } from "./perception/vision.js";
import { Audition } from "./perception/audio.js";

export class Agent extends EventTarget  {
    constructor(containerID, name) {
        super();
        this.name = name;
        this.container = document.getElementById(containerID);

        console.log("Loading Spoon Canvas");
        this.unityCanvas = new UnityCanvas(this.container, `${this.name}_3DContent`, false);
    
        window.addEventListener("WorldEventOnCreated", (e) => {
            console.log("World is loaded and ready to be used");
            this.unityCanvas.forwardCursorToUnity();
            
            //Making Myline the right size and out of scren
            this.unityCanvas.nativeBridge.world_CreateOrUpdateEntity(
                name,
                null,
                "ThreeD",
                { x: 0.0, y: 0.0, z: 10.0 },
                { x: 5.0, y: 5.0, z: 5.0 },
                { x: 0.0, y: 0.0, z: 0.0 },
            );

            //Create the cursor
            this.unityCanvas.nativeBridge.world_CreateOrUpdateEntity(
                "Cursor",
                "Generic3D",
                "ThreeD",
                { x: 0.0, y: 0.0, z: 0.0 },
                { x: 0.05, y: 0.05, z: 0.05 },
                { x: 0.0, y: 0.0, z: 0.0 },
            );
            //this.unityCanvas.nativeBridge.entity_LookAt_Target(name, "Cursor");
            //TODO Fix broken head rotation
            //this.unityCanvas.forwardCursorToUnity();

            //Create a navigation target
            this.unityCanvas.nativeBridge.world_CreateOrUpdateEntity(
                "NavigationTarget",
                "Generic3D",
                "ThreeD",
                { x: 0.0, y: 0.0, z: -5.0 },
                { x: 0.05, y: 0.05, z: 0.05 },
                { x: 0.0, y: 0.0, z: 0.0 },
            );
            this.unityCanvas.nativeBridge.entity_MoveTo_Target(name, "NavigationTarget");

            //Giving eyes and hears to the agent   
            this.vision = new Vision();
            this.audition = new Audition();
            this.audition.addEventListener("audition-asr-result", this.onHeard.bind(this));
            document.the_book.agents[name] = this;
        });
    }

    toggleHears() {
        return this.audition.toggleRecognition();
    }

    toggleEyes() {
        this.vision.initialize();
    }

    onHeard(evt) {
        const text = evt.detail.transcript;
        console.log(`${this.name} heard: ${text}`);
        const fwdEvt = new CustomEvent("agent-heard", { detail: { agent: this.name, sentence: text } });
        this.dispatchEvent(fwdEvt);
    }

    say(text) {
        this.unityCanvas.nativeBridge.entity_Say(this.name, text);
        const evt = new CustomEvent("agent-said", {detail : { agent: this.name, sentence: text }});
        this.dispatchEvent(evt);
    }
}