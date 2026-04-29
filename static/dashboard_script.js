function safeNumber(value) {
    let num = Number(value);
    return isNaN(num) ? 0 : Math.abs(num);
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

async function updateEconomicForecast() {
    const soXe = parseInt(document.getElementById('soXe').value, 10);
    const soGio = parseFloat(document.getElementById('soGio').value);
    if (soXe === 0 || soGio <= 0) {
        document.getElementById('economicResult').innerHTML = `<div class="economic-line"><i class="fas fa-info-circle"></i> Chưa có dữ liệu idling hợp lệ. Hãy tạo sự kiện từ App.</div>`;
        return;
    }
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

async function loadActualDataAndUpdate() {
    try {
        const res = await fetch('/api/actual_statistics');
        const data = await res.json();
        document.getElementById('soXe').value = data.so_xe;
        document.getElementById('soGio').value = data.trung_binh_gio_cho;
        await updateEconomicForecast();
    } catch (err) {
        console.warn('Không lấy được dữ liệu thực tế');
        updateEconomicForecast();
    }
}

document.getElementById('refreshBtn').addEventListener('click', () => {
    loadKPI();
    loadHeatmap();
    loadActualDataAndUpdate();
});

async function exportReport(type) {
    const btn = type === 'excel' ? document.getElementById('exportExcelBtn') : document.getElementById('exportPdfBtn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Đang xuất...`;
    btn.disabled = true;
    try {
        const res = await fetch(`/api/export/${type}`);
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: 'Lỗi không xác định' }));
            alert(`❌ Không thể xuất báo cáo:\n${err.error}`);
            return;
        }
        // Tải file thành công
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const disposition = res.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^"]+)"?/);
        a.download = match ? match[1] : `BaoCao_ESG.${type === 'excel' ? 'xlsx' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert(`❌ Lỗi kết nối: ${err.message}`);
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

document.getElementById('exportExcelBtn').onclick = () => exportReport('excel');
document.getElementById('exportPdfBtn').onclick = () => exportReport('pdf');

loadKPI();
loadHeatmap();
loadActualDataAndUpdate();