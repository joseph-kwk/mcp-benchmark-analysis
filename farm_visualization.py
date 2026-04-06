"""
🌾 Farm Visualization Dashboard
Beautiful, interactive farm simulation to demonstrate MCP vs Traditional AI integration

This creates a visual representation of our smart farm with:
- Real-time field monitoring
- Weather conditions
- Irrigation systems
- Performance metrics comparison
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import requests
import json


class SmartFarmVisualization:
    def __init__(self, root):
        self.root = root
        self.root.title("🌾 Mini Farm Dashboard - MCP Agriculture Project")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # Farm data
        self.fields_data = {
            "Field_A": {"moisture": 12, "crop": "corn", "status": "needs_irrigation", "color": "#e74c3c", "position": (0.1, 0.6)},
            "Field_B": {"moisture": 28, "crop": "wheat", "status": "healthy", "color": "#27ae60", "position": (0.6, 0.6)},
            "Field_C": {"moisture": 8, "crop": "soybean", "status": "critical", "color": "#c0392b", "position": (0.1, 0.1)},
            "Field_D": {"moisture": 45, "crop": "corn", "status": "healthy", "color": "#27ae60", "position": (0.6, 0.1)}
        }
        
        self.weather_conditions = [
            {"day": 1, "condition": "☀️ Sunny", "temp": 78, "precip": 10},
            {"day": 2, "condition": "☁️ Cloudy", "temp": 72, "precip": 40},
            {"day": 3, "condition": "🌧️ Rain", "temp": 65, "precip": 80}
        ]
        
        # Performance tracking
        self.mcp_performance = {"response_times": [], "success_rate": 98.5}
        self.traditional_performance = {"response_times": [], "success_rate": 94.2}
        
        self.setup_ui()
        self.start_simulation()
    
    def setup_ui(self):
        # Create main frames
        self.create_header()
        self.create_farm_view()
        self.create_control_panel()
        self.create_metrics_panel()
    
    def create_header(self):
        """Create the header with project title and status"""
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🌾 Mini Farm Dashboard", 
            font=('Arial', 24, 'bold'),
            bg='#34495e', 
            fg='#ecf0f1'
        )
        title_label.pack(side='left', padx=20, pady=20)
        
        subtitle_label = tk.Label(
            header_frame, 
            text="MCP vs Traditional Function Calling Comparison", 
            font=('Arial', 12),
            bg='#34495e', 
            fg='#bdc3c7'
        )
        subtitle_label.pack(side='left', padx=(0, 20), pady=20)
        
        # Status indicator
        status_frame = tk.Frame(header_frame, bg='#34495e')
        status_frame.pack(side='right', padx=20, pady=20)
        
        tk.Label(status_frame, text="System Status:", font=('Arial', 10), bg='#34495e', fg='#ecf0f1').pack()
        self.status_label = tk.Label(
            status_frame, 
            text="🟢 MCP Server Active", 
            font=('Arial', 10, 'bold'),
            bg='#34495e', 
            fg='#27ae60'
        )
        self.status_label.pack()
    
    def create_farm_view(self):
        """Create the main farm visualization"""
        farm_frame = tk.Frame(self.root, bg='#2c3e50')
        farm_frame.pack(side='left', fill='both', expand=True, padx=(10, 5), pady=5)
        
        # Farm plot using matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 6), facecolor='#2c3e50')
        self.ax.set_facecolor('#34495e')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_title('🚜 Mini Farm Layout', color='white', fontsize=16, fontweight='bold')
        
        # Draw fields
        self.field_patches = {}
        for field_id, data in self.fields_data.items():
            x, y = data['position']
            rect = patches.Rectangle(
                (x, y), 0.35, 0.35, 
                linewidth=3, 
                edgecolor='white', 
                facecolor=data['color'],
                alpha=0.7
            )
            self.ax.add_patch(rect)
            self.field_patches[field_id] = rect
            
            # Field labels
            self.ax.text(
                x + 0.175, y + 0.175, 
                f"{field_id}\n{data['crop'].title()}\n{data['moisture']}% 💧",
                ha='center', va='center', 
                color='white', fontweight='bold', fontsize=10
            )
        
        # Weather display
        self.ax.text(0.02, 0.95, "Weather Forecast:", transform=self.ax.transAxes, 
                    color='white', fontweight='bold', fontsize=12)
        for i, weather in enumerate(self.weather_conditions):
            self.ax.text(0.02, 0.88 - i*0.05, 
                        f"Day {weather['day']}: {weather['condition']} {weather['temp']}°F ({weather['precip']}% rain)",
                        transform=self.ax.transAxes, color='#ecf0f1', fontsize=9)
        
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, farm_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_control_panel(self):
        """Create control panel for interactions"""
        control_frame = tk.Frame(self.root, bg='#34495e', width=300)
        control_frame.pack(side='right', fill='y', padx=(5, 10), pady=5)
        control_frame.pack_propagate(False)
        
        # Title
        tk.Label(
            control_frame, 
            text="🎛️ Farm Controls", 
            font=('Arial', 14, 'bold'),
            bg='#34495e', 
            fg='#ecf0f1'
        ).pack(pady=(20, 10))
        
        # Field selection
        tk.Label(control_frame, text="Select Field:", bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=20)
        self.field_var = tk.StringVar(value="Field_A")
        field_combo = ttk.Combobox(control_frame, textvariable=self.field_var, 
                                  values=list(self.fields_data.keys()))
        field_combo.pack(fill='x', padx=20, pady=5)
        
        # Action buttons
        btn_frame = tk.Frame(control_frame, bg='#34495e')
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Button(btn_frame, text="💧 Check Irrigation", 
                 command=self.check_irrigation, bg='#3498db', fg='white').pack(fill='x', pady=2)
        tk.Button(btn_frame, text="📊 Get Field Status", 
                 command=self.get_field_status, bg='#e67e22', fg='white').pack(fill='x', pady=2)
        tk.Button(btn_frame, text="🌦️ Weather Update", 
                 command=self.update_weather, bg='#9b59b6', fg='white').pack(fill='x', pady=2)
        tk.Button(btn_frame, text="🔄 Run Benchmark", 
                 command=self.run_benchmark, bg='#e74c3c', fg='white').pack(fill='x', pady=2)
        
        # System comparison
        tk.Label(
            control_frame, 
            text="📈 System Comparison", 
            font=('Arial', 12, 'bold'),
            bg='#34495e', 
            fg='#ecf0f1'
        ).pack(pady=(20, 10))
        
        # MCP Stats
        mcp_frame = tk.Frame(control_frame, bg='#27ae60')
        mcp_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(mcp_frame, text="🚀 MCP Protocol", font=('Arial', 10, 'bold'), 
                bg='#27ae60', fg='white').pack()
        self.mcp_stats = tk.Label(mcp_frame, text="Success: 98.5% | Avg: 245ms", 
                                 bg='#27ae60', fg='white')
        self.mcp_stats.pack()
        
        # Traditional Stats
        trad_frame = tk.Frame(control_frame, bg='#e67e22')
        trad_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(trad_frame, text="⚙️ Traditional", font=('Arial', 10, 'bold'), 
                bg='#e67e22', fg='white').pack()
        self.trad_stats = tk.Label(trad_frame, text="Success: 94.2% | Avg: 312ms", 
                                  bg='#e67e22', fg='white')
        self.trad_stats.pack()
        
        # Activity Log
        tk.Label(
            control_frame, 
            text="📝 Activity Log", 
            font=('Arial', 12, 'bold'),
            bg='#34495e', 
            fg='#ecf0f1'
        ).pack(pady=(20, 5))
        
        self.log_text = tk.Text(control_frame, height=8, bg='#2c3e50', fg='#ecf0f1', 
                               font=('Courier', 9))
        self.log_text.pack(fill='both', padx=20, pady=5)
        
        # Add initial log entries
        self.log_activity("🌾 Mini Farm System Initialized")
        self.log_activity("🔌 MCP Server Connected")
        self.log_activity("📡 Sensors Online - 4 fields detected")
    
    def create_metrics_panel(self):
        """Create the metrics visualization panel"""
        pass  # We'll add performance charts here if needed
    
    def log_activity(self, message):
        """Add activity to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def check_irrigation(self):
        """Simulate irrigation check"""
        field = self.field_var.get()
        moisture = self.fields_data[field]["moisture"]
        
        self.log_activity(f"💧 Checking irrigation for {field}")
        time.sleep(0.5)  # Simulate API call
        
        if moisture < 15:
            recommendation = "URGENT: Irrigate immediately (600 gal/acre)"
            self.log_activity(f"🚨 {field}: {recommendation}")
        elif moisture < 30:
            recommendation = "Irrigate soon (300 gal/acre)"
            self.log_activity(f"⚠️ {field}: {recommendation}")
        else:
            recommendation = "No irrigation needed"
            self.log_activity(f"✅ {field}: {recommendation}")
    
    def get_field_status(self):
        """Get comprehensive field status"""
        field = self.field_var.get()
        data = self.fields_data[field]
        
        self.log_activity(f"📊 Retrieving status for {field}")
        time.sleep(0.3)
        
        status_msg = f"{field}: {data['crop']} | {data['moisture']}% moisture | Status: {data['status'].replace('_', ' ').title()}"
        self.log_activity(f"📋 {status_msg}")
    
    def update_weather(self):
        """Simulate weather update"""
        self.log_activity("🌦️ Updating weather forecast...")
        time.sleep(0.4)
        
        # Simulate some weather changes
        import random
        for i, weather in enumerate(self.weather_conditions):
            weather['temp'] += random.randint(-3, 3)
            weather['precip'] += random.randint(-5, 5)
            weather['precip'] = max(0, min(100, weather['precip']))
        
        self.log_activity("✅ Weather forecast updated")
        self.refresh_farm_display()
    
    def run_benchmark(self):
        """Run a system benchmark comparison"""
        self.log_activity("🔄 Running MCP vs Traditional benchmark...")
        
        def benchmark_thread():
            # Simulate MCP performance
            mcp_times = [np.random.normal(245, 50) for _ in range(10)]
            trad_times = [np.random.normal(312, 80) for _ in range(10)]
            
            avg_mcp = np.mean(mcp_times)
            avg_trad = np.mean(trad_times)
            
            improvement = ((avg_trad - avg_mcp) / avg_trad) * 100
            
            self.root.after(2000, lambda: self.log_activity(f"📈 Benchmark complete!"))
            self.root.after(2500, lambda: self.log_activity(f"🚀 MCP: {avg_mcp:.0f}ms avg"))
            self.root.after(3000, lambda: self.log_activity(f"⚙️ Traditional: {avg_trad:.0f}ms avg"))
            self.root.after(3500, lambda: self.log_activity(f"🎯 Performance improvement: {improvement:.1f}%"))
        
        threading.Thread(target=benchmark_thread, daemon=True).start()
    
    def refresh_farm_display(self):
        """Refresh the farm visualization"""
        # Clear and redraw weather info
        # This would update the matplotlib display
        self.canvas.draw()
    
    def start_simulation(self):
        """Start the real-time simulation updates"""
        def update_simulation():
            while True:
                # Simulate gradual moisture changes
                for field_id, data in self.fields_data.items():
                    # Moisture naturally decreases over time
                    data['moisture'] = max(5, data['moisture'] - np.random.uniform(0, 0.5))
                    
                    # Update field colors based on moisture
                    if data['moisture'] < 15:
                        data['color'] = '#e74c3c'  # Red - needs irrigation
                        data['status'] = 'needs_irrigation'
                    elif data['moisture'] < 30:
                        data['color'] = '#f39c12'  # Orange - monitor
                        data['status'] = 'monitor'
                    else:
                        data['color'] = '#27ae60'  # Green - healthy
                        data['status'] = 'healthy'
                
                time.sleep(10)  # Update every 10 seconds
        
        threading.Thread(target=update_simulation, daemon=True).start()


def main():
    root = tk.Tk()
    app = SmartFarmVisualization(root)
    root.mainloop()


if __name__ == "__main__":
    main()