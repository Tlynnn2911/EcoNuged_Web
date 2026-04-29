// Hàm xử lý số an toàn: giữ nguyên giá trị thực (không ép về 0 nếu âm, nhưng để biểu đồ dùng Math.max)
function safeNumber(value) {
    let num = Number(value);
    return isNaN(num) ? 0 : num;
}

function formatNumber(num, decimals = 2) {
    return safeNumber(num).toFixed(decimals);
}

// Helper format tiền
function formatCurrency(vnd) {
    let val = safeNumber(vnd);
    return val.toLocaleString('vi-VN') + ' ₫';
}

// Cập nhật KPI
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

// Heatmap - đảm bảo cột từ dưới lên (bắt đầu từ 0) bằng cách lấy trị tuyệt đối nếu backend trả về âm (tạm thời fix)
let chart;
async function loadHeatmap() {
    try {
        const res = await fetch('/api/heatmap');
        const data = await res.json();
        const ports = data.ports || [];
        // Nếu giá trị CO₂ âm -> chuyển thành dương để cột vẫn hiển thị đúng hướng (hoặc có thể set 0 nếu muốn)
        let co2Values = (data.co2 || []).map(v => Math.abs(safeNumber(v)));
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

// Mô phỏng idling - hiển thị từng dòng với icon
document.getElementById('simulateForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        vehicle_id: document.getElementById('vehicle_id').value,
        port_name: document.getElementById('port_name').value,
        idle_seconds: parseFloat(document.getElementById('idle_seconds').value),
        km_driven: parseFloat(document.getElementById('km_driven').value)
    };
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> Đang xử lý...';
    try {
        const res = await fetch('/api/simulate_idling', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        const co2 = safeNumber(result.co2_kg);
        const nudgeMsg = result.nudge?.canh_bao?.noi_dung || 'Đã ghi nhận thành công';
        const tonThatMoiGio = result.nudge?.ton_that_kinh_te?.tien_mat_vnd_moi_gio || 0;
        
        let html = `
            <div><i class="fas fa-cloud"></i> <strong>CO₂ phát thải:</strong> ${co2.toFixed(2)} kg</div>
            <div><i class="fas fa-hourglass-half"></i> <strong>Thời gian chờ:</strong> ${payload.idle_seconds} giây</div>
            <div><i class="fas fa-road"></i> <strong>Quãng đường đã chạy:</strong> ${payload.km_driven} km</div>
            <div><i class="fas fa-bullhorn"></i> <strong>📢 Nudge:</strong> <em>${nudgeMsg.substring(0, 200)}</em></div>
        `;
        if (tonThatMoiGio > 0) {
            html += `<div><i class="fas fa-chart-line"></i> <strong>Ước tính tổn thất:</strong> ${formatCurrency(tonThatMoiGio)}/giờ</div>`;
        }
        document.getElementById('simulateResult').innerHTML = html;
        loadKPI();
        loadHeatmap();
    } catch (err) {
        document.getElementById('simulateResult').innerHTML = `<div><i class="fas fa-exclamation-triangle"></i> Lỗi: ${err.message}</div>`;
    } finally {
        btn.innerHTML = originalText;
    }
});

// Dự báo kinh tế
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
            html += `<hr class="economic-hr">`;
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