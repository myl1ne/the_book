// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.18.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/9.18.0/firebase-analytics.js";
import { getFirestore, doc, setDoc } from "https://www.gstatic.com/firebasejs/9.18.0/firebase-firestore.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.18.0/firebase-auth.js";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyB7bAv14rouPkeCwg-7NNJr41ckD4U5cYI",
    authDomain: "the-book-b7ff4.firebaseapp.com",
    projectId: "the-book-b7ff4",
    storageBucket: "the-book-b7ff4.appspot.com",
    messagingSenderId: "5148384870",
    appId: "1:5148384870:web:74a5e7087332dc060d17a7",
    measurementId: "G-EFJ1GZTLP5"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const db = getFirestore(app);
const auth = getAuth(app);
let currentUser = null;

auth.onAuthStateChanged((user) => {
    if (user) {
        console.log(`onAuthStateChanged: Used signed in: ${user}`)
        currentUser = user;
    } else {
        console.log(`onAuthStateChanged: Used signed out`)
        currentUser = null;
    }
});

// Functions
export function getCurrentUser() {
    return currentUser
}

export async function authenticateUser(email, password) {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        return { user, isNewUser: false };
    } catch (error) {
        if (error.code === "auth/user-not-found") {
            try {
                const userCredential = await createUserWithEmailAndPassword(auth, email, password);
                const user = userCredential.user;
                return { user, isNewUser: true };
            } catch (signupError) {
                console.error("Error signing up:", signupError);
                return { user: null, isNewUser: false };
            }
        } else {
            console.error("Error signing in:", error);
            return { user: null, isNewUser: false };
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

export async function createUserDocument(user) {
    try {
        const userDocRef = doc(db, "users", user.uid);
        const userData = {
            email: user.email,
        };

        await setDoc(userDocRef, userData);
        return true;
    } catch (error) {
        console.error("Error creating user document:", error);
        return false;
    }
}

export async function createUserInServer(id) {
    try {
        const response = await fetch(`/users/${id}/create`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (response.ok) {
            const data = await response.json();
            console.log("Server response:", data);
            // Use the JSON data in your application
            return true;
        } else {
            console.error("Error creating user on server:", response.statusText);
            return false;
        }
    } catch (error) {
        console.error("Error creating user on server:", error);
        return false;
    }
}

export async function logUserInServer(id) {
    try {
        const response = await fetch(`/users/${id}/log`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (response.ok) {
            const data = await response.json();
            console.log("Server response:", data);
            // Use the JSON data in your application
            return true;
        } else {
            console.error("Error logging user on server:", response.statusText);
            return false;
        }
    } catch (error) {
        console.error("Error logging user on server:", error);
        return false;
    }
}

export async function move_user_to_location(user_id, location_id) {
    try {
        const response = await fetch(`/users/${user_id}/move_to/${location_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
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
            console.error("Error moving user on server:", response.statusText);
            return false;
        }
    } catch (error) {
        console.error("Error moving user on server:", error);
        return false;
    }
}

export async function user_writes(user_id, text) {
    try {
        const response = await fetch(`/users/${user_id}/write`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ 'text': text }),
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