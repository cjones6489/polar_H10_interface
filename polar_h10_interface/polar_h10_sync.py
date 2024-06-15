import threading
import time
from bleak import BleakScanner, BleakClient
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class HeartRateMonitor:
    def __init__(self):
        self.device = None
        self.heart_rates = []
        self.lock = threading.Lock()

    def scan_and_connect(self):
        print("Scanning for devices...")
        devices = BleakScanner.discover(timeout=5.0)  # Timeout to avoid blocking too long
        for device in devices:
            if device.name and "Polar H10" in device.name:
                self.device = device
                break

        if not self.device:
            print("Polar H10 not found.")
            return False

        print(f"Found Polar H10: {self.device.address}")
        with BleakClient(self.device) as client:
            print(f"Connected to {self.device.name}")
            self.start_notify(client)
            time.sleep(60)  # Collect data for 60 seconds
            client.stop_notify("00002a37-0000-1000-8000-00805f9b34fb")
        return True

    def start_notify(self, client):
        def callback(sender, data):
            heart_rate = data[1]
            with self.lock:
                self.heart_rates.append(heart_rate)
            print(f"Heart Rate: {heart_rate}")

        client.start_notify("00002a37-0000-1000-8000-00805f9b34fb", callback)

    def get_heart_rates(self):
        with self.lock:
            return self.heart_rates.copy()

def visualize_data(hr_monitor):
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.set_title("Real-Time Heart Rate Data", color='white', fontsize=20, fontweight='bold')
    ax.set_xlabel("Time (s)", color='lime', fontsize=15, fontweight='bold')
    ax.set_ylabel("Heart Rate (BPM)", color='lime', fontsize=15, fontweight='bold')
    ax.tick_params(axis='x', colors='lime', labelsize=12, width=2)
    ax.tick_params(axis='y', colors='lime', labelsize=12, width=2)
    ax.spines['bottom'].set_color('lime')
    ax.spines['top'].set_color('lime')
    ax.spines['right'].set_color('lime')
    ax.spines['left'].set_color('lime')
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['top'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.set_xlim(0, 60)  # Initial x-axis limit
    ax.set_ylim(40, 180)  # Initial y-axis limit (adjust as needed)

    line, = ax.plot([], [], lw=2, color='red')

    def init():
        line.set_data([], [])
        return line,

    def update(frame):
        heart_rates = hr_monitor.get_heart_rates()
        xdata = list(range(len(heart_rates)))
        ydata = heart_rates
        line.set_data(xdata, ydata)
        ax.set_xlim(0, max(60, len(heart_rates)))  # Update x-axis limit dynamically
        if ydata:
            ax.set_ylim(min(40, min(ydata) - 10), max(180, max(ydata) + 10))  # Update y-axis limit dynamically
        return line,

    ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=1000)
    plt.show()

def run_ble_operations(hr_monitor):
    hr_monitor.scan_and_connect()

def main():
    hr_monitor = HeartRateMonitor()

    # Run BLE operations in a separate thread
    ble_thread = threading.Thread(target=run_ble_operations, args=(hr_monitor,))
    ble_thread.start()

    # Start the visualization
    visualize_data(hr_monitor)

    # Wait for the BLE thread to finish
    ble_thread.join()

if __name__ == "__main__":
    main()
