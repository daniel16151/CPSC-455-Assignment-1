
const SERVER_URI = "wss://lg09dxfj-443.usw3.devtunnels.ms/:443";
let ws, currentTarget = null;

function log(text) {
  const entry = document.createElement("div");
  entry.textContent = text;
  document.getElementById("log").append(entry);
  entry.scrollIntoView();
}

function updateUsers(list) { // handle user list
  const ul = document.getElementById("userList");
  ul.innerHTML = "";
  list.forEach(user => {
    const li = document.createElement("li");
    li.textContent = user;
    li.addEventListener("dblclick", () => {
      if (user === username) {
        log("You cannot select yourself.");
      } else {
        currentTarget = user;
        log(`Chatting with ${user}`);
      }
    });
    ul.append(li);
  });
}

let incomingFile = null, incomingName = ""; // handle files
function handleFile(data) {
  if (data.file_transfer === "start") {
    incomingName = data.filename;
    incomingFile = [];
    log(`Preparing to receive file: ${incomingName}`);
  }
  else if (data.file_transfer === "end") {
    const blob = new Blob(incomingFile);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `received_${incomingName}`;
    a.click();
    URL.revokeObjectURL(a.href);
    log(`File received: received_${incomingName}`);
    incomingFile = null;
  }
}

let username = null;
function start() {
  ws = new WebSocket(SERVER_URI);

  setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ping" }));
  }
  }, 
  30000);

  ws.onopen = () => {
    log("Connected to server.");
    log("Enter 'R' to register or 'L' to login:");
  };

  ws.onmessage = async evt => {
    let data;
    try { data = JSON.parse(evt.data); }
    catch { log(evt.data); return; }
    if (data.type === "ping") {
    ws.send(JSON.stringify({ type: "pong" }));
    }

    if (data.online_users) {
      updateUsers(data.online_users);
    }
    else if (data.direct_message) {
      log(data.direct_message);
    }
    else if (data.file_transfer) {
      handleFile(data);
    }
    else if (typeof data === "string" && data.startsWith("Logged in as ")) {
      username = data.replace("Logged in as ", "").trim();
      log(data);
    }
    else {
      log(evt.data);
    }
  };

  ws.onclose = () => { log("Connection closed."); };
  ws.onerror = e => { log("WebSocket error: " + e.message); };
}

function sendText(msg) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  if (msg.toLowerCase() === "/quit") {
    ws.close();
    return;
  }
  if (currentTarget) {
    ws.send(JSON.stringify({ target: currentTarget, message: msg }));
    log(`To ${currentTarget}: ${msg}`);
  } else {
    ws.send(msg);
    log(`To system: ${msg}`);
  }
}

async function sendFile(file) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    log("WebSocket not connected!");
    return;
  }
  if (!currentTarget) {
    log("No target selected for file transfer!");
    return;
  }

  log(`Sending file: ${file.name} to ${currentTarget}`);
  ws.send(JSON.stringify({
    file_transfer: "start",
    target: currentTarget,
    filename: file.name
  }));

  const chunkSize = 4096;
  const reader = file.stream().getReader();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    ws.send(value);
  }

  ws.send(JSON.stringify({
    file_transfer: "end",
    target: currentTarget
  }));
  log(`File '${file.name}' sent successfully to ${currentTarget}.`);
}

document.addEventListener("DOMContentLoaded", () => {
  start();

  document.getElementById("sendBtn").onclick = () => {
    const inp = document.getElementById("msgInput");
    const txt = inp.value.trim();
    if (txt) {
      sendText(txt);
      inp.value = "";
    }
  };

  document.getElementById("fileBtn").onclick = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.onchange = e => sendFile(e.target.files[0]);
    input.click();
  };

  document.getElementById("msgInput")
    .addEventListener("keypress", e => {
      if (e.key === "Enter") {
        document.getElementById("sendBtn").click();
      }
      const emojis = [
        "😀", "😃", "😄", "😁", "😆", "🤣", "😊", "😇",
        "😉", "😍", "🤔", "🤗", "🙄", "😏", "😣", "😖",
        "😞", "😡", "❤️", "💔", "🔥", "🎉", "👍", "👎",
        "🚀", "✨", "☕", "🍔", "🍕", "🍎", "⚽"
      ];
    
      const picker = document.getElementById("emojiPicker");
      const btn    = document.getElementById("emojiBtn");
      const input  = document.getElementById("msgInput");
    
      if (!picker.dataset.populated) {
        emojis.forEach(e => {
          const span = document.createElement("span");
          span.textContent = e;
          span.addEventListener("click", () => {
            const input = document.getElementById("msgInput");
            const start = input.selectionStart, end = input.selectionEnd;
            input.value = input.value.slice(0,start) + e + input.value.slice(end);
            input.selectionStart = input.selectionEnd = start + e.length;
            input.focus();
            picker.style.display = "none";
          });
          picker.append(span);
        });
        picker.dataset.populated = "true";  // mark it done
      }
    
      btn.addEventListener("click", () => {
        picker.style.display = (picker.style.display === "block") ? "none" : "block";
      });
    
      document.addEventListener("click", e => {
        if (!picker.contains(e.target) && e.target !== btn) {
          picker.style.display = "none";
        }
      });
    });});
