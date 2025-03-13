// static/script.js
let stream;
let isMuted = false;
let isCameraOff = false;
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordingStartTime;

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

async function toggleRecording() {
    if (!mediaRecorder) return;

    if (!isRecording) {
        // Start recording
        audioChunks = [];
        mediaRecorder.start();
        recordingStartTime = Date.now();
        isRecording = true;
        document.getElementById('record-btn').innerText = 'Stop Recording';
        document.getElementById('subtitle').innerText = "Recording...";
        
        // Start transcription on the server side
        const currentQuestion = document.querySelector('#interviewer-content div').textContent;
        const questionMatch = currentQuestion.match(/Question (\d+): (.*)/);
        let question = questionMatch ? questionMatch[2] : currentQuestion;
        let index = questionMatch ? parseInt(questionMatch[1]) : 0;
        
        // Notify server that recording has started
        fetch('/start_recording', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, index })
        });
    } else {
        // Stop recording
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById('record-btn').innerText = 'Record Response';
        document.getElementById('subtitle').innerText = "Processing...";

        // Wait for audio data to be available
        mediaRecorder.onstop = async () => {
            const duration = (Date.now() - recordingStartTime) / 1000; // Duration in seconds
            const currentQuestion = document.querySelector('#interviewer-content div').textContent;
            const questionMatch = currentQuestion.match(/Question (\d+): (.*)/);
            let question = questionMatch ? questionMatch[2] : currentQuestion;
            let index = questionMatch ? parseInt(questionMatch[1]) : 0;
            
            // Create audio blob and send to server
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('question', question);
            formData.append('index', index);
            formData.append('duration', duration);
            
            try {
                const response = await fetch('/submit_audio', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                // Display transcript
                document.getElementById('subtitle').innerText = data.transcript;
                document.getElementById('submit-btn').disabled = false; // Enable submit button
            } catch (error) {
                console.error("Error submitting audio:", error);
                document.getElementById('subtitle').innerText = "Error processing audio";
            }
        };
    }
}

async function submitAnswer(question, index) {
    if (!recordingStartTime) {
        document.getElementById('subtitle').innerText = "Please record a response first.";
        return;
    }

    const duration = (Date.now() - recordingStartTime) / 1000; // Duration in seconds
    const response = await fetch('/submit_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            question, 
            index, 
            duration,
            transcript: document.getElementById('subtitle').innerText 
        })
    });
    const data = await response.json();

    document.getElementById('submit-btn').disabled = true; // Disable submit until next recording

    if (data.next) {
        setTimeout(nextQuestion, 2000);
    }
}

async function endInterview() {
    const response = await fetch('/end_interview');
    const data = await response.json();
    document.getElementById('interviewer-content').innerHTML = `<div>${data.message}. Video saved to ${data.video_file}</div>`;
    document.getElementById('subtitle').innerText = '';
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
            <button id="record-btn" onclick="toggleRecording()">Record Response</button>
            <button id="submit-btn" onclick="submitAnswer('${data.question}', ${data.index})" disabled>Submit</button>
        `;
        document.getElementById('subtitle').innerText = '';
        isRecording = false;
        recordingStartTime = null;
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
    }
}

document.getElementById('mute-btn').addEventListener('click', toggleMute);
document.getElementById('camera-btn').addEventListener('click', toggleCamera);
document.getElementById('disconnect-btn').addEventListener('click', endInterview);

window.onload = () => {
    startWebcam();
    startInterview();
};