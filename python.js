async function setupPyodide() {
    const status = document.getElementById("status");
    const setStatus = (msg) => { if (status) status.textContent = msg; };

    setStatus("Loading Pyodide…");
    const pyodide = await loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.4/full/",
    });

    setStatus("Loading Python packages (openai, httpx, ssl)…");
    await pyodide.loadPackage(["openai", "httpx", "ssl"]);

    const jsModule = {
        async displayResponse(response) {
            const chatbox = document.getElementById("chatbox");
            const div = document.createElement("div");
            div.className = "msg ai";
            div.innerHTML = `<strong>AI:</strong> `;
            div.appendChild(document.createTextNode(response));
            chatbox.appendChild(div);
            chatbox.scrollTop = chatbox.scrollHeight;
            setSending(false);
        },
        async displayError(message) {
            const chatbox = document.getElementById("chatbox");
            const div = document.createElement("div");
            div.className = "msg err";
            div.innerHTML = `<strong>Error:</strong> `;
            div.appendChild(document.createTextNode(message));
            chatbox.appendChild(div);
            chatbox.scrollTop = chatbox.scrollHeight;
            setSending(false);
        },
    };
    pyodide.registerJsModule("js_module", jsModule);

    setStatus("Fetching app bundle…");
    await pyodide.runPythonAsync(`
        from pyodide.http import pyfetch
        response = await pyfetch("build/app.tar.gz")
        await response.unpack_archive()
        from main import sender_message_proxy
    `);

    const apiKey = window.prompt("Please enter your OpenRouter API key:");
    if (!apiKey) {
        setStatus("No API key provided. Reload to try again.");
        return;
    }

    setStatus("Ready.");
    document.getElementById("app").hidden = false;

    const sendMessageToPython = pyodide.globals.get("sender_message_proxy");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    function setSending(isSending) {
        sendButton.disabled = isSending;
        userInput.disabled = isSending;
        sendButton.textContent = isSending ? "…" : "Send";
        if (!isSending) userInput.focus();
    }

    function send() {
        const text = userInput.value.trim();
        if (!text) return;
        userInput.value = "";

        const chatbox = document.getElementById("chatbox");
        const div = document.createElement("div");
        div.className = "msg you";
        div.innerHTML = `<strong>You:</strong> `;
        div.appendChild(document.createTextNode(text));
        chatbox.appendChild(div);
        chatbox.scrollTop = chatbox.scrollHeight;

        setSending(true);
        sendMessageToPython(apiKey, text);
    }

    sendButton.addEventListener("click", send);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") send();
    });
    userInput.focus();

    pyodide.runPythonAsync(`
        from main import main as py_main
        await py_main()
    `);
}

document.addEventListener("DOMContentLoaded", setupPyodide);
