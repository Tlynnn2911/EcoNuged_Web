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

async function loadKPI() {
    try {
        const res = await fetch('/api/kpi');
        const data = await res.json();
        const total = data.total || {};
        document.getElementById('kpiSummary').innerHTML = `
            <div class="stat"><i class="fas fa-truck"></i> <span>${safeNumber(total.tong_xe_giam_sat)}</span><small>Xe</small></div>
            <div class="stat"><i class="fas fa-cloud"></i> <span>${formatNumber(total.tong_co2_kg)}</span><small>kg CO₂</small></div>
            <div class="stat"><i class="fas fa-clock"></i> <span>${formatNumber(total.tong_gio_cho)}</span><small>giờ chờ</small></div>
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
    } catch (err) { console.error(err); }
}

let chart;
async function loadHeatmap() {
    try {
        const res = await fetch('/api/heatmap');
        const data = await res.json();
        const ports = data.ports || [];
        let co2Values = (data.co2 || []).map(v => Math.abs(safeNumber(v)));
        const ctx = document.getElementById('co2Chart').getContext('2d');
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
            type: 'bar',
            data: { labels: ports, datasets: [{ label: 'CO₂ (kg)', data: co2Values, backgroundColor: '#2c8c6e', borderRadius: 12 }] },
            options: { responsive: true, maintainAspectRatio: true, scales: { y: { beginAtZero: true, title: { display: true, text: 'kg CO₂' } } } }
        });
    } catch (err) { console.warn(err); }
}

async function runEconomicForecast() {
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
            <div class="economic-line"><i class="fas fa-percent"></i> <strong>Tỷ lệ giảm idling:</strong> ${tyLeGiam}%</div>
            <div class="economic-line"><i class="fas fa-message"></i> <strong>Thông điệp:</strong> ${thongDiep}</div>
        `;
        if (data.truoc_ap_dung && data.truoc_ap_dung.tong_gio_thang) {
            html += `<hr><div class="economic-line"><i class="fas fa-clock"></i> <strong>Tổng giờ idling/tháng:</strong> ${safeNumber(data.truoc_ap_dung.tong_gio_thang).toFixed(0)} giờ</div>`;
            html += `<div class="economic-line"><i class="fas fa-co2"></i> <strong>CO₂ hiện tại:</strong> ${safeNumber(data.truoc_ap_dung.tong_co2_kg).toFixed(2)} kg</div>`;
        }
        document.getElementById('economicResult').innerHTML = html;
    } catch (err) { document.getElementById('economicResult').innerHTML = `<div>Lỗi: ${err.message}</div>`; }
}

async function loadActualDataAndForecast() {
    try {
        const res = await fetch('/api/actual_statistics');
        const data = await res.json();
        if (data.so_xe > 0) {
            document.getElementById('soXe').value = data.so_xe;
            document.getElementById('soGio').value = data.trung_binh_gio_cho;
        }
        runEconomicForecast();
    } catch (err) {
        console.warn('Không lấy được dữ liệu thực tế, dùng mặc định');
        runEconomicForecast();
    }
}

document.getElementById('calcEconomicBtn').addEventListener('click', runEconomicForecast);
document.getElementById('exportExcelBtn').onclick = () => window.location.href = '/api/export/excel';
document.getElementById('exportPdfBtn').onclick = () => window.location.href = '/api/export/pdf';
document.getElementById('refreshBtn').onclick = () => { loadKPI(); loadHeatmap(); loadActualDataAndForecast(); };

loadKPI();
loadHeatmap();
loadActualDataAndForecast();