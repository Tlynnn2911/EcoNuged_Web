// Helper: chuyển số an toàn, không ép về 0 nếu âm (để giữ nguyên dữ liệu gốc)
function safeNumber(value) {
    let num = Number(value);
    return isNaN(num) ? 0 : num;
}
function formatNumber(num, decimals = 2) {
    return safeNumber(num).toFixed(decimals);
}
function formatCurrency(vnd) {
    let val = safeNumber(vnd);
    return val.toLocaleString('vi-VN') + ' ₫';
}

// Biến timer
let startTime = null;
let timerInterval = null;
let isIdling = false;

// DOM elements
const vehicleIdInput = document.getElementById('vehicle_id');
const portNameSelect = document.getElementById('port_name');
const kmDrivenInput = document.getElementById('km_driven');
const startBtn = document.getElementById('startIdleBtn');
const endBtn = document.getElementById('endIdleBtn');
const timerDisplay = document.getElementById('timerDisplay');
const simulateResultDiv = document.getElementById('simulateResult');

// Cập nhật hiển thị timer
function updateTimerDisplay() {
    if (startTime && isIdling) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        timerDisplay.textContent = `${elapsed} giây`;
    } else {
        timerDisplay.textContent = `0 giây`;
    }
}

// Bắt đầu idling
startBtn.addEventListener('click', () => {
    if (isIdling) {
        simulateResultDiv.innerHTML = `<div><i class="fas fa-exclamation-triangle"></i> Xe đang trong quá trình chờ, hãy kết thúc trước khi bắt đầu mới.</div>`;
        return;
    }
    if (timerInterval) clearInterval(timerInterval);
    startTime = Date.now();
    isIdling = true;
    updateTimerDisplay();
    timerInterval = setInterval(updateTimerDisplay, 1000);
    startBtn.disabled = true;
    endBtn.disabled = false;
    simulateResultDiv.innerHTML = `<div><i class="fas fa-hourglass-start"></i> Đã ghi nhận xe vào cảng, bắt đầu tính thời gian chờ...</div>`;
});

// Kết thúc idling và gửi dữ liệu
endBtn.addEventListener('click', async () => {
    if (!isIdling || !startTime) return;
    
    const idleSeconds = Math.floor((Date.now() - startTime) / 1000);
    const vehicle_id = vehicleIdInput.value.trim();
    const port_name = portNameSelect.value;
    const km_driven = parseFloat(kmDrivenInput.value) || 0;
    
    if (idleSeconds <= 0) {
        simulateResultDiv.innerHTML = `<div><i class="fas fa-exclamation-triangle"></i> Thời gian chờ không hợp lệ.</div>`;
        return;
    }
    
    // Tạm thời vô hiệu nút để tránh gửi nhiều lần
    endBtn.disabled = true;
    startBtn.disabled = false;
    if (timerInterval) clearInterval(timerInterval);
    isIdling = false;
    startTime = null;
    
    const payload = {
        vehicle_id: vehicle_id,
        port_name: port_name,
        idle_seconds: idleSeconds,
        km_driven: km_driven
    };
    
    try {
        const res = await fetch('/api/simulate_idling', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        const co2 = safeNumber(result.co2_kg);
        const nudgeMsg = result.nudge?.canh_bao?.noi_dung || 'Đã ghi nhận thành công';
        
        let html = `
            <div><i class="fas fa-check-circle" style="color:#1b6e4e;"></i> <strong>✅ Đã ghi nhận sự kiện</strong></div>
            <div><i class="fas fa-clock"></i> <strong>Thời gian chờ thực tế:</strong> ${idleSeconds} giây (${(idleSeconds/60).toFixed(1)} phút)</div>
            <div><i class="fas fa-cloud"></i> <strong>CO₂ phát thải:</strong> ${co2.toFixed(2)} kg</div>
            <div><i class="fas fa-road"></i> <strong>Quãng đường đã chạy:</strong> ${km_driven} km</div>
            <div><i class="fas fa-bullhorn"></i> <strong>📢 Nudge:</strong> <em>${nudgeMsg.substring(0, 200)}</em></div>
        `;
        simulateResultDiv.innerHTML = html;
        timerDisplay.textContent = `0 giây`;
        loadKPI();
        loadHeatmap();
    } catch (err) {
        simulateResultDiv.innerHTML = `<div><i class="fas fa-exclamation-triangle"></i> Lỗi: ${err.message}</div>`;
        // Nếu lỗi, khôi phục trạng thái để thử lại
        endBtn.disabled = false;
        startBtn.disabled = true;
        startTime = Date.now();
        isIdling = true;
        timerInterval = setInterval(updateTimerDisplay, 1000);
    }
});

// ========== KPI và Heatmap ==========
async function loadKPI() {
    try {
        const res = await fetch('/api/kpi');
        const data = await res.json();
        const total = data.total || {};
        document.getElementById('kpiSummary').innerHTML = `
            <div class="stat"><i class="fas fa-truck"></i> <span>${safeNumber(total.tong_xe_giam_sat)}</span> <small>Xe giám sát</small></div>
            <div class="stat"><i class="fas fa-cloud"></i> <span>${formatNumber(total.tong_co2_kg)}</span> <small>kg CO₂</small></div>
            <div class="stat"><i class="fas fa-clock"></i> <span>${formatNumber(total.tong_gio_cho)}</span> <small>giờ chờ</small></div>
        `;
        const topList = document.getElementById('topDrivers');
        topList.innerHTML = '';
        if (data.top_drivers && data.top_drivers.length) {
            data.top_drivers.forEach(d => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${d.Hang}</strong> ${d.ID_Xe} <span>${safeNumber(d.Tong_Diem)} điểm</span> <small>${d.Huy_Hieu}</small>`;
                topList.appendChild(li);
            });
        } else {
            topList.innerHTML = '<li>Chưa có dữ liệu</li>';
        }
        document.getElementById('kpiTimestamp').innerHTML = `Cập nhật: ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        console.error('KPI error', err);
    }
}

let chart;
async function loadHeatmap() {
    try {
        const res = await fetch('/api/heatmap');
        const data = await res.json();
        const ports = data.ports || [];
        let co2Values = (data.co2 || []).map(v => Math.abs(safeNumber(v))); // lấy trị tuyệt đối để cột dương
        const ctx = document.getElementById('co2Chart').getContext('2d');
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ports,
                datasets: [{
                    label: 'CO₂ (kg)',
                    data: co2Values,
                    backgroundColor: '#2c8c6e',
                    borderRadius: 12,
                    barPercentage: 0.7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: { y: { beginAtZero: true, title: { display: true, text: 'kg CO₂' } } },
                plugins: { legend: { position: 'top' } }
            }
        });
    } catch (err) {
        console.warn('Heatmap error', err);
    }
}

// Dự báo kinh tế (hiển thị từng dòng)
document.getElementById('calcEconomicBtn').addEventListener('click', async () => {
    const soXe = parseInt(document.getElementById('soXe').value, 10);
    const soGio = parseFloat(document.getElementById('soGio').value);
    try {
        const res = await fetch(`/api/economic_analysis?so_xe=${soXe}&so_gio=${soGio}`);
        const data = await res.json();
        const tonThat = safeNumber(data.ton_that_hien_tai_vnd);
        const tietKiem = safeNumber(data.tiet_kiem_du_kien_vnd);
        const tyLeGiam = data.ty_le_giam_pct || 30;
        const thongDiep = data.roi_message || '';
        
        let html = `
            <div class="economic-line"><i class="fas fa-chart-line"></i> <strong>Tổn thất hiện tại:</strong> <span class="highlight">${formatCurrency(tonThat)}</span></div>
            <div class="economic-line"><i class="fas fa-sack-dollar"></i> <strong>Tiết kiệm dự kiến:</strong> <span class="highlight">${formatCurrency(tietKiem)}</span></div>
            <div class="economic-line"><i class="fas fa-percent"></i> <strong>Tỷ lệ giảm idling:</strong> <span class="highlight">${tyLeGiam}%</span></div>
            <div class="economic-line"><i class="fas fa-message"></i> <strong>Thông điệp:</strong> ${thongDiep}</div>
        `;
        if (data.truoc_ap_dung && data.truoc_ap_dung.tong_gio_thang) {
            html += `<hr>`;
            html += `<div class="economic-line"><i class="fas fa-clock"></i> <strong>Tổng giờ idling/tháng:</strong> ${safeNumber(data.truoc_ap_dung.tong_gio_thang).toFixed(0)} giờ</div>`;
            html += `<div class="economic-line"><i class="fas fa-co2"></i> <strong>CO₂ hiện tại:</strong> ${safeNumber(data.truoc_ap_dung.tong_co2_kg).toFixed(2)} kg</div>`;
        }
        document.getElementById('economicResult').innerHTML = html;
    } catch (err) {
        document.getElementById('economicResult').innerHTML = `<div class="economic-line"><i class="fas fa-exclamation-triangle"></i> Lỗi: ${err.message}</div>`;
    }
});

// Xuất báo cáo
document.getElementById('exportExcelBtn').onclick = () => window.location.href = '/api/export/excel';
document.getElementById('exportPdfBtn').onclick = () => window.location.href = '/api/export/pdf';
document.getElementById('refreshBtn').onclick = () => { loadKPI(); loadHeatmap(); };

// Khởi động
loadKPI();
loadHeatmap();