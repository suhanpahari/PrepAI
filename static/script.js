// static/script.js
let stream;
let isMuted = false;
let isCameraOff = false;

async function startWebcam() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        video.muted = true; // Mute to avoid audio feedback
        video.style.width = '100%'; // Fit to container width
        video.style.height = '100%'; // Fit to container height
        video.style.objectFit = 'cover'; // Ensure it fills the space without distortion
        const selfVideo = document.getElementById('self-video');
        selfVideo.innerHTML = ''; // Clear the placeholder text
        selfVideo.appendChild(video);
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
    const answer = "User response placeholder"; // Replace with actual audio transcription if integrated
    const response = await fetch('/submit_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer, question, index })
    });
    const data = await response.json();
    if (data.next) {
        setTimeout(nextQuestion, 2000); // Move to next question after 2 seconds
    }
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
        endInterview();
    } else {
        content.innerHTML = `
            <div>Question ${data.index}: ${data.question}</div>
            <button onclick="submitAnswer('${data.question}', ${data.index})">Submit Answer</button>
        `;
    }
}

document.getElementById('mute-btn').addEventListener('click', toggleMute);
document.getElementById('camera-btn').addEventListener('click', toggleCamera);
document.getElementById('disconnect-btn').addEventListener('click', endInterview);

window.onload = () => {
    startWebcam();
    startInterview();
};