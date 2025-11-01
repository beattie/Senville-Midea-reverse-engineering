#!/usr/bin/env python3
"""
Senville AC Control - Desktop GUI
Simple desktop application for controlling your Senville/Midea mini-split AC
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from pathlib import Path
from datetime import datetime
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import check moved to after potential venv activation
# These imports will fail with clear error if libraries missing
from midea_beautiful import appliance_state
from dotenv import load_dotenv


class SenvilleGUI:
    """Main GUI application for Senville AC control"""

    def __init__(self, root):
        self.root = root
        self.root.title("Senville AC Control")
        self.root.geometry("600x700")
        self.root.resizable(False, False)

        # Load configuration
        self.load_config()

        # State variables
        self.device = None
        self.current_state = None
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = 5  # seconds
        self.refresh_thread = None
        self.running = True
        self.temp_slider_active = False  # Track if user is adjusting slider

        # Create GUI
        self.create_widgets()

        # Initial status check
        self.refresh_status()

        # Start auto-refresh
        self.start_auto_refresh()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        """Load configuration from .env file"""
        env_path = Path(__file__).parent / '.env'

        if not env_path.exists():
            messagebox.showerror(
                "Configuration Error",
                f".env file not found at {env_path}\n\n"
                "Please create .env from .env.example and configure your device."
            )
            sys.exit(1)

        load_dotenv(env_path)

        self.ip = os.getenv('SENVILLE_IP')
        self.token = os.getenv('SENVILLE_TOKEN')
        self.key = os.getenv('SENVILLE_KEY')

        if not all([self.ip, self.token, self.key]):
            messagebox.showerror(
                "Configuration Error",
                "Missing required configuration in .env:\n"
                "- SENVILLE_IP\n"
                "- SENVILLE_TOKEN\n"
                "- SENVILLE_KEY"
            )
            sys.exit(1)

    def create_widgets(self):
        """Create all GUI widgets"""

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Senville AC Control",
            font=('Helvetica', 18, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Device info
        device_label = ttk.Label(
            main_frame,
            text=f"Device: {self.ip}",
            font=('Helvetica', 10)
        )
        device_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Status Frame
        self.create_status_frame(main_frame)

        # Controls Frame
        self.create_controls_frame(main_frame)

        # Action Buttons Frame
        self.create_action_buttons(main_frame)

        # Status bar
        self.status_bar = ttk.Label(
            main_frame,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def create_status_frame(self, parent):
        """Create status display frame"""
        status_frame = ttk.LabelFrame(parent, text="Current Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))

        # Status labels
        self.status_labels = {}

        status_items = [
            ('power', 'Power:'),
            ('mode', 'Mode:'),
            ('target_temp', 'Target Temp:'),
            ('indoor_temp', 'Indoor Temp:'),
            ('fan_speed', 'Fan Speed:'),
            ('vswing', 'V-Swing:'),
            ('hswing', 'H-Swing:'),
        ]

        for idx, (key, label) in enumerate(status_items):
            ttk.Label(status_frame, text=label, font=('Helvetica', 10, 'bold')).grid(
                row=idx, column=0, sticky=tk.W, padx=(0, 10), pady=3
            )
            value_label = ttk.Label(status_frame, text="--", font=('Helvetica', 10))
            value_label.grid(row=idx, column=1, sticky=tk.W, pady=3)
            self.status_labels[key] = value_label

        # Last updated
        ttk.Label(status_frame, text="Last Updated:", font=('Helvetica', 9)).grid(
            row=len(status_items), column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0)
        )
        self.last_updated_label = ttk.Label(status_frame, text="--", font=('Helvetica', 9))
        self.last_updated_label.grid(row=len(status_items), column=1, sticky=tk.W, pady=(10, 0))

    def create_controls_frame(self, parent):
        """Create control widgets frame"""
        controls_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        controls_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))

        # Power control
        ttk.Label(controls_frame, text="Power:", font=('Helvetica', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        power_frame = ttk.Frame(controls_frame)
        power_frame.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Button(power_frame, text="ON", command=lambda: self.set_power(True), width=8).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(power_frame, text="OFF", command=lambda: self.set_power(False), width=8).pack(side=tk.LEFT)

        # Mode control
        ttk.Label(controls_frame, text="Mode:", font=('Helvetica', 10, 'bold')).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.mode_var = tk.StringVar(value="auto")
        mode_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.mode_var,
            values=['auto', 'cool', 'heat', 'dry', 'fan'],
            state='readonly',
            width=15
        )
        mode_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        mode_combo.bind('<<ComboboxSelected>>', lambda e: self.set_mode())

        # Temperature control
        ttk.Label(controls_frame, text="Temperature:", font=('Helvetica', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )

        temp_frame = ttk.Frame(controls_frame)
        temp_frame.grid(row=2, column=1, sticky=tk.W, pady=5)

        self.temp_var = tk.IntVar(value=72)
        self.temp_scale = tk.Scale(
            temp_frame,
            from_=60,
            to=87,
            orient=tk.HORIZONTAL,
            variable=self.temp_var,
            length=200,
            command=self.on_temp_change
        )
        self.temp_scale.pack(side=tk.LEFT)

        # Bind to ButtonPress and ButtonRelease to track slider interaction
        self.temp_scale.bind("<ButtonPress-1>", self.on_temp_press)
        self.temp_scale.bind("<ButtonRelease-1>", self.on_temp_release)

        self.temp_label = ttk.Label(temp_frame, text="72°F", font=('Helvetica', 10, 'bold'))
        self.temp_label.pack(side=tk.LEFT, padx=(10, 0))

        # Unit toggle
        self.temp_unit = tk.StringVar(value="F")
        ttk.Radiobutton(
            temp_frame,
            text="°F",
            variable=self.temp_unit,
            value="F",
            command=self.update_temp_scale
        ).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(
            temp_frame,
            text="°C",
            variable=self.temp_unit,
            value="C",
            command=self.update_temp_scale
        ).pack(side=tk.LEFT)

        # Fan speed control
        ttk.Label(controls_frame, text="Fan Speed:", font=('Helvetica', 10, 'bold')).grid(
            row=3, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.fan_var = tk.StringVar(value="Auto")
        fan_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.fan_var,
            values=['Auto', 'Low', 'Med-Low', 'Medium', 'Med-High', 'High'],
            state='readonly',
            width=15
        )
        fan_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        fan_combo.bind('<<ComboboxSelected>>', lambda e: self.set_fan_speed())

        # Swing controls
        ttk.Label(controls_frame, text="Vertical Swing:", font=('Helvetica', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.vswing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            controls_frame,
            text="Enable",
            variable=self.vswing_var,
            command=self.set_vswing
        ).grid(row=4, column=1, sticky=tk.W, pady=5)

        ttk.Label(controls_frame, text="Horizontal Swing:", font=('Helvetica', 10, 'bold')).grid(
            row=5, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.hswing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            controls_frame,
            text="Enable",
            variable=self.hswing_var,
            command=self.set_hswing
        ).grid(row=5, column=1, sticky=tk.W, pady=5)

    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Refresh Status",
            command=self.refresh_status,
            width=20
        ).pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(
            button_frame,
            text="Auto-refresh (5s)",
            variable=self.auto_refresh,
            command=self.toggle_auto_refresh
        ).pack(side=tk.LEFT, padx=5)

    def update_temp_scale(self):
        """Update temperature scale for F/C"""
        current_temp = self.temp_var.get()

        if self.temp_unit.get() == "C":
            # Switch to Celsius
            self.temp_scale.configure(from_=16, to=31)
            # Convert F to C
            if current_temp > 31:  # Was in F
                current_temp = int((current_temp - 32) * 5 / 9)
            self.temp_var.set(current_temp)
        else:
            # Switch to Fahrenheit
            self.temp_scale.configure(from_=60, to=87)
            # Convert C to F
            if current_temp < 60:  # Was in C
                current_temp = int(current_temp * 9 / 5 + 32)
            self.temp_var.set(current_temp)

        self.on_temp_change(None)

    def on_temp_change(self, value):
        """Handle temperature slider change (just update label)"""
        temp = self.temp_var.get()
        unit = self.temp_unit.get()
        self.temp_label.config(text=f"{temp}°{unit}")

    def on_temp_press(self, event):
        """Handle temperature slider press (start dragging)"""
        self.temp_slider_active = True

    def on_temp_release(self, event):
        """Handle temperature slider release (actually set temperature)"""
        self.temp_slider_active = False
        self.set_temperature()

    def get_device(self):
        """Get or create device connection"""
        try:
            if self.device is None:
                self.device = appliance_state(
                    address=self.ip,
                    token=self.token,
                    key=self.key
                )
            return self.device
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to device:\n{str(e)}")
            return None

    def refresh_status(self):
        """Refresh device status"""
        self.update_status_bar("Refreshing status...")

        def refresh_thread():
            try:
                device = self.get_device()
                if device:
                    state = device.state
                    self.current_state = state

                    # Update UI in main thread
                    self.root.after(0, self.update_status_display, state)
            except Exception as e:
                self.root.after(0, self.update_status_bar, f"Error: {str(e)}")

        threading.Thread(target=refresh_thread, daemon=True).start()

    def update_status_display(self, state):
        """Update status display with device state"""
        try:
            # Power
            power_text = "ON" if state.running else "OFF"
            self.status_labels['power'].config(
                text=power_text,
                foreground='green' if state.running else 'red'
            )

            # Mode
            mode_map = {1: 'Auto', 2: 'Cool', 3: 'Dry', 4: 'Heat', 5: 'Fan'}
            mode_reverse = {1: 'auto', 2: 'cool', 3: 'dry', 4: 'heat', 5: 'fan'}
            mode_text = mode_map.get(state.mode, f"Unknown ({state.mode})")
            self.status_labels['mode'].config(text=mode_text)

            # Update mode control to match current state
            if state.mode in mode_reverse:
                self.mode_var.set(mode_reverse[state.mode])

            # Temperatures
            target_temp = state.target_temperature
            indoor_temp = state.indoor_temperature

            if self.temp_unit.get() == "F":
                target_temp = int(target_temp * 9 / 5 + 32)
                indoor_temp = int(indoor_temp * 9 / 5 + 32)
                unit = "°F"
            else:
                unit = "°C"

            self.status_labels['target_temp'].config(text=f"{target_temp}{unit}")
            self.status_labels['indoor_temp'].config(text=f"{indoor_temp}{unit}")

            # Update temperature control to match current state (only if not being adjusted)
            if not self.temp_slider_active:
                self.temp_var.set(target_temp)
                self.temp_label.config(text=f"{target_temp}°{self.temp_unit.get()}")

            # Fan speed
            fan_map = {20: 'Low', 40: 'Med-Low', 60: 'Medium', 80: 'Med-High', 102: 'Auto'}
            fan_reverse = {20: 'Low', 40: 'Med-Low', 60: 'Medium', 80: 'Med-High', 102: 'Auto', 100: 'High'}
            fan_text = fan_map.get(state.fan_speed, f"{state.fan_speed}")
            self.status_labels['fan_speed'].config(text=fan_text)

            # Update fan control to match current state
            if state.fan_speed in fan_reverse:
                self.fan_var.set(fan_reverse[state.fan_speed])

            # Swing
            self.status_labels['vswing'].config(
                text="ON" if state.vertical_swing else "OFF"
            )
            self.status_labels['hswing'].config(
                text="ON" if state.horizontal_swing else "OFF"
            )

            # Update swing controls to match current state
            self.vswing_var.set(state.vertical_swing)
            self.hswing_var.set(state.horizontal_swing)

            # Last updated
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated_label.config(text=now)

            self.update_status_bar("Status updated")

        except Exception as e:
            self.update_status_bar(f"Error updating display: {str(e)}")

    def update_status_bar(self, message):
        """Update status bar message"""
        self.status_bar.config(text=message)

    def set_power(self, power_on):
        """Set power state"""
        self.update_status_bar(f"Turning {'ON' if power_on else 'OFF'}...")

        def power_thread():
            try:
                device = self.get_device()
                if device:
                    device.state.running = power_on
                    device.apply()
                    self.root.after(1000, self.refresh_status)
                    self.root.after(0, self.update_status_bar,
                                  f"Power {'ON' if power_on else 'OFF'}")
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error",
                              f"Failed to set power:\n{str(e)}")

        threading.Thread(target=power_thread, daemon=True).start()

    def set_mode(self):
        """Set operating mode"""
        mode = self.mode_var.get()
        mode_map = {'auto': 1, 'cool': 2, 'dry': 3, 'heat': 4, 'fan': 5}
        mode_num = mode_map.get(mode, 1)

        self.update_status_bar(f"Setting mode to {mode}...")

        def mode_thread():
            try:
                device = self.get_device()
                if device:
                    device.state.mode = mode_num
                    device.apply()
                    self.root.after(1000, self.refresh_status)
                    self.root.after(0, self.update_status_bar, f"Mode set to {mode}")
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error",
                              f"Failed to set mode:\n{str(e)}")

        threading.Thread(target=mode_thread, daemon=True).start()

    def set_temperature(self):
        """Set target temperature"""
        temp = self.temp_var.get()
        unit = self.temp_unit.get()

        # Convert to Celsius for device
        temp_c = temp if unit == "C" else int((temp - 32) * 5 / 9)

        self.update_status_bar(f"Setting temperature to {temp}°{unit}...")

        def temp_thread():
            try:
                device = self.get_device()
                if device:
                    device.state.target_temperature = temp_c
                    device.apply()
                    self.root.after(1000, self.refresh_status)
                    self.root.after(0, self.update_status_bar,
                                  f"Temperature set to {temp}°{unit}")
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error",
                              f"Failed to set temperature:\n{str(e)}")

        threading.Thread(target=temp_thread, daemon=True).start()

    def set_fan_speed(self):
        """Set fan speed"""
        fan = self.fan_var.get()
        fan_map = {
            'Auto': 102, 'Low': 20, 'Med-Low': 40,
            'Medium': 60, 'Med-High': 80, 'High': 100
        }
        fan_speed = fan_map.get(fan, 102)

        self.update_status_bar(f"Setting fan speed to {fan}...")

        def fan_thread():
            try:
                device = self.get_device()
                if device:
                    device.state.fan_speed = fan_speed
                    device.apply()
                    self.root.after(1000, self.refresh_status)
                    self.root.after(0, self.update_status_bar, f"Fan speed set to {fan}")
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error",
                              f"Failed to set fan speed:\n{str(e)}")

        threading.Thread(target=fan_thread, daemon=True).start()

    def set_vswing(self):
        """Set vertical swing"""
        enabled = self.vswing_var.get()

        def swing_thread():
            try:
                device = self.get_device()
                if device:
                    device.state.vertical_swing = enabled
                    device.apply()
                    self.root.after(1000, self.refresh_status)
                    self.root.after(0, self.update_status_bar,
                                  f"Vertical swing {'enabled' if enabled else 'disabled'}")
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error",
                              f"Failed to set vertical swing:\n{str(e)}")

        threading.Thread(target=swing_thread, daemon=True).start()

    def set_hswing(self):
        """Set horizontal swing"""
        enabled = self.hswing_var.get()

        def swing_thread():
            try:
                device = self.get_device()
                if device:
                    device.state.horizontal_swing = enabled
                    device.apply()
                    self.root.after(1000, self.refresh_status)
                    self.root.after(0, self.update_status_bar,
                                  f"Horizontal swing {'enabled' if enabled else 'disabled'}")
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error",
                              f"Failed to set horizontal swing:\n{str(e)}")

        threading.Thread(target=swing_thread, daemon=True).start()

    def start_auto_refresh(self):
        """Start auto-refresh thread"""
        def auto_refresh_loop():
            while self.running:
                if self.auto_refresh.get():
                    self.root.after(0, self.refresh_status)
                time.sleep(self.refresh_interval)

        self.refresh_thread = threading.Thread(target=auto_refresh_loop, daemon=True)
        self.refresh_thread.start()

    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        if self.auto_refresh.get():
            self.update_status_bar("Auto-refresh enabled")
        else:
            self.update_status_bar("Auto-refresh disabled")

    def on_closing(self):
        """Handle window close"""
        self.running = False
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = SenvilleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
