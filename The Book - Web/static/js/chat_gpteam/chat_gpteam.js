import { post_to_authenticated_route } from "../common/firebase.js";

export function registerListeners() {
    document.getElementById('clear-button').addEventListener('click', async () => {
        post_to_authenticated_route('/chat_gpteam/clear', {}).then(async (response) => {
            if (response.ok) {
                const data = await response.json();
                console.log(data.reply);
            } else {
                console.error('Error:', response.status, response.statusText);
            }
        });
    });

    document.getElementById('run-button').addEventListener('click', async () => {
        post_to_authenticated_route('/chat_gpteam/run', {}).then(async (response) => {
            if (response.ok) {
                const data = await response.json();
                console.log(data.reply);
            } else {
                console.error('Error:', response.status, response.statusText);
            }
        });
    });
}