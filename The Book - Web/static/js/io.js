import { getCurrentUser, user_writes } from "./firebase.js";

const sceneImage = document.getElementById("scene-image");
const sceneTitle = document.getElementById("scene-title");
const sceneDaemonName = document.getElementById("scene-daemon-name");
const sceneText = document.getElementById("scene-text");
const sceneAnswerImgs = document.getElementById("scene-answer-images");
const sceneAnswerQuickReplies = document.getElementById("scene-answer-quick-replies");
const spinner = document.getElementById("loading-spinner");
const inputForm = document.getElementById("user-input-form");

export async function updateContent(imageUrl, title, daemonName, text, delay = 100) {
    sceneImage.src = imageUrl;
    sceneTitle.innerHTML = title;
    sceneDaemonName.innerHTML = daemonName;
    sceneText.innerHTML = "";
  
    let currentTag = "";
    let currentText = "";
    let currentElement = sceneText;
  
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
        currentText += character;
        await appendTextNodeAnimated(currentElement, character, delay);
      }
    }
  }
  
  function appendTextNode(parent, text) {
    const textNode = document.createTextNode(text);
    if (parent.lastChild && parent.lastChild.nodeType === Node.TEXT_NODE) {
      parent.lastChild.textContent += text;
    } else {
      parent.appendChild(textNode);
    }
  }
  
  async function appendTextNodeAnimated(parent, character, delay) {
    if (parent.lastChild && parent.lastChild.nodeType === Node.TEXT_NODE) {
      parent.lastChild.textContent += character;
    } else {
      parent.appendChild(document.createTextNode(character));
    }
    await new Promise((resolve) => setTimeout(resolve, delay));
}
  
document.getElementById("user-input-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const user_input = document.getElementById("user-input");
    const currentUser = getCurrentUser();
    console.log(`User ${currentUser.uid} is submitting ${user_input.value}`);
    user_writes(currentUser.uid, user_input.value);
    user_input.value = "";
    sceneText.innerHTML = "";
    // Disable input and show spinner
    inputForm.disabled = true;
    spinner.style.display = "block";
});

document.addEventListener("book-event-content-update", async (event) => {
    console.log("book-event-content-update caught:", event.detail);
    // Hide spinner
    spinner.style.display = "none";
    sceneAnswerImgs.innerHTML = "";
    sceneAnswerQuickReplies.innerHTML = "";

    // Parse daemon message
    let text = "";
    if (typeof event.detail.daemon_message === 'object') {
        if (event.detail.daemon_message.payload_type === "QUESTION") {
            text = event.detail.daemon_message.question;
            if (event.detail.daemon_message.options) {
                for (const choice of event.detail.daemon_message.options) {
                    const button = document.createElement("button");
                    button.innerHTML = choice;
                    button.classList.add("answer-button");
                    button.addEventListener("click", () => {
                        const currentUser = getCurrentUser();
                        console.log(`User ${currentUser.uid} is submitting ${choice}`);
                        user_writes(currentUser.uid, choice);
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
                    const currentUser = getCurrentUser();
                    console.log(`User ${currentUser.uid} is submitting ${choice.image_description}`);
                    user_writes(currentUser.uid, choice.image_description);
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
    //Show typewriter content
    await updateContent(event.detail.image_url, event.detail.location_name, event.detail.daemon_name, text, 30);

    // Enable input
    const input = document.getElementById("user-input-form");
    inputForm.disabled = false;
  });