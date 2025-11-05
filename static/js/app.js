// static/js/app.js
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const messagesEl = document.getElementById("messages");

function appendMessage(text, who = "bot") {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${who}`;

  const msg = document.createElement("div");
  msg.textContent = text;
  wrapper.appendChild(msg);

  const time = document.createElement("div");
  time.className = "timestamp";
  const now = new Date();
  time.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  wrapper.appendChild(time);

  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showThinking() {
  const thinking = document.createElement("div");
  thinking.className = "message bot";
  thinking.id = "thinking-msg";
  thinking.innerHTML = `<span class="dots">Thinking<span>.</span><span>.</span><span>.</span></span>`;
  messagesEl.appendChild(thinking);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeThinking() {
  const t = document.getElementById("thinking-msg");
  if (t) t.remove();
}

async function sendQuery() {
  const q = inputEl.value.trim();
  if (!q) return;
  appendMessage(q, "user");
  inputEl.value = "";
  sendBtn.disabled = true;

  showThinking();

  try {
    const resp = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q }),
    });

    const data = await resp.json();
    removeThinking();

    if (!data.ok) {
      appendMessage("Error: " + (data.error || "Something went wrong."), "bot");
      return;
    }

    const result = data.result;
    const reply =
      result.tool_result ||
      result.rag_answer ||
      "I'm sorry, I couldn't find the requested information.";
    appendMessage(reply, "bot");
  } catch (err) {
    removeThinking();
    appendMessage("Error: " + err.message, "bot");
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

sendBtn.addEventListener("click", sendQuery);

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendQuery();
  }
});
