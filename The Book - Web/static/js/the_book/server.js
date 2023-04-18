import { getCurrentToken, post_to_authenticated_route } from "../common/firebase.js";

export function registerListeners() {
    document.addEventListener("book-event-login-update", (e) => {
        const { status, user } = e.detail;
        if (status === "logged-in") {
            user_watch();
        }
    });
}

export async function user_watch() {
    try {
        const response = await post_to_authenticated_route(`/users/watch`);
        if (response.ok) {
            const data = await response.json();
            console.log("Server response:", data);
            const myEvent = new CustomEvent("book-event-content-update", {
                detail: data,
            });
            document.dispatchEvent(myEvent);
            return true;
        } else {
            console.error("Error moving user on server:", response.statusText);
            return false;
        }
    } catch (error) {
        console.error("Error moving user on server:", error);
        return false;
    }
}

export async function moveUserToLocation(location_id) {
    try {
        const response = await post_to_authenticated_route(`/users/move_to/${location_id}`);
        if (response.ok) {
            const data = await response.json();
            console.log("Server response:", data);
            const myEvent = new CustomEvent("book-event-content-update", {
                detail: data,
            });
            document.dispatchEvent(myEvent);
            return true;
        } else {
            console.error("Error moving user on server:", response.statusText);
            return false;
        }
    } catch (error) {
        console.error("Error moving user on server:", error);
        return false;
    }
}

export const availableCommands = [
    "@admin-clean-firestore",
    "@admin-ideate_world",
    "@inner-daemon",
    "@daemon",
    "@all",
];
export async function user_writes(text) {
    try {
        let url = "";
        if (text === "@admin-clean-firestore") {
            url = `/admin/data/clean`;
        }
        else if (text === "@admin-ideate_world") {
            url = `/admin/data/populate_world`;
        } else if (text === "@inner-daemon") {
            url = `/users/write`;
        } else if (text === "@daemon") {
            url = `/users/write`;
        } else if (text === "@all") {
            url = `/users/write`;
        } else {
            url = `/users/write`;
        }

        const response = await post_to_authenticated_route(url, {
            'text': text,
        });
        if (response.ok) {
            const data = await response.json();
            console.log("Server response:", data);
            const myEvent = new CustomEvent("book-event-content-update", {
                detail: data,
            });
            document.dispatchEvent(myEvent);
            return true;
        } else {
            console.error("Error processing user write on server:", response.statusText);
            return false;
        }
    } catch (error) {
        console.error("Error processing user write on server:", error);
        return false;
    }
}