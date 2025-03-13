// static/script.js
let stream;
let isMuted = false;
let isCameraOff = false;
let mediaRecorder;
let audioChunks = [];

async function startWebcam() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        video.muted = true;
        video.style.width = '100%';
        video.style.height = '100%';
        video.style.objectFit = 'cover';
        const selfVideo = document.getElementById('self-video');
        selfVideo.innerHTML = '';
        selfVideo.appendChild(video);

        // Set up MediaRecorder for audio
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        mediaRecorder.onstop = () => {
            // Audio recording stopped, handled in submitAnswer
        };
    } catch (err) {
        console.error("Error accessing webcam:", err);
        document.getElementById('self-video').innerHTML = 'Webcam not available';
    }
}

function toggleMute() {
    if (stream) {
        stream.getAudioTracks().forEach(track => {
            track.enabled = !track.enabled;
            isMuted = !track.enabled;
        });
        document.getElementById('mute-btn').innerText = isMuted ? '🎙️ Unmute Mic' : '🎙️ Mute Mic';
    }
}

function toggleCamera() {
    if (stream) {
        stream.getVideoTracks().forEach(track => {
            track.enabled = !track.enabled;
            isCameraOff = !track.enabled;
        });
        document.getElementById('camera-btn').innerText = isCameraOff ? '📷 Camera On' : '📷 Camera Off';
    }
}

async function startInterview() {
    const response = await fetch('/start_interview');
    const data = await response.json();
    updateQuestion(data);
}

async function nextQuestion() {
    const response = await fetch('/next_question');
    const data = await response.json();
    updateQuestion(data);
}

async function submitAnswer(question, index) {
    if (!mediaRecorder) return;

    // Start recording audio
    audioChunks = [];
    mediaRecorder.start();
    document.getElementById('subtitle').innerText = "Recording...";

    // Stop recording after 5 seconds
    setTimeout(async () => {
        mediaRecorder.stop();
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        // Send audio to backend (though we'll rely on backend recording for now)
        const response = await fetch('/submit_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, index })
        });
        const data = await response.json();

        // Display transcript as subtitle
        document.getElementById('subtitle').innerText = data.transcript;

        if (data.next) {
            setTimeout(nextQuestion, 2000);
        }
    }, 5000); // 5 seconds of recording
}

async function endInterview() {
    const response = await fetch('/end_interview');
    const data = await response.json();
    document.getElementById('interviewer-content').innerHTML = `<div>${data.message}. Video saved to ${data.video_file}</div>`;
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
}

function updateQuestion(data) {
    const content = document.getElementById('interviewer-content');
    if (data.done) {
        content.innerHTML = `<div>${data.question}</div>`;
        document.getElementById('subtitle').innerText = '';
        endInterview();
    } else {
        content.innerHTML = `
            <div>Question ${data.index}: ${data.question}</div>
            <button onclick="submitAnswer('${data.question}', ${data.index})">Submit Answer</button>
        `;
        document.getElementById('subtitle').innerText = ''; // Clear subtitle for new question
    }
}

document.getElementById('mute-btn').addEventListener('click', toggleMute);
document.getElementById('camera-btn').addEventListener('click', toggleCamera);
document.getElementById('disconnect-btn').addEventListener('click', endInterview);

window.onload = () => {
    startWebcam();
    startInterview();
};