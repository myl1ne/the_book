import { getCurrentUser, user_writes } from "./firebase.js";
import { attractAttention } from "./effects.js";

const sceneImage = document.getElementById("scene-header-image");
const sceneTitle = document.getElementById("scene-header-title");
const sceneDaemonName = document.getElementById("scene-header-daemon-name");
const sceneText = document.getElementById("scene-text");
const sceneAnswerImgs = document.getElementById("scene-answer-images");
const sceneAnswerQuickReplies = document.getElementById("scene-answer-quick-replies");
const spinner = document.getElementById("loading-spinner");
const inputFormContainer = document.getElementById("scene-input"); 
const userInputText = document.getElementById("user-input");
const suggestionsBox = document.getElementById("autocomplete-suggestions");

export async function updateContent(imageUrl, title, daemonName, text, textType, delay = 100) {
    sceneImage.src = imageUrl;
    sceneTitle.innerHTML = title;
    sceneDaemonName.innerHTML = daemonName;
    sceneText.innerHTML = "";
  
    let currentTag = "";
    let currentText = "";
    let currentElement = sceneText;
    let wordElement;
  
    for (const character of text) {
      if (character === "<") {
        currentText = "";
        currentTag = "<";
      } else if (character === ">" && currentTag) {
        currentTag += ">";
        const tagMatch = currentTag.match(/<(\w+)>/);
  
        if (tagMatch) {
          const tagName = tagMatch[1];
          const tagElement = document.createElement(tagName);
          sceneText.appendChild(tagElement);
          currentElement = tagElement;
        }
  
        currentTag = "";
      } else if (currentTag) {
        currentTag += character;
      } else {
        if (character === " " || character === "\n") {
          if (wordElement) {
            await fadeInWord(wordElement, delay);
          }
          wordElement = document.createElement("span");
          sceneText.appendChild(wordElement);
          wordElement.classList.add("fade-in");
          wordElement.classList.add(textType);
          appendTextNode(wordElement, character);
        } else {
          currentText += character;
          if (!wordElement) {
            wordElement = document.createElement("span");
            sceneText.appendChild(wordElement);
            wordElement.classList.add("fade-in");
            wordElement.classList.add(textType);
          }
          appendTextNode(wordElement, character);
        }
      }
    }
    if (wordElement) {
      await fadeInWord(wordElement, delay);
    }
  }
  
  function appendTextNode(parent, character) {
    if (parent.lastChild && parent.lastChild.nodeType === Node.TEXT_NODE) {
      parent.lastChild.textContent += character;
    } else {
      parent.appendChild(document.createTextNode(character));
    }
  }
  
  function fadeInWord(wordElement, delay) {
    return new Promise((resolve) => {
      wordElement.addEventListener("animationend", () => {
        wordElement.classList.remove("fade-in");
        resolve();
      }, { once: true });
  
      setTimeout(() => {
        wordElement.style.animationDelay = "0s";
      }, delay);
    });
  }
function hideSpinner() {
    spinner.style.display = "none";
    inputFormContainer.style.display = "flex";
}

function showSpinner() {
    userInputText.value = "";
    sceneText.innerHTML = "";
    sceneAnswerImgs.innerHTML = "";
    sceneAnswerQuickReplies.innerHTML = "";
    inputFormContainer.style.display = "none";
    spinner.style.display = "block";
}

document.getElementById("user-input-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const user_input = document.getElementById("user-input");
    const currentUser = getCurrentUser();
    console.log(`User ${currentUser.uid} is submitting ${user_input.value}`);
    user_writes(user_input.value);
    // Disable input and show spinner
    showSpinner();
});

document.addEventListener("book-event-content-update", async (event) => {
    console.log("book-event-content-update caught:", event.detail);
    // Hide spinner
    hideSpinner();
    sceneAnswerImgs.innerHTML = "";
    sceneAnswerQuickReplies.innerHTML = "";

    // Check if we need the icons
    if (event.detail.creation_process_passed) {
        document.getElementById("icon-container").style.display = "flex";
        attractAttention("icon-container", "shadow");
    } else {
        document.getElementById("icon-container").style.display = "none";
    }
    // Parse daemon message
    let text = "";
    if (typeof event.detail.daemon_message === 'object') {
        if (event.detail.daemon_message.payload_type === "QUESTION") {
            text = event.detail.daemon_message.question;
            if (event.detail.daemon_message.options) {
                for (const choice of event.detail.daemon_message.options) {
                    const button = document.createElement("button");
                    button.innerHTML = choice;
                    button.classList.add("quick-reply");
                    button.addEventListener("click", () => {
                        showSpinner();
                        const currentUser = getCurrentUser();
                        console.log(`User ${currentUser.uid} is submitting ${choice}`);
                        user_writes(choice);
                    });
                    sceneAnswerQuickReplies.appendChild(button);
                }
            }
        } else if (event.detail.daemon_message.payload_type === "IMAGE_CHOICE") {
            text = event.detail.daemon_message.question;
            for (const choice of event.detail.daemon_message.options) {
                const img = document.createElement("img");
                img.src = choice.image_url;
                img.alt = choice.image_description;
                img.classList.add("answer-image");
                img.addEventListener("click", () => {
                    showSpinner();
                    const currentUser = getCurrentUser();
                    console.log(`User ${currentUser.uid} is submitting ${choice.image_description}`);
                    user_writes(choice.image_description);
                });
                sceneAnswerImgs.appendChild(img);
            }
        } else {
            console.error("Unknown payload type:", event.detail.daemon_message.payload_type);
            text = "The daemon speaks in tongues.";
        }
    } else if (typeof event.detail.daemon_message === 'string') {
        text = event.detail.daemon_message;
    } else {
        console.error("Unknown daemon message type:", typeof event.detail.daemon_message);
        text = "The daemon speaks in tongues.";
    }

    await updateContent(event.detail.image_url, event.detail.location_name, event.detail.daemon_name, text, event.detail.type??"", 10);

    // Enable input
    hideSpinner();
});
  

//Autocomplete logic
userInputText.addEventListener("keyup", autocomplete);
const availableCommands = [
    "@help",
    "@inventory",
    "@look",
    "@move",
    "@pickup",
    "@use",
];

export function autocomplete(e) {
    const input = e.target;

    if (input.value[0] === "@" && input.value.length > 1) {
        const search = input.value.substring(1).toLowerCase();
        const suggestions = availableCommands.filter(
            (command) => command.toLowerCase().indexOf(search) === 1
        );

        suggestionsBox.innerHTML = "";
        suggestionsBox.style.display = "block";
        suggestions.forEach((suggestion) => {
            const item = document.createElement("div");
            item.classList.add("suggestion-item");
            item.textContent = suggestion;
            item.onclick = function () {
                input.value = suggestion;
                suggestionsBox.style.display = "none";
            };
            suggestionsBox.appendChild(item);
        });
    } else {
        suggestionsBox.style.display = "none";
    }
}