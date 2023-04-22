import { authenticateUser, logoutUser, getCurrentUser } from "./firebase.js";

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
    let logOutForm = document.getElementById("logout-form");
    if (logOutForm) {
        logOutForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            logoutUser();
        });
        // Hide the login form and show the logout form
        document.getElementById("logout-form-user-email").textContent = `Logged in as: ${getCurrentUser().email}`;
        document.getElementById("logout-form").style.display = "block";
    }
    let loginForm = document.getElementById("login-form");
    if (loginForm) {
        document.getElementById("login-form").style.display = "none";
    }

    let sceneInput = document.getElementById("scene-input");
    if (sceneInput) {
        sceneInput.style.display = "flex";
    }

    // Check if the user is an admin
    //const isAdmin = await checkIfUserIsAdmin(uid);

    // Show or hide admin-only links based on the admin status
    if (getCurrentUser().isAdmin) {
        const adminLinks = document.querySelectorAll('.admin-only');
        adminLinks.forEach((link) => {
            link.classList.remove('hidden');
            //link.style.display = ''; //isAdmin ? '' : 'none';
        });
    }
}

function onUserLogout() {
    let loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;
            authenticateUser(email, password);
        });
        document.getElementById("login-form").style.display = "block";
    }
    let logoutForm = document.getElementById("logout-form");
    if (logoutForm) {
        document.getElementById("logout-form").style.display = "none";
    }
    let sceneInput = document.getElementById("scene-input");
    if (sceneInput) {
        document.getElementById("scene-input").style.display = "none";
        document.getElementById("icon-container").style.display = "none";
    }
    // Hide admin-only links
    const adminLinks = document.querySelectorAll('.admin-only');
    adminLinks.forEach((link) => {
        link.classList.add('hidden');
        //link.style.display = 'none';
    });
}