import { post_to_authenticated_route } from "../common/firebase.js";

const form = document.getElementById("message-form");
const messageInput = document.getElementById("message");
const chatWindow = document.getElementById("chat-window");
const episodesList = document.getElementById("episodes-list");
const loadEpisodesButton = document.getElementById("load-episodes");

export function registerListeners(persona_id) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = messageInput.value;
        addMessageToChat("user", message);
        const url = `/persona/${persona_id}/read_and_reply`;
        post_to_authenticated_route(url, { text: message }).then(async (response) => {
            if (response.ok) {
                const data = await response.json();
                addMessageToChat("assistant", data);
            } else {
                addMessageToChat("system", "Error: Could not get reply from Persona");
            }
            messageInput.value = "";
        });
    });

    loadEpisodesButton.addEventListener("click", () => { fetchEpisodes(persona_id); });
}

function addMessageToChat(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", role);
    messageDiv.innerHTML = `<p>${content}</p>`;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight; // Scroll to the bottom
}

function createEpisodeElement(date, summary, messages) {
    const episodeDiv = document.createElement("div");
    episodeDiv.classList.add("episode");

    const header = document.createElement("h3");
    header.textContent = `Episode on ${date}`;
    episodeDiv.appendChild(header);

    const summaryDiv = document.createElement("div");
    summaryDiv.classList.add("episode-summary");
    summaryDiv.innerHTML = `<strong>Summary:</strong><br>${summary}`;
    episodeDiv.appendChild(summaryDiv);

    const messagesDiv = document.createElement("div");
    messagesDiv.classList.add("episode-messages");
    const messagesTitle = document.createElement("div");
    messagesTitle.classList.add("episode-messages");
    messagesTitle.innerHTML = `<strong>Messages:</strong>`;
    messagesDiv.appendChild(messagesTitle);
    messages.forEach((message) => {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", message.role);
        messageDiv.innerHTML = `<p>${message.content}</p>`;
        messagesDiv.appendChild(messageDiv);
    });
    episodeDiv.appendChild(messagesDiv);

    return episodeDiv;
}

async function fetchEpisodes(persona_id) {
    const url = `/persona/${persona_id}/episodes`;
    post_to_authenticated_route(url).then(async (response) => {
        if (response.ok) {
            const episodes = await response.json();
    
            episodesList.innerHTML = ""; // Clear the episodes list
            episodes.forEach((episode) => {
                const episodeElement = createEpisodeElement(
                    episode.date,
                    episode.episode_summary,
                    episode.messages
                );
                episodesList.appendChild(episodeElement);
            });
        } else {
            const errorDiv = document.createElement("div");
            errorDiv.classList.add("error");
            errorDiv.textContent = "Error: Could not fetch episodes";
            episodesList.appendChild(errorDiv);
        }
    });
}