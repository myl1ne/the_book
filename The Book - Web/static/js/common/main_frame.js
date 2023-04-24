import { post_to_authenticated_route } from './firebase.js';
import { UnityCanvas } from './unity_canvas.js';


document.addEventListener('DOMContentLoaded', () => {
    setupHeaderFooter();
    setupUnity();
    setupNavBarButtons();
});

function setupUnity() {
    
    const isDevelopment = false;
    console.log("Loading Spoon Canvas");
    document.unityCanvas = new UnityCanvas(document.getElementById("body-overlay"), "Overlaid3DContent", isDevelopment);

    window.addEventListener("WorldEventOnCreated", (e) => {
        console.log("World is loaded and ready to be used");
        document.unityCanvas.forwardCursorToUnity();
        
        document.unityCanvas.nativeBridge.world_CreateOrUpdateEntity(
            "NavigationTarget",
            "Generic3D",
            "ThreeD",
            { x: 0.0, y: 0.0, z: 0.0 },
            { x: 0.25, y: 0.25, z: 0.25 },
            { x: 0.0, y: 0.0, z: 0.0 },
        );
        //Making Myline the right size and out of scren
        document.unityCanvas.nativeBridge.world_CreateOrUpdateEntity(
            "Myline",
            null,
            "ThreeD",
            { x: 0.0, y: 0.0, z: 0.0 },
            { x: 2.5, y: 2.5, z: 2.5 },
            { x: 0.0, y: 0.0, z: 180.0 },
        );
        document.unityCanvas.nativeBridge.entity_MoveTo_Target("Myline", "NavigationTarget");
    });
}

function setupNavBarButtons() {
    const button = document.getElementById('main-frame-btn-speak');
    button.addEventListener('click', async () => {
        button.disabled = true;
        document.unityCanvas.nativeBridge.entity_Say("Myline", "This is a test.", "jaina", "en" );
    });
}

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

function setupHeaderFooter() {
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
}
