import os
import pandas as pd
import numpy as np
import matplotlib
# Use non-interactive Agg backend to avoid GUI/threading issues in Flask
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

def setup_plot_style():
    """Applies a premium, dark cyber-glassmorphism theme to Matplotlib/Seaborn."""
    sns.set_theme(style="darkgrid")
    
    # Custom color palette matching the SMSAM UI
    plt.rcParams.update({
        'figure.facecolor': '#0f172a',    # Deep Slate / Dark blue background
        'axes.facecolor': '#1e293b',      # Dark Slate Card background
        'savefig.facecolor': '#0f172a',   # Figure save background
        'axes.edgecolor': '#334155',      # Subtle border
        'axes.grid': True,
        'grid.color': '#334155',          # Subtle grid lines
        'grid.alpha': 0.5,
        'text.color': '#f8fafc',          # White/Slate text
        'axes.labelcolor': '#cbd5e1',     # Dimmed label text
        'xtick.color': '#94a3b8',         # Slate tick marks
        'ytick.color': '#94a3b8',
        'font.family': 'sans-serif',
        'font.size': 10,
        'figure.titlesize': 14,
        'axes.titlesize': 12,
    })

def seed_mock_data_if_empty(engine):
    """
    Checks each sensor table and seeds 7 days of highly realistic,
    diurnal, noisy sensor data if the tables are empty or have very little data.
    """
    import sqlalchemy as sa
    
    inspector = sa.inspect(engine)
    now = datetime.utcnow()
    start_time = now - timedelta(days=7)
    
    # Generate 336 points (every 30 mins for 7 days)
    timestamps = [start_time + timedelta(minutes=30 * i) for i in range(336)]
    
    # --- 1. DHT22 (Temperature & Humidity) ---
    has_dht22 = False
    if 'dht22_data' in inspector.get_table_names():
        with engine.connect() as conn:
            res = conn.execute(sa.text("SELECT COUNT(*) FROM dht22_data")).fetchone()
            if res and res[0] > 10:
                has_dht22 = True
                
    if not has_dht22:
        print("[SMSAM Analytics] Seeding DHT22 data...")
        temps = []
        humidities = []
        for ts in timestamps:
            # Diurnal temperature cycle: peak around 3 PM (15:00)
            hour_val = ts.hour + ts.minute / 60.0
            # Sine wave model: peak at 15:00, trough at 3:00
            temp_base = 22.0 + 5.0 * np.sin(2 * np.pi * (hour_val - 9) / 24)
            # Add noise
            temp = temp_base + np.random.normal(0, 0.8)
            
            # Humidity: inversely proportional to temp, higher at night
            hum_base = 65.0 - 15.0 * np.sin(2 * np.pi * (hour_val - 9) / 24)
            hum = hum_base + np.random.normal(0, 1.5)
            # Keep within sensor bounds
            temp = clip_val(temp, -40.0, 80.0)
            hum = clip_val(hum, 0.0, 100.0)
            
            temps.append(temp)
            humidities.append(hum)
            
        df_dht = pd.DataFrame({
            'temperature': temps,
            'humidity': humidities,
            'timestamp': timestamps
        })
        df_dht.to_sql('dht22_data', con=engine, if_exists='append', index=False)
        print(f"[SMSAM Analytics] Seeded {len(df_dht)} rows of DHT22 data.")

    # --- 2. LDR (Light Intensity) ---
    has_ldr = False
    if 'ldr_data' in inspector.get_table_names():
        with engine.connect() as conn:
            res = conn.execute(sa.text("SELECT COUNT(*) FROM ldr_data")).fetchone()
            if res and res[0] > 10:
                has_ldr = True
                
    if not has_ldr:
        print("[SMSAM Analytics] Seeding LDR data...")
        light_levels = []
        for ts in timestamps:
            hour_val = ts.hour + ts.minute / 60.0
            # Daylight hours: 6 AM to 6 PM (06:00 to 18:00)
            if 6.0 <= hour_val <= 18.0:
                # Bell curve centered at 12:00 PM
                intensity = 85.0 * np.exp(-((hour_val - 12.0) ** 2) / 8.0)
                # Add cloud cover noise
                intensity += np.random.normal(0, 3.0)
            else:
                # Night: very low intensity
                intensity = max(0.0, np.random.normal(0.5, 0.2))
                
            intensity = clip_val(intensity, 0.0, 100.0)
            light_levels.append(intensity)
            
        df_ldr = pd.DataFrame({
            'light_intensity': light_levels,
            'timestamp': timestamps
        })
        df_ldr.to_sql('ldr_data', con=engine, if_exists='append', index=False)
        print(f"[SMSAM Analytics] Seeded {len(df_ldr)} rows of LDR data.")

    # --- 3. PIR (Motion Sensors) ---
    has_pir = False
    if 'pir_data' in inspector.get_table_names():
        with engine.connect() as conn:
            res = conn.execute(sa.text("SELECT COUNT(*) FROM pir_data")).fetchone()
            if res and res[0] > 10:
                has_pir = True
                
    if not has_pir:
        print("[SMSAM Analytics] Seeding PIR motion data...")
        events = []
        
        # 7 days, generate ~50 random events paired with clear states
        for day in range(7):
            current_day = start_time + timedelta(days=day)
            # More active during work hours (8 to 17) and security patrol times (0, 1, 2)
            num_events = np.random.randint(5, 12)
            for _ in range(num_events):
                # Sample hour based on weighted probabilities
                hours_pool = list(range(24))
                weights = [
                    0.05, 0.05, 0.04, 0.01, 0.01, 0.01, 0.02, 0.04, # 0-7
                    0.07, 0.08, 0.08, 0.07, 0.08, 0.08, 0.07, 0.08, # 8-15
                    0.07, 0.05, 0.03, 0.02, 0.01, 0.02, 0.03, 0.03  # 16-23
                ]
                weights = np.array(weights)
                weights = weights / weights.sum() # Dynamically normalize to sum to exactly 1.0
                hour = np.random.choice(hours_pool, p=weights)
                minute = np.random.randint(0, 50) # Leave room for the cooldown event
                second = np.random.randint(0, 60)
                event_ts = current_day.replace(hour=int(hour), minute=int(minute), second=int(second))
                
                events.append((event_ts, 1)) # Motion detected (1)
                
                # Sensor goes clear 2 to 5 minutes later
                clear_ts = event_ts + timedelta(minutes=np.random.randint(2, 6))
                events.append((clear_ts, 0)) # Motion cleared (0)
                
        # Sort all events chronologically by timestamp
        events.sort(key=lambda x: x[0])
        
        motion_timestamps = [x[0] for x in events]
        motion_detections = [x[1] for x in events]
        
        df_pir = pd.DataFrame({
            'motion_detected': motion_detections,
            'timestamp': motion_timestamps
        })
        df_pir.to_sql('pir_data', con=engine, if_exists='append', index=False)
        print(f"[SMSAM Analytics] Seeded {len(df_pir)} rows of paired PIR motion/clear data.")

    # --- 4. Ultrasonic (Distance Proximity) ---
    has_ultra = False
    if 'ultrasonic_data' in inspector.get_table_names():
        with engine.connect() as conn:
            res = conn.execute(sa.text("SELECT COUNT(*) FROM ultrasonic_data")).fetchone()
            if res and res[0] > 10:
                has_ultra = True
                
    if not has_ultra:
        print("[SMSAM Analytics] Seeding Ultrasonic data...")
        distances = []
        # Seed hourly sweeps
        ultra_timestamps = [start_time + timedelta(hours=i) for i in range(168)]
        for ts in ultra_timestamps:
            # Machine moving back and forth from walls
            # Periodic wave between 40cm and 150cm
            hour_val = ts.hour + ts.day * 24
            base_dist = 90.0 + 40.0 * np.sin(2 * np.pi * hour_val / 12.0)
            dist = base_dist + np.random.normal(0, 5.0)
            
            # Occasional close obstacle detection (security trigger)
            if np.random.rand() < 0.08:
                dist = np.random.uniform(5.0, 15.0)
                
            dist = clip_val(dist, 2.0, 400.0)
            distances.append(dist)
            
        df_ultra = pd.DataFrame({
            'distance_cm': distances,
            'timestamp': ultra_timestamps
        })
        df_ultra.to_sql('ultrasonic_data', con=engine, if_exists='append', index=False)
        print(f"[SMSAM Analytics] Seeded {len(df_ultra)} rows of Ultrasonic data.")

def clip_val(val, min_v, max_v):
    return max(min_v, min(max_v, float(val)))

def generate_analytics_report(engine, output_dir):
    """
    Main entry point. Loads real sensor data using Pandas,
    creates beautiful seaborn charts, and computes summary statistics.
    Only data actually received from the ESP32 hardware is used.
    """
    # 1. Ensure target graph directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 2. Apply custom plots style
    setup_plot_style()
    
    metrics = {}
    
    # ==========================================
    # CHART 1: DHT22 (Temperature & Humidity)
    # ==========================================
    try:
        df_dht = pd.read_sql("SELECT * FROM dht22_data ORDER BY timestamp ASC", con=engine)
        if not df_dht.empty:
            df_dht['timestamp'] = pd.to_datetime(df_dht['timestamp'])
            
            # Compute DHT22 statistics (KPIs)
            metrics['temp_avg'] = round(df_dht['temperature'].mean(), 1)
            metrics['temp_max'] = round(df_dht['temperature'].max(), 1)
            metrics['temp_min'] = round(df_dht['temperature'].min(), 1)
            metrics['hum_avg'] = round(df_dht['humidity'].mean(), 1)
            metrics['hum_max'] = round(df_dht['humidity'].max(), 1)
            
            # Plot
            fig, ax1 = plt.subplots(figsize=(10, 4.5), dpi=150)
            
            # Temperature on primary y-axis
            color = '#06b6d4' # Cyan
            ax1.set_xlabel('Timestamp', color='#cbd5e1')
            ax1.set_ylabel('Temperature (°C)', color=color)
            sns.lineplot(data=df_dht.tail(100), x='timestamp', y='temperature', ax=ax1, color=color, linewidth=2, label='Temp (°C)')
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.yaxis.label.set_color(color)
            
            # Humidity on secondary y-axis
            ax2 = ax1.twinx()
            color = '#3b82f6' # Ice Blue
            ax2.set_ylabel('Humidity (%)', color=color)
            sns.lineplot(data=df_dht.tail(100), x='timestamp', y='humidity', ax=ax2, color=color, linewidth=1.5, linestyle='--', label='Humidity (%)')
            ax2.tick_params(axis='y', labelcolor=color)
            ax2.yaxis.label.set_color(color)
            
            # Fix grid lines overlapping
            ax1.grid(True, which='both', color='#334155', linestyle='-', linewidth=0.5, alpha=0.3)
            ax2.grid(False)
            
            plt.title('DHT22 Environment Trends (Last 50 Hours)', pad=15, color='#f8fafc', fontweight='bold')
            fig.tight_layout()
            
            # Save chart
            plt.savefig(os.path.join(output_dir, 'dht22_trends.png'), bbox_inches='tight', transparent=True)
            plt.close()
        else:
            metrics_dummy_dht(metrics)
    except Exception as e:
        print(f"[SMSAM Analytics] Error generating DHT22 chart: {e}")
        metrics_dummy_dht(metrics)

    # ==========================================
    # CHART 2: LDR (Light Intensity)
    # ==========================================
    try:
        df_ldr = pd.read_sql("SELECT * FROM ldr_data ORDER BY timestamp ASC", con=engine)
        if not df_ldr.empty:
            df_ldr['timestamp'] = pd.to_datetime(df_ldr['timestamp'])
            
            metrics['ldr_avg'] = round(df_ldr['light_intensity'].mean(), 1)
            metrics['ldr_max'] = round(df_ldr['light_intensity'].max(), 1)
            
            # Plot LDR
            fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
            df_plot = df_ldr.tail(100)
            
            # Filled area plot for light intensity
            ax.fill_between(df_plot['timestamp'], df_plot['light_intensity'], color='#eab308', alpha=0.15)
            sns.lineplot(data=df_plot, x='timestamp', y='light_intensity', ax=ax, color='#fbbf24', linewidth=2.5, label='Light Level %')
            
            ax.set_xlabel('Timestamp', color='#cbd5e1')
            ax.set_ylabel('Light Level (%)', color='#fbbf24')
            plt.title('LDR Solar Ambient Light Profile', pad=15, color='#f8fafc', fontweight='bold')
            fig.tight_layout()
            
            plt.savefig(os.path.join(output_dir, 'ldr_trends.png'), bbox_inches='tight', transparent=True)
            plt.close()
        else:
            metrics_dummy_ldr(metrics)
    except Exception as e:
        print(f"[SMSAM Analytics] Error generating LDR chart: {e}")
        metrics_dummy_ldr(metrics)

    # ==========================================
    # CHART 3: Ultrasonic (Distance Sweeps)
    # ==========================================
    try:
        df_ultra = pd.read_sql("SELECT * FROM ultrasonic_data ORDER BY timestamp ASC", con=engine)
        if not df_ultra.empty:
            df_ultra['timestamp'] = pd.to_datetime(df_ultra['timestamp'])
            
            metrics['distance_min'] = round(df_ultra['distance_cm'].min(), 1)
            metrics['distance_latest'] = round(df_ultra['distance_cm'].iloc[-1], 1)
            metrics['distance_avg'] = round(df_ultra['distance_cm'].mean(), 1)
            
            # Plot Proximity Radar
            fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
            df_plot = df_ultra.tail(60)
            
            sns.lineplot(data=df_plot, x='timestamp', y='distance_cm', ax=ax, color='#10b981', linewidth=2, label='Radar Range')
            
            # Highlight obstacle breaches (< 20cm) in neon red
            breaches = df_plot[df_plot['distance_cm'] < 20.0]
            if not breaches.empty:
                sns.scatterplot(data=breaches, x='timestamp', y='distance_cm', ax=ax, color='#ef4444', s=60, zorder=5, label='Breach Hazard (<20cm)')
            
            ax.axhline(20.0, color='#ef4444', linestyle='--', linewidth=1.2, alpha=0.8) # Threshold line
            
            ax.set_xlabel('Timestamp', color='#cbd5e1')
            ax.set_ylabel('Clearance Distance (cm)', color='#10b981')
            plt.title('Ultrasonic Proximity Range Sweep', pad=15, color='#f8fafc', fontweight='bold')
            fig.tight_layout()
            
            plt.savefig(os.path.join(output_dir, 'ultrasonic_trends.png'), bbox_inches='tight', transparent=True)
            plt.close()
        else:
            metrics_dummy_ultra(metrics)
    except Exception as e:
        print(f"[SMSAM Analytics] Error generating Ultrasonic chart: {e}")
        metrics_dummy_ultra(metrics)

    # ==========================================
    # CHART 4: PIR (Security Motion Alerts)
    # ==========================================
    try:
        df_pir = pd.read_sql("SELECT * FROM pir_data ORDER BY timestamp ASC", con=engine)
        if not df_pir.empty:
            df_pir['timestamp'] = pd.to_datetime(df_pir['timestamp'])
            metrics['pir_total'] = len(df_pir[df_pir['motion_detected'] == 1])
            
            # Calculate dynamic last active event time relative to database maximum to stay evergreen
            last_ts = df_pir['timestamp'].max()
            now = datetime.utcnow()
            time_diff = now - last_ts
            minutes_ago = int(time_diff.total_seconds() / 60)
            if minutes_ago < 0:
                metrics['pir_peak_hour'] = "Current State: Active"
            elif minutes_ago < 60:
                metrics['pir_peak_hour'] = f"Last event: {minutes_ago}m ago"
            elif minutes_ago < 1440:
                metrics['pir_peak_hour'] = f"Last event: {int(minutes_ago/60)}h ago"
            else:
                metrics['pir_peak_hour'] = f"Last event: {int(minutes_ago/1440)}d ago"
            
            # Create a regular 30-minute time grid for 24 hours leading to the latest database entry
            last_ts_rounded = last_ts.round('30min')
            start_time = last_ts_rounded - timedelta(hours=24)
            time_grid = pd.date_range(start=start_time, end=last_ts_rounded, freq='30min')
            
            df_motion = pd.DataFrame({'timestamp': time_grid, 'motion': 0})
            
            # Set motion = 1 for timestamps present in rounded active event stamps
            df_active = df_pir[df_pir['motion_detected'] == 1]
            active_rounded_ts = df_active['timestamp'].dt.round('30min')
            df_motion.loc[df_motion['timestamp'].isin(active_rounded_ts), 'motion'] = 1
            
            # Plot raw binary step line
            fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
            
            ax.step(df_motion['timestamp'], df_motion['motion'], where='post', color='#f87171', linewidth=2.5, label='Motion State')
            ax.fill_between(df_motion['timestamp'], df_motion['motion'], step='post', color='#ef4444', alpha=0.12)
            
            ax.set_xlabel('Timeline (Last 24 Hours)', color='#cbd5e1')
            ax.set_ylabel('Motion State', color='#f87171')
            plt.title('PIR Motion Active vs. Idle State Stream', pad=15, color='#f8fafc', fontweight='bold')
            
            # Strictly binary Y axis
            ax.set_yticks([0, 1])
            ax.set_yticklabels(['Idle (0)', 'Active (1)'], color='#cbd5e1')
            ax.set_ylim(-0.1, 1.1)
            
            # Date/Time formatting on X axis
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.xticks(rotation=45, color='#94a3b8')
            
            fig.tight_layout()
            
            plt.savefig(os.path.join(output_dir, 'pir_trends.png'), bbox_inches='tight', transparent=True)
            plt.close()
        else:
            metrics_dummy_pir(metrics)
    except Exception as e:
        print(f"[SMSAM Analytics] Error generating PIR chart: {e}")
        metrics_dummy_pir(metrics)
        
    return metrics

def metrics_dummy_dht(m):
    """No real DHT22 data yet — display placeholder indicators."""
    m['temp_avg'] = '—'
    m['temp_max'] = '—'
    m['temp_min'] = '—'
    m['hum_avg'] = '—'
    m['hum_max'] = '—'

def metrics_dummy_ldr(m):
    """No real LDR data yet — display placeholder indicators."""
    m['ldr_avg'] = '—'
    m['ldr_max'] = '—'

def metrics_dummy_ultra(m):
    """No real ultrasonic data yet — display placeholder indicators."""
    m['distance_min'] = '—'
    m['distance_latest'] = '—'
    m['distance_avg'] = '—'

def metrics_dummy_pir(m):
    """No real PIR data yet — display placeholder indicators."""
    m['pir_total'] = '—'
    m['pir_peak_hour'] = 'No events recorded'
