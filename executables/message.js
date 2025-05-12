const SERVER_URI = "wss://web-production-860cc.up.railway.app/ws";
let ws, currentTarget = null;
let reconnectInterval = 1000; 
const maxInterval       = 30000;
const FERNET_KEY = "FERNET_KEY";

async function encryptMessage(message) {
    const encodedMessage = new TextEncoder().encode(message);
    const response = await fetch('/encrypt', { 
        method: 'POST', 
        body: JSON.stringify({ key: FERNET_KEY, message: encodedMessage }) 
    });
    const { encrypted } = await response.json();
    return encrypted;
}

async function decryptMessage(encryptedMessage) {
    const response = await fetch('/decrypt', { 
        method: 'POST', 
        body: JSON.stringify({ key: FERNET_KEY, encryptedMessage }) 
    });
    const { message } = await response.json();
    return message;
}

function sendText(msg) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const encryptedMsg = encryptMessage(msg);
    ws.send(encryptedMsg);
}

ws.onmessage = async evt => {
    if (evt.data instanceof ArrayBuffer) {
        const encryptedFile = new Uint8Array(evt.data);
        const decryptedFile = await decryptMessage(encryptedFile);
    } else {
        const decryptedMessage = await decryptMessage(evt.data);
        console.log(decryptedMessage);
    }
};

function sanitizeText(text) {
  return text.replace(/[<>]/g, "");
}

function log(text) {
  const entry = document.createElement("div");
  entry.textContent = text;
  document.getElementById("log").append(entry);
  entry.scrollIntoView();
}

function updateUsers(list) {
  const ul = document.getElementById("userList");
  ul.innerHTML = ""; 
  list.forEach(user => {
    const li = document.createElement("li");
    li.textContent = user;
    li.addEventListener("dblclick", () => {
      currentTarget = user;
      log(`Chatting with ${user}`);
    });
    ul.appendChild(li);
  });
}

function handleFile(data) {
  console.log("handleFile called — using manual download link");
  const logDiv = document.getElementById("log");

  if (data.file_transfer === "start") {
    incomingName = data.filename;
    incomingFile = [];
    const msg = document.createElement("div");
    msg.textContent = `Preparing to receive file: ${incomingName}`;
    logDiv.append(msg);
    msg.scrollIntoView();
  }
  else if (data.file_transfer === "end") {
    const blob = new Blob(incomingFile);
    const url  = URL.createObjectURL(blob);

    const container = document.createElement("div");
    container.textContent = `File received: `;

    const link = document.createElement("a");
    link.href = url;
    link.download = incomingName;
    link.textContent = `Download ${incomingName}`;
    link.style.marginLeft = "8px";

    link.addEventListener("click", () => {
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });

    container.append(link);
    logDiv.append(container);
    container.scrollIntoView();

    incomingFile = [];
    incomingName = "";
  }
}

function renderFileLink(url, filename, prefix = "") {
  const container = document.createElement("div");
  container.textContent = prefix;

  const link = document.createElement("a");
  link.href        = url;
  link.textContent = filename;
  link.target      = "_blank";
  link.style.marginLeft = "8px";

  container.append(link);
  document.getElementById("log").append(container);
  container.scrollIntoView();
}
let username = null;
function connect() {
  ws = new WebSocket(SERVER_URI);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    log("Connected to server.");
    reconnectInterval = 1000;
  };

ws.onmessage = async evt => {
  if (evt.data instanceof ArrayBuffer) {
    incomingFile.push(evt.data);
    return;
  }
  if (evt.data instanceof Blob) {
    const buf = await evt.data.arrayBuffer();
    incomingFile.push(buf);
    return;
  }

  const text = evt.data;
  if (text.startsWith("Logged in as ")) {
        username = text.replace("Logged in as ", "").trim();
        log(text);
        return;
    }
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    log(text);
    return;
  }

  if (data.type === "file_url" && data.url && data.filename) {
    renderFileLink(data.url, data.filename);
    return;
  }

  if (data.online_users) {
    updateUsers(data.online_users);
    return;
  }

  if (data.direct_message) {
    const dm = data.direct_message; 
    const brace = dm.indexOf("{");
    if (brace !== -1) {
      const prefix   = dm.substring(0, brace);
      const jsonPart = dm.substring(brace);

      try {
        const inner = JSON.parse(jsonPart);

        if (inner.type === "file_url" && inner.url && inner.filename) {
          renderFileLink(inner.url, inner.filename, prefix);
          return;
        }
      } catch (e) {
      }
    }
    log(dm);
    return;
  }
  if (data.file_transfer) {
    handleFile(data);
    return;
  }
  if (typeof data === "string" && data.startsWith("Logged in as ")) {
    username = data.replace("Logged in as ", "").trim();
    log(data);
    return;
  }
  log(text);
};

  ws.onclose = e => {
    username = null;
    currentTarget = null;
    log(`Connection closed. Reconnecting in ${reconnectInterval/1000}s…`);
    setTimeout(connect, reconnectInterval);
    reconnectInterval = Math.min(reconnectInterval * 2, maxInterval);
    
  };
  ws.onerror = e => { log("WebSocket error: " + e.message); };
}

function sendText(msg) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  const safe = sanitizeText(msg);
  if (safe === "") return;

  if (!username) {
    ws.send(safe);
    log(safe);
    return;
  }

  if (currentTarget) {
    const payload = { target: currentTarget, message: safe };
    ws.send(JSON.stringify(payload));
    log(`To ${currentTarget}: ${safe}`);
  } else {
    log("No target selected.");
  }
}

import {
  ref as storageRef,
  uploadBytes,
  getDownloadURL
} from "https://www.gstatic.com/firebasejs/9.22.2/firebase-storage.js";

async function uploadFileToFirebase(file) {
  const path = `uploads/${Date.now()}_${file.name}`;
  const ref  = storageRef(window.storage, path);

  await uploadBytes(ref, file);
  return getDownloadURL(ref);
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

async function validateFile(file) {
  const maxSize    = 20 * 1024 * 1024;
  const allowedMIMEs = [
    "image/png", "image/jpeg",
    "application/pdf", "text/plain"
  ];

  if (file.size > maxSize) throw new Error("File too big (max 20 MB).");

  if (!allowedMIMEs.includes(file.type)) {
    throw new Error(`Disallowed file type: ${file.type}`);
  }

  if (file.type === "text/plain") {
    const txt = await file.text();
    if (/<script[\s>]/i.test(txt)) {
      throw new Error("Text file contains forbidden <script> tags.");
    }
  }

  return true;
}
    document.addEventListener("DOMContentLoaded", () => {
        connect();
  document.getElementById("sendBtn").onclick = () => {
    const inp = document.getElementById("msgInput");
    const txt = inp.value.trim();
    if (txt) {
      sendText(txt);
      inp.value = "";
    }
  };

  document.getElementById("fileBtn").onclick = () => {
  const chooser = document.createElement("input");
  chooser.type = "file";

  chooser.onchange = async e => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      await validateFile(file);
      const url = await uploadFileToFirebase(file);
      const filePayload = {
        type:     "file_url",
        url:      url,
        filename: file.name
      };
      const envelope = {
        target:  currentTarget,
        message: JSON.stringify(filePayload)
      };
      ws.send(JSON.stringify(envelope));
      renderFileLink(url, file.name, `To ${currentTarget}: `);
    }
    catch (err) {
      alert("Upload blocked: " + err.message);
    }
  };

  chooser.click();
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
