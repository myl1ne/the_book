import { authenticateUser, logoutUser, getCurrentUser } from "./firebase.js";

document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    authenticateUser(email, password);
});
  
document.getElementById("logout-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    logoutUser();
});

document.addEventListener("book-event-login-update", async (event) => {
    console.log("book-event-login-update caught:", event.detail);
    if (event.detail.status === "logged-out") {
        onUserLogout();
    }
    else if (event.detail.status === "logged-in") {
        onUserLogin();
    }
});

function onUserLogin() {
    // Hide the login form and show the logout form
    document.getElementById("logout-form-user-email").textContent = `Logged in as: ${getCurrentUser().email}`;
    document.getElementById("login-form").style.display = "none";
    document.getElementById("logout-form").style.display = "block";
    document.getElementById("scene-input").style.display = "flex";
}

function onUserLogout() {
    // Hide the logout form and show the login form
    document.getElementById("logout-form").style.display = "none";
    document.getElementById("login-form").style.display = "block";
    document.getElementById("scene-input").style.display = "none";
    document.getElementById("icon-container").style.display = "none";
}