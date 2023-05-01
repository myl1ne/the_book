export class Audition extends EventTarget {
    constructor(language = "en") {
        super();
        this.recognition = null;
        this.recognizing = false;
        this.language = language;
    }

    initialize() {
        this.recognizing = false;
        return new Promise((resolve, reject) => {
            if ("webkitSpeechRecognition" in window) {
                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(stream => {
                        if (this.recognition != null) {
                            this.recognition.stop();
                            this.recognition = null;
                        }
                        this.recognition = new webkitSpeechRecognition();
                        this.recognition.continuous = true;
                        this.recognition.interimResults = true;
                        this.recognition.lang = this.language;

                        this.recognition.onresult = this.handleResult.bind(this);
                        this.recognition.onerror = this.handleError.bind(this);
                        this.recognition.onend = this.handleEnd.bind(this);
                        this.recognition.start();
                        this.recognizing = true;
                        resolve();
                    })
                    .catch(error => {
                        // Error occurred while requesting microphone access
                        console.error('Error accessing microphone:', error);
                        reject(error);
                    });
            } else {
                console.error('webkitSpeechRecognition not supported in this browser.');
                reject('webkitSpeechRecognition not supported in this browser.');
            }
        });
    }

    handleEnd(event) {
        console.log("ASR End: " + event);
    }

    handleError(event) {
        console.log("ASR Error: " + event.error);
    }

    handleResult(event) { 
        var final = "";
        var interim = "";
        for (var i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                final += event.results[i][0].transcript;

                this.isFinal = true;
                console.log("ASR Result: " + final);
                const evt = new CustomEvent("audition-asr-result", {
                    detail: {
                        isFinal : event.results[i].isFinal,
                        transcript : event.results[i][0].transcript,
                    }
                });
                this.dispatchEvent(evt);
                
                final = "";
                interim = "";
            } else {
                interim += event.results[i][0].transcript;
            }
        }
        console.log("ASR Result: " + interim);
    }

    isRecognizing() {
        return this.recognizing;
    }

    async toggleRecognition() {
        if (this.isRecognizing()) {
            await this.stopListening();
        } else {
            await this.startListening();
        }
        return this.isRecognizing();
    }

    async startListening() {
        await this.initialize();
    }

    async stopListening() {
        await this.recognition.stop();
        this.recognizing = false;
    }
}

