// Show exactly one screen: "start", "ringing", "call", or "recap".
function show(name) {
  document.querySelectorAll(".screen").forEach((el) => {
    el.hidden = el.id !== `screen-${name}`;
  });
}

// Temporary click-through so each screen can be previewed.
// Step 3 replaces this with the real flow and mock API.
document.getElementById("btn-start").onclick = () => show("ringing");
document.getElementById("btn-decline").onclick = () => show("start");
document.getElementById("btn-accept").onclick = () => show("call");
document.getElementById("btn-hangup").onclick = () => show("recap");
document.getElementById("btn-again").onclick = () => show("start");
