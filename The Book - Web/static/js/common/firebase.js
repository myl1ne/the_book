import { initializeApp } from "https://www.gstatic.com/firebasejs/9.18.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.18.0/firebase-auth.js";

var firebaseConfig = {
    apiKey: "AIzaSyDl5jdMRsx0ynlWlH-YuxeS-RrfGaNcK1Q",
    authDomain: "the-book-382116.firebaseapp.com",
  };

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
let currentUser = null;
let currentToken = null;

auth.onAuthStateChanged(async (user) => {
    if (user) {
        console.log(`onAuthStateChanged: Used signed in: ${user}`)
        currentUser = user;
        const serverSuccess = await logUserInServer();
        if (serverSuccess) {
            console.log("Character Log: Success");
            
            const myEvent = new CustomEvent("book-event-login-update", {
                detail: {
                    status: "logged-in",
                    user: user,
                },
            });
            document.dispatchEvent(myEvent);
            return true;
        }
    }
    console.log(`onAuthStateChanged: Used signed out`)
    currentUser = null;
    currentToken = null;
    const myEvent = new CustomEvent("book-event-login-update", {
        detail: {
            status: "logged-out",
            user: currentUser,
        },
    });
    document.dispatchEvent(myEvent);
});

// Functions
export function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

export function getCurrentUser() {
    return currentUser;
}
export function getCurrentToken() {
    return currentToken;
}

export async function authenticateUser(email, password) {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        return { user };
    } catch (error) {
        if (error.code === "auth/user-not-found") {
            try {
                const userCredential = await createUserWithEmailAndPassword(auth, email, password);
                const user = userCredential.user;
                return { user  };
            } catch (signupError) {
                console.error("Error signing up:", signupError);
                return { user: null };
            }
        } else {
            console.error("Error signing in:", error);
            return { user: null };
        }
    }
}

export async function logoutUser() {
    try {
        await signOut(auth);
        return true;
    } catch (error) {
        console.error("Error signing out:", error);
        return false;
    }
}

export async function logUserInServer() {
    let result = false;
    try {
        result = getCurrentUser().getIdToken(true).then(async (idToken) => {
            currentToken = idToken;
            const response = await fetch(`/users/log`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({
                    idToken: currentToken,
                }),
            });
    
            if (response.ok) {
                const data = await response.json();
                console.log("Server response:", data);
                currentUser.isAdmin = data.isAdmin;
                // Use the JSON data in your application
                return true;
            } else {
                console.error("Error logging user on server:", response.statusText);
                return false;
            }
        }).catch(function (error) {
            console.error("Error while getting idToken:", error);
            currentToken = null;
            return false;
          });
    } catch (error) {
        console.error("Error logging user on server:", error);
        result = false;
    }
    return result;
}

export async function getUserDocument(user_id) {
    try {
        const response = await fetch(`/users/${user_id}/`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (response.ok) {
            const data = await response.json();
            return data;
        } else {
            console.error("Error getting user document:", response.statusText);
            return false;
        }
    } catch (error) {
        console.error("Error fetching user document:", error);
        return false;
    }
}

export async function get_authenticated_route(route) {
    return new Promise(async (resolve, reject) => {
        try {
            const response = await fetch(route, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${currentToken}`,
                },
            });
            resolve(response);
        } catch (error) {
            console.error("Error fetching authenticated route:", error);
            reject(error);
        }
    });
}

export async function post_to_authenticated_route(route, additionalBody = {}) {
    return new Promise(async (resolve, reject) => {
        try {
            let fullBody = {
                idToken: currentToken,
            };
            fullBody = Object.assign(fullBody, additionalBody);
            const response = await fetch(route, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify(fullBody),
            });
            resolve(response);
        } catch (error) {
            console.error("Error fetching authenticated route:", error);
            reject(error);
        }
      });
}

