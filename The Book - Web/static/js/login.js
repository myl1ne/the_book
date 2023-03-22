import { authenticateUser, logoutUser, createUserDocument, createUserInServer, logUserInServer, move_user_to_location, user_watch } from "./firebase.js";

document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
  
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
  
    const { user, isNewUser } = await authenticateUser(email, password);
  
    if (user) {
        if (isNewUser) {
            console.log("Authentication: New user registered");
            const success = await createUserDocument(user);
            if (success) {
                console.log("User creation: Success");
                const serverSuccess = await createUserInServer(user.uid);
                if (serverSuccess) {
                    console.log("Character Creation: Success");
                    const daemon_message = move_user_to_location(user.uid, "The Book");
                }
                else
                {
                    console.log("Character Creation: Failure");
                }
            }
            else
            {
                console.log("User Creation: Failure");
            }
        }
        else
        {
            console.log("Authentication: Welcome back");
            const serverSuccess = await logUserInServer(user.uid);
            if (serverSuccess) {
                console.log("Character Log: Success");
                const daemon_message = user_watch(user.uid);
            }
            else
            {
                console.log("Character Log: Failure");
            }
        }
        document.getElementById("logout-form-user-email").textContent = `Logged in as: ${user.email}`;
        document.getElementById("logout-form").style.display = "block";
        document.getElementById("login-form").style.display = "none";
        document.getElementById("input-container").style.display = "flex"; 
    }
    else
    {
        console.log("Authentication: Failed");
      // Authentication or registration failed, show an error message or handle the error
    }
});
  
document.getElementById("logout-form").addEventListener("submit", async (event) => {
    event.preventDefault();
  
    const success = await logoutUser();
  
    if (success) {
      // User successfully logged out
      // Hide the logout form and show the login form
      document.getElementById("logout-form").style.display = "none";
      document.getElementById("login-form").style.display = "block";
      document.getElementById("input-container").style.display = "none";
    } else {
      // Log out failed, show an error message or handle the error
    }
  });