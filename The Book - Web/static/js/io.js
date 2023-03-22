import { getCurrentUser, user_writes } from "./firebase.js";

const sceneImage = document.getElementById("scene-image");
const sceneText = document.getElementById("scene-text");

export async function updateContent(imageUrl, text, delay = 100) {
    sceneImage.src = imageUrl;
    sceneText.textContent = "";
  
    // Write the new text character by character
    for (const character of text) {
      sceneText.textContent += character;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
}

document.getElementById("user-input-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const user_input = document.getElementById("user-input");
    const currentUser = getCurrentUser();
    console.log(`User ${currentUser.uid} is submitting ${user_input.value}`);
    await user_writes(currentUser.uid, user_input.value);
    user_input.value = "";
});

document.addEventListener("book-event-content-update", async (event) => {
    console.log("book-event-content-update caught:", event.detail);
    await updateContent(event.detail.image_url, event.detail.daemon_message, 50);
  });