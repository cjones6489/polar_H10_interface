import asyncio
from concurrent.futures import ThreadPoolExecutor
from bleak import BleakScanner, BleakClient
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from threading import Lock

class HeartRateMonitor:
    def __init__(self):
        self.device = None
        self.heart_rates = []
        self.lock = Lock()

    async def scan_and_connect(self):
        print("Scanning for devices...")
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name and "Polar H10" in device.name:
                self.device = device
                break

        if not self.device:
            print("Polar H10 not found.")
            return False

        print(f"Found Polar H10: {self.device.address}")
        async with BleakClient(self.device) as client:
            print(f"Connected to {self.device.name}")
            await self.start_notify(client)
            await asyncio.sleep(60)  # Collect data for 60 seconds
            await client.stop_notify("00002a37-0000-1000-8000-00805f9b34fb")
        return True

    async def start_notify(self, client):
        def callback(sender, data):
            heart_rate = data[1]
            with self.lock:
                self.heart_rates.append(heart_rate)
            print(f"Heart Rate: {heart_rate}")

        await client.start_notify("00002a37-0000-1000-8000-00805f9b34fb", callback)

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

async def run_ble(hr_monitor):
    await hr_monitor.scan_and_connect()

def main():
    hr_monitor = HeartRateMonitor()

    # Create a new event loop for the BLE operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Use ThreadPoolExecutor to run BLE operations in the correct thread
    with ThreadPoolExecutor() as executor:
        ble_future = executor.submit(loop.run_until_complete, run_ble(hr_monitor))

        # Start the visualization in the main thread
        visualize_data(hr_monitor)

        # Wait for BLE operations to complete
        ble_future.result()

if __name__ == "__main__":
    main()
