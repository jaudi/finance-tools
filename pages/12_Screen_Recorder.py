import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Screen Recorder · FinancePlots",
    page_icon="🎥",
    layout="wide",
)

from mobile_css import inject_mobile_css
inject_mobile_css()

st.markdown("[← All Tools](/) &nbsp;", unsafe_allow_html=True)
st.title("🎥 Screen Recorder")
st.markdown(
    "Record your screen and download the video to share with colleagues. "
    "Everything runs in your browser — nothing is uploaded anywhere."
)
st.markdown("---")

components.html(
    """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: transparent;
    color: #1a1a1a;
    padding: 4px 0;
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    margin-bottom: 18px;
  }

  button {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
  }
  button:active { transform: scale(0.97); }
  button:disabled { opacity: 0.38; cursor: not-allowed; transform: none; }

  #startBtn  { background: #0066cc; color: #fff; }
  #startBtn:hover:not(:disabled) { background: #0052a3; }
  #stopBtn   { background: #dc2626; color: #fff; }
  #stopBtn:hover:not(:disabled)  { background: #b91c1c; }
  #pauseBtn  { background: #f59e0b; color: #fff; }
  #pauseBtn:hover:not(:disabled) { background: #d97706; }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    background: #f1f5f9;
    color: #64748b;
  }
  .badge.recording { background: #fee2e2; color: #dc2626; }
  .badge.paused    { background: #fef9c3; color: #92400e; }
  .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: none;
  }
  .badge.recording .dot { animation: blink 1s infinite; }
  @keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0 } }

  #timer { font-size: 0.82rem; font-weight: 700; color: #374151; min-width: 42px; }

  /* options row */
  .options {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 18px;
    align-items: center;
  }
  .opt-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #374151;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  select {
    padding: 5px 10px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 0.82rem;
    background: #fff;
    color: #1a1a1a;
  }
  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #374151;
    cursor: pointer;
  }

  /* preview */
  #preview-wrap {
    position: relative;
    background: #0f172a;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 18px;
    display: none;
    min-height: 80px;
  }
  #preview {
    width: 100%;
    max-height: 280px;
    display: block;
    object-fit: contain;
  }
  .preview-label {
    position: absolute;
    top: 8px; left: 10px;
    font-size: 0.72rem;
    font-weight: 700;
    color: rgba(255,255,255,0.55);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  /* recordings list */
  #recordings { display: flex; flex-direction: column; gap: 12px; }

  .rec-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
  }
  .rec-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;
  }
  .rec-name { font-size: 0.88rem; font-weight: 700; color: #1e293b; }
  .rec-meta { font-size: 0.78rem; color: #64748b; }
  .rec-actions { display: flex; gap: 8px; flex-wrap: wrap; }

  .btn-sm {
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  .btn-download { background: #0066cc; color: #fff; }
  .btn-download:hover { background: #0052a3; }
  .btn-delete   { background: #fff; color: #dc2626; border: 1px solid #fca5a5; }
  .btn-delete:hover { background: #fee2e2; }
  .btn-copy     { background: #fff; color: #0066cc; border: 1px solid #bfdbfe; }
  .btn-copy:hover { background: #eff6ff; }

  video.rec-video {
    width: 100%;
    max-height: 220px;
    border-radius: 6px;
    background: #0f172a;
    margin-top: 6px;
    display: block;
  }

  .info-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #1e40af;
    margin-bottom: 18px;
    line-height: 1.55;
  }
  .empty-state {
    text-align: center;
    padding: 30px 0 10px;
    color: #94a3b8;
    font-size: 0.88rem;
  }
</style>
</head>
<body>

<div class="info-box">
  ℹ️ Your browser will ask you to choose what to share (entire screen, a window, or a tab).
  Recordings stay entirely in your browser — nothing is sent to any server.
</div>

<!-- Options -->
<div class="options">
  <label class="opt-label">
    Quality:
    <select id="qualitySelect">
      <option value="2500000">High (2.5 Mbps)</option>
      <option value="1000000" selected>Standard (1 Mbps)</option>
      <option value="400000">Low (400 Kbps)</option>
    </select>
  </label>
  <label class="checkbox-label">
    <input type="checkbox" id="audioCheck" checked>
    Include microphone audio
  </label>
  <label class="checkbox-label">
    <input type="checkbox" id="sysAudioCheck" checked>
    Include system audio
  </label>
</div>

<!-- Controls -->
<div class="controls">
  <button id="startBtn">▶ Start Recording</button>
  <button id="pauseBtn" disabled>⏸ Pause</button>
  <button id="stopBtn"  disabled>⏹ Stop</button>
  <span id="statusBadge" class="badge"><span class="dot"></span> Idle</span>
  <span id="timer">0:00</span>
</div>

<!-- Live preview -->
<div id="preview-wrap">
  <span class="preview-label">Live preview</span>
  <video id="preview" autoplay muted playsinline></video>
</div>

<!-- Saved recordings -->
<div id="recordings">
  <div class="empty-state" id="emptyState">No recordings yet — hit Start to begin.</div>
</div>

<script>
  let mediaRecorder = null;
  let chunks = [];
  let stream = null;
  let timerInterval = null;
  let elapsedSeconds = 0;
  let recIndex = 0;

  const startBtn   = document.getElementById('startBtn');
  const pauseBtn   = document.getElementById('pauseBtn');
  const stopBtn    = document.getElementById('stopBtn');
  const badge      = document.getElementById('statusBadge');
  const timerEl    = document.getElementById('timer');
  const previewWrap= document.getElementById('preview-wrap');
  const preview    = document.getElementById('preview');
  const recList    = document.getElementById('recordings');
  const emptyState = document.getElementById('emptyState');

  function formatTime(s) {
    const m = Math.floor(s / 60);
    const sec = String(s % 60).padStart(2, '0');
    return m + ':' + sec;
  }

  function setBadge(state) {
    badge.className = 'badge ' + state;
    const labels = { '': 'Idle', recording: '● Recording', paused: '⏸ Paused' };
    badge.innerHTML = '<span class="dot"></span> ' + (labels[state] || 'Idle');
  }

  function startTimer() {
    timerInterval = setInterval(() => {
      elapsedSeconds++;
      timerEl.textContent = formatTime(elapsedSeconds);
    }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
  }

  startBtn.onclick = async () => {
    try {
      const micAudio = document.getElementById('audioCheck').checked;
      const sysAudio = document.getElementById('sysAudioCheck').checked;
      const bitrate  = parseInt(document.getElementById('qualitySelect').value);

      stream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 30 },
        audio: sysAudio,
      });

      // Optionally mix in microphone
      if (micAudio) {
        try {
          const micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
          micStream.getAudioTracks().forEach(t => stream.addTrack(t));
        } catch(e) { /* mic denied — continue without */ }
      }

      // Stop recording automatically if user ends share via browser UI
      stream.getVideoTracks()[0].addEventListener('ended', () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
      });

      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')
        ? 'video/webm;codecs=vp9,opus'
        : MediaRecorder.isTypeSupported('video/webm')
        ? 'video/webm'
        : 'video/mp4';

      mediaRecorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: bitrate });
      chunks = [];

      mediaRecorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
      mediaRecorder.onstop = () => saveRecording(mimeType);

      mediaRecorder.start(1000);
      elapsedSeconds = 0;
      timerEl.textContent = '0:00';
      startTimer();

      preview.srcObject = stream;
      previewWrap.style.display = 'block';

      setBadge('recording');
      startBtn.disabled = true;
      pauseBtn.disabled = false;
      stopBtn.disabled  = false;

    } catch (err) {
      if (err.name !== 'NotAllowedError') {
        alert('Could not start recording: ' + err.message);
      }
    }
  };

  pauseBtn.onclick = () => {
    if (!mediaRecorder) return;
    if (mediaRecorder.state === 'recording') {
      mediaRecorder.pause();
      stopTimer();
      setBadge('paused');
      pauseBtn.textContent = '▶ Resume';
    } else if (mediaRecorder.state === 'paused') {
      mediaRecorder.resume();
      startTimer();
      setBadge('recording');
      pauseBtn.textContent = '⏸ Pause';
    }
  };

  stopBtn.onclick = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    stopTimer();
    preview.srcObject = null;
    previewWrap.style.display = 'none';
    setBadge('');
    timerEl.textContent = '0:00';
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    pauseBtn.textContent = '⏸ Pause';
    stopBtn.disabled  = true;
  };

  function saveRecording(mimeType) {
    const ext  = mimeType.includes('mp4') ? 'mp4' : 'webm';
    const blob = new Blob(chunks, { type: mimeType });
    const url  = URL.createObjectURL(blob);
    const now  = new Date();
    const ts   = now.toLocaleDateString('en-GB') + ' ' + now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    const dur  = formatTime(elapsedSeconds);
    const name = 'FinancePlots_Recording_' + (++recIndex);
    const size = (blob.size / 1024 / 1024).toFixed(1) + ' MB';

    emptyState.style.display = 'none';

    const card = document.createElement('div');
    card.className = 'rec-card';
    card.id = 'rec-' + recIndex;

    card.innerHTML = `
      <div class="rec-top">
        <div>
          <div class="rec-name">🎬 ${name}.${ext}</div>
          <div class="rec-meta">${ts} &nbsp;·&nbsp; ${dur} &nbsp;·&nbsp; ${size}</div>
        </div>
        <div class="rec-actions">
          <a class="btn-sm btn-download" href="${url}" download="${name}.${ext}">⬇ Download</a>
          <button class="btn-sm btn-delete" onclick="deleteRec('rec-${recIndex}', '${url}')">🗑 Delete</button>
        </div>
      </div>
      <video class="rec-video" src="${url}" controls></video>
    `;

    recList.insertBefore(card, recList.firstChild);
  }

  function deleteRec(id, url) {
    const card = document.getElementById(id);
    if (card) card.remove();
    URL.revokeObjectURL(url);
    if (!recList.querySelector('.rec-card')) {
      emptyState.style.display = '';
    }
  }
</script>
</body>
</html>
""",
    height=780,
    scrolling=True,
)
