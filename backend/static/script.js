/* ============================================================
   SMSAM — Logic & Simulation
   script.js
   ============================================================ */

/**
 * Live Clock
 */
function updateClock() {
    const el = document.getElementById('live-clock');
    if (!el) return;

    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    const time = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    
    el.textContent = time;
}

setInterval(updateClock, 1000);
updateClock();

/**
 * Sensor Simulation
 */
const sensorData = {
    temperature: { val: 24.5, min: 20, max: 35, statusId: 'temperature-status' },
    humidity: { val: 45.0, min: 30, max: 70, statusId: 'humidity-status' },
    distance: { val: 120, min: 10, max: 400, statusId: 'distance-status' },
    motion: { detected: false, statusId: 'motion-status' },
    ldr: { val: 85, min: 0, max: 100, statusId: 'ldr-status' }
};

function updateDashboard() {
    // Temperature
    sensorData.temperature.val += (Math.random() - 0.5) * 0.5;
    updateSensorElement('temperature', sensorData.temperature.val.toFixed(1), '%');
    
    // Humidity
    sensorData.humidity.val += (Math.random() - 0.5) * 1.0;
    updateSensorElement('humidity', sensorData.humidity.val.toFixed(1), '%');
    
    // Distance
    sensorData.distance.val += (Math.random() - 0.5) * 5.0;
    updateSensorElement('distance', Math.round(sensorData.distance.val), '%');

    // LDR
    sensorData.ldr.val += (Math.random() - 0.5) * 2.0;
    if (sensorData.ldr.val < 0) sensorData.ldr.val = 0;
    if (sensorData.ldr.val > 100) sensorData.ldr.val = 100;
    updateSensorElement('ldr', Math.round(sensorData.ldr.val), '%');
    const ldrStatusEl = document.getElementById('ldr-status');
    if (ldrStatusEl) {
        const isDark = sensorData.ldr.val < 30;
        ldrStatusEl.textContent = isDark ? 'DARK' : 'BRIGHT';
        ldrStatusEl.style.color = isDark ? 'var(--warning)' : 'var(--success)';
    }

    // Motion
    const motionDetected = Math.random() > 0.85;
    const motionValEl = document.getElementById('motion-val');
    const motionStatusEl = document.getElementById('motion-status');
    const motionBarEl = document.getElementById('motion-bar');
    
    if (motionValEl) motionValEl.textContent = motionDetected ? 'DETECTED' : 'CLEAR';
    if (motionBarEl) motionBarEl.style.width = motionDetected ? '100%' : '0%';
    if (motionStatusEl) {
        motionStatusEl.textContent = motionDetected ? 'ALERT' : 'NORMAL';
        motionStatusEl.style.color = motionDetected ? 'var(--danger)' : 'var(--success)';
    }

    if (motionDetected) {
        addAlert('Motion detected in sector A-1');
    }
}

function updateSensorElement(id, value, unit) {
    const valEl = document.getElementById(`${id}-val`);
    const barEl = document.getElementById(`${id}-bar`);
    if (valEl) valEl.textContent = value;
    if (barEl) {
        // Simple mapping for demo
        const pct = Math.min(100, Math.max(0, (value / 100) * 100)); 
        barEl.style.width = `${pct}%`;
    }
}

function addAlert(message) {
    const list = document.getElementById('alert-list');
    if (!list) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const item = document.createElement('div');
    item.style.cssText = `
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.9rem;
        animation: slideIn 0.3s ease-out;
    `;
    
    item.innerHTML = `
        <span>${message}</span>
        <span style="color: var(--text-muted); font-size: 0.75rem;">${time}</span>
    `;

    list.prepend(item);
    if (list.children.length > 5) list.lastChild.remove();
}

/**
 * Uptime
 */
let uptime = 0;
function updateUptime() {
    uptime++;
    const el = document.getElementById('uptime-counter');
    if (!el) return;

    const h = Math.floor(uptime / 3600);
    const m = Math.floor((uptime % 3600) / 60);
    const s = uptime % 60;
    const pad = n => String(n).padStart(2, '0');
    el.textContent = `${pad(h)}:${pad(m)}:${pad(s)}`;
}

/**
 * Initialize
 */
document.addEventListener('DOMContentLoaded', () => {
    // Start simulation if on dashboard
    if (document.getElementById('temperature-val')) {
        setInterval(updateDashboard, 3000);
        updateDashboard();
    }
    
    setInterval(updateUptime, 1000);
});

// Add keyframe for alert animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-10px); }
        to { opacity: 1; transform: translateX(0); }
    }
`;
document.head.appendChild(style);
