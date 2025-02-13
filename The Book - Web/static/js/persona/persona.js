import { post_to_authenticated_route } from "../common/firebase.js";
import { Agent } from "../common/conversational_agent.js";

const form = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const chatWindow = document.getElementById("chat-window");
const btnToggleMicrophone = document.getElementById("microphone-toggle");
const btnToggleCamera = document.getElementById("camera-toggle");

var agent = null;
var persona = "Unknown";
//const episodesList = document.getElementById("episodes-list");
//const loadEpisodesButton = document.getElementById("load-episodes");

export function registerListeners(persona_id) {
    persona = persona_id;
    agent = new Agent('persona-canvas', persona);

    btnToggleMicrophone.addEventListener("click", (e) => {
        let status = agent.toggleHears();
        if (status) {
            btnToggleMicrophone.classList.add("active");
        }
        else {
            btnToggleMicrophone.classList.remove("active");
        }
    });

    //Listen to ASR
    agent.addEventListener("agent-heard", (e) => {
        handleUserInput(e.detail.sentence);
    });

    //Listen to keyboard
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = messageInput.value;
        handleUserInput(message);
    });
}

function handleUserInput(text) {
    addMessageToChat("user", text);
    const url = `/persona/${persona}/read_and_reply`;
    post_to_authenticated_route(url, { text: text }).then(async (response) => {
        if (response.ok) {
            const data = await response.json();
            addMessageToChat("persona", data);
            agent.say(data);
            fetchAndDisplayRelevantEpisodes(text);
        } else {
            addMessageToChat("system", "Error: Could not get reply from Persona");
        }
        messageInput.value = "";
    });
}

function addMessageToChat(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", role);
    messageDiv.innerHTML = `<p>${content}</p>`;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight; // Scroll to the bottom
}

async function fetchAndDisplayRelevantEpisodes(text) {
    // Fetch the most relevant episodes
    const url = `/persona/${persona}/relevant_episodes`;
    const response = await post_to_authenticated_route(url, { text: text });

    if (response.ok) {
        const episodes = await response.json();
        const panel = document.getElementById("relevant-memories-panel");
        panel.innerHTML = ""; // Clear previous memories

        for (const episode of episodes) {
            const episodeDiv = document.createElement("div");
            episodeDiv.classList.add("episode");
            
            const progressBar = document.createElement("div");
            progressBar.classList.add("progress-bar");
            episodeDiv.appendChild(progressBar);
            
            const progressBarFilling = document.createElement("div");
            progressBarFilling.classList.add("progress-bar-filling");
            progressBarFilling.style.width = `${episode.similarity_score * 100}%`;
            progressBar.appendChild(progressBarFilling);
            
            const progressBarScore = document.createElement("div");
            progressBarScore.classList.add("progress-bar-score");
            progressBarScore.innerHTML = `${episode.similarity_score * 100}%`;
            progressBar.appendChild(progressBarScore);
            
            const dateDiv = document.createElement("div");
            dateDiv.classList.add("episode-date");
            dateDiv.innerHTML = `<p>${episode.date}</p>`;
            episodeDiv.appendChild(dateDiv);
            
            const summaryDiv = document.createElement("div");
            summaryDiv.classList.add("episode-summary");
            summaryDiv.innerHTML = `<p>${episode.episode_summary}</p>`;
            episodeDiv.appendChild(summaryDiv);
            
            panel.appendChild(episodeDiv);
        }
    } else {
        console.error("Error fetching relevant episodes");
    }
}

/*
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
        messageDiv.classList.add("message", message.role == "assistant" ? "persona" : message.role);
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
*/