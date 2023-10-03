import { handleUserInput } from './script.mjs';
import { franc } from 'https://esm.sh/franc@6?bundle'; //https://github.com/wooorm/franc
import { iso6393To1 } from './iso6393-to-bcp47.mjs';

//https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API/Using_the_Web_Speech_API#speech_recognition
var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
var isSpeakMode = false;
var isNowSpeaking = false;


export function textToSpeech(message, isByClicking) {
    //Only in speak mode the new message will be spoken automatically
    //every time when a new reply is received, this function will be called from script.mjs. 
    //But script.mjs doesn't hold the information whether it is speak mode now, so this condition will be checked here firstly

    if (isNowSpeaking && isByClicking) {
        console.log('User stopped the speaking');
        speechSynthesis.cancel();
        return;
    }

    if ((isSpeakMode || isByClicking)) {
        console.log('message to speak:', message);
        //https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisUtterance
        var utterance = new SpeechSynthesisUtterance();

        utterance.onstart = function (event) {
            console.log('Speech started');
            isNowSpeaking = true;
        };

        utterance.onend = function (event) {
            console.log('Speech ended');
            isNowSpeaking = false;
        };

        utterance.onerror = function (event) {
            //In tested chrome browser the speaking sometimes abrupts without calling onerror or onend
            //but with Edge it is ok.
            console.error('Speech synthesis error:', event.error);
            isNowSpeaking = false;
        };

        var detectedLanguage = franc(message);
        console.log("Detected language code by franc:", detectedLanguage);
        utterance.lang = mapISO6393toISO6391(detectedLanguage) || 'en-US';
        //for code "zh", chrome uses mandarin, and edge uses cantonese :O maybe use BCP47 language code will be exacter
        console.log("Language code in ISO639-1:", utterance.lang);
        utterance.text = message;
        utterance.rate = 1.3;
        speechSynthesis.speak(utterance);
    }
}

export function setUpSpeechRecognition() {
    recognition.continuous = true; // Enable continuous recognition

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
    };

    recognition.onstart = () => {
        console.log('Speech recognition started.');
    };

    recognition.addEventListener('result', (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Recognized text:', transcript);
        recognition.stop();
        let message = { value: transcript };
        handleUserInput(message);
    });
};


function toggleMode(btn) {
    console.log("Mode toggled. IsSpeakMode:", isSpeakMode);

    var speakModeDiv = document.getElementById('speak-mode-container');
    var writeModeDiv = document.getElementById('write-mode-container');

    if (isSpeakMode) {
        btn.textContent = 'Write Mode';
        speakModeDiv.style.display = 'block';
        writeModeDiv.style.display = 'none';

        var LanguageDropdown = document.getElementById("language-dropdown");
        LanguageDropdown.addEventListener('change', () => {
            //console.log('change language');
            setSpeechRecognitionLanguage(LanguageDropdown.value);
        });

        var audioInputIcon = document.getElementById("audio-input-icon");
        audioInputIcon.addEventListener('click', () => {
            recognition.start();
        });

        setUpSpeechRecognition();
        setSpeechRecognitionLanguage(LanguageDropdown.value);
    } else {
        btn.textContent = 'Speak Mode';
        speakModeDiv.style.display = 'none';
        writeModeDiv.style.display = 'block';
        var userInput = document.getElementById("user-input");
        userInput.focus();
    }
}

function setSpeechRecognitionLanguage(lang) {
    console.log('set language to: ', lang);
    recognition.lang = lang;
};


function mapISO6393toISO6391(iso6393Code) {
    return iso6393To1[iso6393Code];
}

document.addEventListener("DOMContentLoaded", function () {

    var modeToggleButton = document.getElementById("mode-toggle-button");

    modeToggleButton.addEventListener("click", function () {
        isSpeakMode = !isSpeakMode;
        toggleMode(modeToggleButton);
    });
});