// Helper
function safeNumber(value) {
    let num = Number(value);
    return isNaN(num) ? 0 : num;
}

let startTime = null;
let timerInterval = null;
let isIdling = false;

const vehicleIdInput = document.getElementById('vehicle_id');
const portNameSelect = document.getElementById('port_name');
const kmDrivenInput = document.getElementById('km_driven');
const startBtn = document.getElementById('startIdleBtn');
const endBtn = document.getElementById('endIdleBtn');
const timerDisplay = document.getElementById('timerDisplay');
const resultDiv = document.getElementById('simulateResult');

function updateTimerDisplay() {
    if (startTime && isIdling) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        timerDisplay.textContent = `${elapsed} giây`;
    } else {
        timerDisplay.textContent = `0 giây`;
    }
}

startBtn.addEventListener('click', () => {
    if (isIdling) {
        resultDiv.innerHTML = `<div><i class="fas fa-exclamation-triangle"></i> Xe đang chờ, hãy kết thúc trước.</div>`;
        return;
    }
    if (timerInterval) clearInterval(timerInterval);
    startTime = Date.now();
    isIdling = true;
    updateTimerDisplay();
    timerInterval = setInterval(updateTimerDisplay, 1000);
    startBtn.disabled = true;
    endBtn.disabled = false;
    resultDiv.innerHTML = `<div><i class="fas fa-hourglass-start"></i> Đã ghi nhận xe vào cảng, bắt đầu tính thời gian chờ...</div>`;
});

endBtn.addEventListener('click', async () => {
    if (!isIdling || !startTime) return;
    let idleSeconds = Math.floor((Date.now() - startTime) / 1000);
    if (idleSeconds < 0) idleSeconds = 0; // đảm bảo không âm

    const vehicle_id = vehicleIdInput.value.trim();
    const port_name = portNameSelect.value;
    const km_driven = parseFloat(kmDrivenInput.value) || 0;

    if (idleSeconds <= 0) {
        resultDiv.innerHTML = `<div><i class="fas fa-exclamation-triangle"></i> Thời gian chờ không hợp lệ (${idleSeconds} giây). Vui lòng thử lại.</div>`;
        // Reset lại timer để có thể bắt đầu lại
        endBtn.disabled = false;
        startBtn.disabled = true;
        startTime = Date.now();
        isIdling = true;
        timerInterval = setInterval(updateTimerDisplay, 1000);
        return;
    }

    endBtn.disabled = true;
    startBtn.disabled = false;
    if (timerInterval) clearInterval(timerInterval);
    isIdling = false;
    startTime = null;

    const payload = { vehicle_id, port_name, idle_seconds: idleSeconds, km_driven };
    try {
        const res = await fetch('/api/simulate_idling', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        const co2 = safeNumber(result.co2_kg);
        const nudgeMsg = result.nudge?.canh_bao?.noi_dung || 'Đã ghi nhận thành công';
        resultDiv.innerHTML = `
            <div><i class="fas fa-check-circle" style="color:#1b6e4e;"></i> <strong>✅ Đã ghi nhận</strong></div>
            <div><i class="fas fa-clock"></i> <strong>Thời gian chờ:</strong> ${idleSeconds} giây (${(idleSeconds/60).toFixed(1)} phút)</div>
            <div><i class="fas fa-cloud"></i> <strong>CO₂:</strong> ${co2.toFixed(2)} kg</div>
            <div><i class="fas fa-road"></i> <strong>Quãng đường:</strong> ${km_driven} km</div>
            <div><i class="fas fa-bullhorn"></i> <strong>Nudge:</strong> ${nudgeMsg.substring(0, 200)}</div>
        `;
        timerDisplay.textContent = `0 giây`;
    } catch (err) {
        resultDiv.innerHTML = `<div><i class="fas fa-exclamation-triangle"></i> Lỗi: ${err.message}</div>`;
        endBtn.disabled = false;
        startBtn.disabled = true;
        startTime = Date.now();
        isIdling = true;
        timerInterval = setInterval(updateTimerDisplay, 1000);
    }
});