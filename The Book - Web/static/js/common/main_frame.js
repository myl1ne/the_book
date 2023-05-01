import { post_to_authenticated_route } from './firebase.js';
import { Agent } from './conversational_agent.js';


if (!document.the_book) {
    document.the_book = {
        agents: {},
    };
}

document.addEventListener('DOMContentLoaded', () => {
    setupHeaderFooter();
    setupNavBarButtons();
});

function setupNavBarButtons() {
    const button = document.getElementById('main-frame-btn-speak');
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
