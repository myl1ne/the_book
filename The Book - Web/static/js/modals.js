import { getCurrentUser, getUserDocument, moveUserToLocation } from "./firebase.js";

const teleportIcon = document.getElementById("teleport-icon");
const characterSheetIcon = document.getElementById("character-sheet-icon");
const inventoryIcon = document.getElementById("inventory-icon");
const questsIcon = document.getElementById("quests-icon");

const teleportModal = document.getElementById("teleport-modal");
const characterSheetModal = document.getElementById("character-sheet-modal");
const inventoryModal = document.getElementById("inventory-modal");
const questsModal = document.getElementById("quests-modal");

function openModal(modal) {
    updateAllModalsContent();
    modal.style.display = "block";
}

function closeModal(modal) {
    modal.style.display = "none";
}

function closeAllModals() {
    closeModal(teleportModal);
    closeModal(characterSheetModal);
    closeModal(inventoryModal);
    closeModal(questsModal);
}

async function updateAllModalsContent() {
    let user = await getCurrentUser();
    let userDoc = await getUserDocument(user.uid);
    if (!userDoc) {
        console.log("User document not found");
        return;
    }
    let character = userDoc.user.character;
    console.log(`Character: ${character}`);
    updateTeleportModalContent(character);
    updateQuestsModalContent(character);
    updateInventoryModalContent(character);
    updateCharSheetModalContent(character);
}

teleportIcon.onclick = () => openModal(teleportModal);
characterSheetIcon.onclick = () => openModal(characterSheetModal);
inventoryIcon.onclick = () => openModal(inventoryModal);
questsIcon.onclick = () => openModal(questsModal);

// Close the modal when clicking outside of the modal content
window.onclick = (event) => {
    if (event.target.classList.contains("modal")) {
        closeModal(event.target);
    }
}

document.getElementById('teleport-btn').addEventListener('click', () => {
    const selectedLocation = document.getElementById('teleport-location').value;
    moveUserToLocation( getCurrentUser().uid, selectedLocation);
    closeAllModals();
});