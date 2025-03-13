// static/js/script.js
let questionIndex = 0;
let questionSources = ["question.txt"];

async function startInterview() {
    console.log("Starting interview...");
    const response = await fetch('/start_interview');
    const data = await response.json();

    if (data.error) {
        console.error("Start interview error:", data.error);
        document.querySelector('.interviewer-content').innerText = "Error starting interview.";
        return;
    }

    console.log("Interview started:", data.message);
    document.querySelector('.interviewer-content').innerText = "Interview Started!";
    setupWebcam();
    getNextQuestion();
}

async function getNextQuestion() {
    console.log("Fetching next question...");
    const response = await fetch('/next_question');
    const data = await response.json();

    if (data.error) {
        console.error("Next question error:", data.error);
        return;
    }

    console.log("Question received:", data.question);
    document.querySelector('.interviewer-content').innerText = data.question;
    setTimeout(submitAnswer, 16000); // Wait 16s (15s recording + 1s buffer)
}

async function submitAnswer() {
    const question = document.querySelector('.interviewer-content').innerText;
    console.log("Submitting answer for:", question);
    const response = await fetch('/submit_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });
    const data = await response.json();

    if (data.error) {
        console.error("Submit answer error:", data.error);
        return;
    }

    console.log("Answer:", data.answer);
    if (data.keywords) {
        questionSources = data.sources;
        console.log(`Keywords: ${data.keywords.join(', ')} | Sources: ${data.sources.join(', ')}`);
    } else if (data.evaluation) {
        console.log(`Evaluation: ${data.evaluation}`);
    }

    if (questionIndex < 5) {
        getNextQuestion();
    } else {
        endInterview();
    }
}

async function endInterview() {
    console.log("Ending interview...");
    const response = await fetch('/end_interview');
    const data = await response.json();

    console.log("Interview ended:", data.message);
    document.querySelector('.interviewer-content').innerText = "Interview Ended. Thank you!";
    questionIndex = 0;
    questionSources = ["question.txt"];
    const video = document.querySelector('#self-video-stream');
    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
}

function setupWebcam() {
    console.log("Setting up webcam...");
    const video = document.createElement('video');
    video.id = 'self-video-stream';
    video.autoplay = true;
    video.style.width = '100%';
    video.style.height = '100%';
    video.style.objectFit = 'cover';

    const selfVideo = document.querySelector('.self-video');
    selfVideo.innerHTML = '';
    selfVideo.appendChild(video);

    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(stream => {
            console.log("Webcam stream acquired");
            video.srcObject = stream;
        })
        .catch(err => {
            console.error("Webcam error:", err);
            selfVideo.innerText = "Webcam unavailable: " + err.message;
        });
}

document.addEventListener('DOMContentLoaded', () => {
    const muteBtn = document.querySelector('.control-btn:nth-child(1)');
    const camBtn = document.querySelector('.control-btn:nth-child(2)');
    const disconnectBtn = document.querySelector('.control-btn.disconnect');

    muteBtn.addEventListener('click', () => {
        muteBtn.innerText = muteBtn.innerText.includes('Mute') ? '🎙️ Unmute Mic' : '🎙️ Mute Mic';
        console.log("Mic toggle clicked (not implemented)");
    });

    camBtn.addEventListener('click', () => {
        const video = document.querySelector('#self-video-stream');
        if (video && video.srcObject) {
            const tracks = video.srcObject.getVideoTracks();
            tracks.forEach(track => track.enabled = !track.enabled);
            camBtn.innerText = camBtn.innerText.includes('Off') ? '📷 Camera On' : '📷 Camera Off';
            console.log("Camera toggled");
        }
    });

    disconnectBtn.addEventListener('click', () => {
        console.log("Disconnect clicked");
        endInterview();
    });

    console.log("Page loaded, starting interview...");
    startInterview();
});