const teleportIcon = document.getElementById("teleport-icon");
const characterSheetIcon = document.getElementById("character-sheet-icon");
const inventoryIcon = document.getElementById("inventory-icon");
const questsIcon = document.getElementById("quests-icon");

const teleportModal = document.getElementById("teleport-modal");
const characterSheetModal = document.getElementById("character-sheet-modal");
const inventoryModal = document.getElementById("inventory-modal");
const questsModal = document.getElementById("quests-modal");

function openModal(modal) {
    modal.style.display = "block";
}

function closeModal(modal) {
    modal.style.display = "none";
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