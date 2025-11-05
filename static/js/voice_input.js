// Voice input functionality using Web Speech API
class VoiceInput {
    constructor(textareaId, buttonId) {
        this.textarea = document.getElementById(textareaId);
        this.button = document.getElementById(buttonId);
        this.recognition = null;
        this.isListening = false;

        this.init();
    }

    init() {
        // Check if browser supports Web Speech API
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Web Speech API not supported in this browser');
            this.button.style.display = 'none';
            return;
        }

        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US'; // Default to English, can be made configurable

        this.recognition.onstart = () => {
            this.isListening = true;
            this.button.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
            this.button.classList.add('recording');
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.textarea.value += (this.textarea.value ? ' ' : '') + transcript;
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.button.innerHTML = '<i class="fas fa-microphone"></i> Voice Input';
            this.button.classList.remove('recording');
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.button.innerHTML = '<i class="fas fa-microphone"></i> Voice Input';
            this.button.classList.remove('recording');
        };

        // Add click event to button
        this.button.addEventListener('click', () => {
            if (this.isListening) {
                this.recognition.stop();
            } else {
                this.recognition.start();
            }
        });
    }
}

// Initialize voice input when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new VoiceInput('prompt', 'voice-input-btn');
});
