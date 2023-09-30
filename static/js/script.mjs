import { textToSpeech } from './audio.mjs';

var speechSynthesis = 'speechSynthesis' in window;

export function handleUserInput(userInput) {
    var message = userInput.value;
    if (message.trim() !== "") {
        addMessage(message, "user");
        userInput.value = "";
        // TODO: sanitize input; avoid code injection
        // Send the message to your backend using AJAX or WebSocket
        fetch('/process-input', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })
            // and handle the response from the assistant
            .then((response) => response.json())
            .then((data) => {
                const reply = data.reply;
                if (reply === '' || reply === null) {
                    console.log('Received null response from backend.');
                }
                else {
                    addMessage(reply, 'assistant');
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    }
}

function addMessage(message, sender) {
    var messageElement = document.createElement("div");
    messageElement.classList.add("message");
    if (sender === "user") {
        messageElement.classList.add("user-input");
        messageElement.textContent = "You: " + message;
    } else if (sender === "assistant") {
        messageElement.classList.add("ai-message");
        messageElement.textContent = "AI: " + message; // BACKUP: render newlines: .replace(/(?:\r\n|\r|\n)/g, '<br>');
        if(speechSynthesis){
            textToSpeech(message);
            messageElement.addEventListener("click", function () {
                textToSpeech(message, true);
            });
            messageElement.addEventListener("contextmenu", function () { //on right click
                stopSpeak();
            });
        }
    }
    else {
        console.error('Unknown message sender:', sender);
        return;
    }

    conversation.appendChild(messageElement); //Why conversation can be accessed from here magically? 0_0 somewhere saved this as global?
    conversation.scrollTop = conversation.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function () {

    // ---------------- USER INTERACTION ----------------
    var conversation = document.getElementById("conversation");
    var userInput = document.getElementById("user-input");
    var buttonContainer = document.getElementById("button-container");
    var sendButton = document.getElementById("send-button");
    var closeButton = document.getElementById("close-button");
    var setRecordButton = document.getElementById("set-recording");
    var recordStatus = document.getElementById("recording-status");
    var recordInfo = document.getElementById("recording-info");
    var newSessionHint = document.getElementById("new-session-hint");    

    checkSpeakMode();
    chatStartUIChange();

    const featureFlags = {
        allowRecords: true
    };

    function checkSpeakMode() {
        var SpeechRecognition = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;

        if (!SpeechRecognition) {
            var modeToggleBtn = document.getElementById("mode-toggle-button");
            console.error('Speech recognition is not supported in this browser.');
            changeDivDisplay(modeToggleBtn, 'none');
        }
        if (!speechSynthesis) {
            console.error('Speech synthesis not supported in this browser.');
            var speakInfo = document.getElementById("speak-info");
            changeDivDisplay(speakInfo, 'none');
        }
    };

    sendButton.addEventListener("click", function () {
        handleUserInput(userInput);
        setFocusOnInput();
    });


    document.addEventListener("keydown", function (event) {
        if (event.shiftKey && event.key === "Enter") {
            event.preventDefault(); // Prevent form submission
            var currentCursorPosition = userInput.selectionStart; // Get current cursor position
            var inputValue = userInput.value;
            var newValue = inputValue.substring(0, currentCursorPosition) + "\r\n" + inputValue.substring(userInput.selectionEnd);
            userInput.value = newValue;
            userInput.setSelectionRange(currentCursorPosition + 1, currentCursorPosition + 1); // Set cursor position after the inserted newline
        }
        else if (event.key === "Enter") {
            event.preventDefault();
            handleUserInput(userInput);
            setFocusOnInput();
        }
    });

    function chatEndedUIChange() {
        changeDivDisableStatus(userInput, true);
        changeDivDisplay(buttonContainer, 'none');
        changeDivDisplay(recordInfo, 'none');
    }

    function chatStartUIChange() {
        changeDivDisplay(newSessionHint, 'none');
        changeDivDisableStatus(userInput, false);
        setFocusOnInput();
        changeDivDisplay(buttonContainer, 'flex');
        changeDivDisplay(recordInfo, 'block');
    }

    function setFocusOnInput() {
        userInput.focus();
    }

    function changeDivDisplay(div, display) {
        div.style.display = display;
    }

    function changeDivDisableStatus(div, disabled) {
        div.disabled = disabled;
    }

    function setRecord(flag) {
        const url = `/set-records?flag=${flag}`;
        fetch(url, {
            method: 'GET'
        })
            .then((response) => {
                if (response.status === 200) {
                    return response.json();
                } else {
                    console.error('Request failed with status:', response.status);
                }
            })
            .then((data) => {
                recordStatus.textContent = data.message;
                setRecordButton.textContent = featureFlags.allowRecords ? 'Disable recording' : 'Enable recording'
            });
    }

    function saveRecords() {
        fetch('/save-records', {
            method: 'GET'
        });
    }

    function close_session() {
        conversation.innerHTML = "";
        fetch('/close-session', {
            method: 'GET'
        });
        console.log('Session refreshed');
        refreshNewSession();
    }

    function refreshNewSession() {
        featureFlags.allowRecords = true; //enable chat recording by default
        chatStartUIChange();
        setRecord(featureFlags.allowRecords);

    }

    closeButton.addEventListener("click", function () {
        saveRecords();
        close_session();
    });

    setRecordButton.addEventListener("click", function () {
        featureFlags.allowRecords = !featureFlags.allowRecords;
        console.log("chat recording flag is now " + featureFlags.allowRecords);
        setRecord(featureFlags.allowRecords);
    })

    window.addEventListener('beforeunload', function (event) { //before browser is closed
        if(featureFlags.allowRecords){
            saveRecords();
        }
    });

    // ---------------- IDLE REFRESH ----------------
    const idleTimeoutDuration = 3 * 60 * 1000;
    let idleTimer;

    function startIdleTimer() {
        clearTimeout(idleTimer);
        idleTimer = setTimeout(function () {
            saveRecords();
            close_session();
        }, idleTimeoutDuration);
    }

    // Listen for clicks and input on the document
    document.addEventListener('click', startIdleTimer);
    document.addEventListener('input', startIdleTimer);
    
    // startIdleTimer(); // TODO: remove?


    // ---------------- INSTRUCTIONS FROM BACKEND ----------------
    var socket = io();
    socket.on('connect', function () {
        socket.emit('connection', { state: 'success' });
    });

    socket.on('instruction', function (instruction) {
        let type = instruction.type;
        if (type == 'refresh_session_timer') {
            addMessage(instruction.goodbye_msg, 'assistant');
            chatEndedUIChange();
            saveRecords();
            setTimeout(close_session, instruction.timer * 1000);  // TODO: clear timer if second call here
            changeDivDisplay(newSessionHint, 'block');
        }
        else {
            console.error('Unknown instruction:', type);
        }
    });


});
