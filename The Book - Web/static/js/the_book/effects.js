export function attractAttention(divId, effect) {
    const div = document.getElementById(divId);
    div.classList.add(effect);
  
    // Remove the effect class after the animation is done
    setTimeout(() => {
      div.classList.remove(effect);
    }, 1000); // 1000ms = 1s, which is the duration of the animations
  }