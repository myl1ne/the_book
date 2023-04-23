import { post_to_authenticated_route } from './firebase.js';
import { UnityCanvas } from './unity_canvas.js';


document.addEventListener('DOMContentLoaded', () => {
    setupHeaderFooter();
    setupNavBarButtons();
    setupUnity();
});

function setupUnity() {
    
    const isDevelopment = false;
    console.log("Loading Spoon Canvas");
    document.unityCanvas = new UnityCanvas(document.getElementById("body-overlay"), "Overlaid3DContent", isDevelopment);

    window.addEventListener("WorldEventOnCreated", (e) => {
        console.log("World is loaded and ready to be used");
            console.log("Spawning a cursor");
            document.unityCanvas.forwardCursorToUnity();
    });
}

function setupNavBarButtons() {
    const button = document.getElementById('main-frame-btn-speak');
    button.addEventListener('click', async () => {
        button.disabled = true;
        const response = await post_to_authenticated_route(`/api/say`, {'text': 'Hello World!', 'voice': 'jaina', 'language': 'en'});
        if (response.ok) {
            const data = await response.json();
            console.log("Server response:", data);
            document.unityCanvas.nativeBridge.entity_Play_Sound("Myline", data.url);
        } else {
            console.error("Error:", response.statusText);
            return false;
        }
        button.disabled = false;
    });
}

function setupHeaderFooter() {
    function headerFooterClose() {
        document.getElementById('body-content').className = 'collapsed-both';
        let nav = document.querySelector('.nav-drawer');
        nav.style.display = 'none';
        nav.parentElement.classList.add('collapsed');
        let foot = document.querySelector('.footer-drawer');
        foot.style.display = 'none';
        foot.parentElement.classList.add('collapsed');
        const toggleButtons = document.querySelectorAll('.toggle-button');
        toggleButtons.forEach((btn) => {
            if (btn.parentElement.tagName === 'HEADER') {
                btn.querySelector('i').className = 'fas fa-chevron-down';
            } else if (btn.parentElement.tagName === 'FOOTER') {
                btn.querySelector('i').className = 'fas fa-chevron-up';
            }
        });
    }

    function headerFooterOpen() {
        document.getElementById('body-content').className = '';
        let nav = document.querySelector('.nav-drawer');
        nav.style.display = 'flex';
        nav.parentElement.classList.remove('collapsed');
        let foot = document.querySelector('.footer-drawer');
        foot.style.display = 'flex';
        foot.parentElement.classList.remove('collapsed');
        const toggleButtons = document.querySelectorAll('.toggle-button');
        toggleButtons.forEach((btn) => {
            if (btn.parentElement.tagName === 'HEADER') {
                btn.querySelector('i').className = 'fas fa-chevron-up';
            } else if (btn.parentElement.tagName === 'FOOTER') {
                btn.querySelector('i').className = 'fas fa-chevron-down';
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        const toggleButtons = document.querySelectorAll('.toggle-button');
        toggleButtons.forEach((btn) => {
            btn.addEventListener('click', function() {

                if (btn.parentElement.classList.contains('collapsed')){
                    headerFooterOpen();
                } else {
                    headerFooterClose();
                }
            });
        });
    });
}
