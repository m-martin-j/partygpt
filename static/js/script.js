document.addEventListener("DOMContentLoaded", function() {

    // ---------------- USER INTERACTION ----------------
    var conversation = document.getElementById("conversation");
    var userInput = document.getElementById("user-input");
    var sendButton = document.getElementById("send-button");
    var closeButton = document.getElementById("close-button");


    function setFocusOnInput() {
        userInput.focus();
    }

    setFocusOnInput();


    function addMessage(message, sender) {
        var messageElement = document.createElement("div");
        messageElement.classList.add("message");
        if (sender === "user") {
          messageElement.classList.add("user-input");
          messageElement.textContent = "You: " + message;
        } else if (sender === "assistant") {
          messageElement.classList.add("ai-message");
          messageElement.textContent = "AI: " + message; // BACKUP: render newlines: .replace(/(?:\r\n|\r|\n)/g, '<br>');
        }
        else {
            console.error('Unknown message sender:', sender);
            return;
        }
        conversation.appendChild(messageElement);
        conversation.scrollTop = conversation.scrollHeight;
        setFocusOnInput();
    }


    function handleUserInput() {
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


    sendButton.addEventListener("click", function() {
        handleUserInput();
    });


    document.addEventListener("keydown", function(event) {
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
            handleUserInput();
        }
    });


    function lockInputField() {
        userInput.disabled = true;
    }


    function unlockInputField() {
        userInput.disabled = false;
    }

    function saveRecords() {
        fetch('/save-records', {
            method: 'GET'
        });
    }

    function close_session(){
        conversation.innerHTML = "";
        fetch('/close-session', {
            method: 'GET'
        });
        console.log('Session refreshed');
        unlockInputField();
        setFocusOnInput();
    }


    closeButton.addEventListener("click", function() {
        saveRecords();
        close_session();
    });



    // ---------------- IDLE REFRESH ----------------
    const idleTimeoutDuration = 3 * 60 * 1000;
    let idleTimer;

    function startIdleTimer() {
        clearTimeout(idleTimer);
        idleTimer = setTimeout (function () {
            saveRecords();
            close_session();
          }, idleTimeoutDuration);
    }

    const inputElements = document.querySelectorAll('input, textarea');
    inputElements.forEach(function (input) {
        input.addEventListener('input', startIdleTimer);
    });

    // startIdleTimer(); // TODO: remove?




    // ---------------- INSTRUCTIONS FROM BACKEND ----------------
    var socket = io();
    socket.on('connect', function() {
        socket.emit('connection', {state: 'success'});
    });

    socket.on('instruction', function(instruction) {
        type = instruction.type
        if (type == 'refresh_session_timer') {
            addMessage(instruction.goodbye_msg, 'assistant');
            saveRecords();
            lockInputField();
            setTimeout(close_session, instruction.timer * 1000);  // TODO: clear timer if second call here
        }
        else {
            console.error('Unknown instruction:', type);
        }
    });


  });
