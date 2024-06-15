import sys
import asyncio
from bleak import BleakScanner, BleakClient
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class HeartRateMonitor(QtCore.QObject):
    heartRateUpdated = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.client = None
        self.connected = False
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.read_heart_rate)
        self.find_device()
        self.timer.start(1000)  # Read heart rate every 1 second

    async def find_device(self):
        devices = await BleakScanner.discover()
        for device in devices:
            if "Polar H10" in device.name:
                await self.connect(device)
                return
        print("Polar H10 device not found")

    async def connect(self, device):
        try:
            self.client = BleakClient(device.address)
            await self.client.connect()
            self.connected = True
            print(f"Connected to Polar H10 at {device.address}")
            await self.start_notifications()
        except Exception as err:
            print(f"Error connecting: {err}")

    async def start_notifications(self):
        heart_rate_uuid = "0x180D"
        heart_rate_char_uuid = "0x2A37"
        await self.client.start_notify(heart_rate_char_uuid, self.handle_notification)

    def handle_notification(self, sender, data):
        heart_rate = int.from_bytes(data, byteorder="little")
        self.heartRateUpdated.emit(heart_rate)

    def read_heart_rate(self):
        if self.connected:
            try:
                asyncio.run(self.client.get_services())
            except Exception as err:
                print(f"Error reading heart rate: {err}")
                self.connected = False
                asyncio.run(self.find_device())

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Heart Rate Monitor")
        self.heart_rate_monitor = HeartRateMonitor()
        self.heart_rate_monitor.heartRateUpdated.connect(self.update_chart)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.chart = pg.PlotWidget()
        self.heart_rate_data = []
        self.chart_curve = self.chart.plot(pen='r')

        layout.addWidget(self.chart)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_chart(self, heart_rate):
        self.heart_rate_data.append(heart_rate)
        self.chart_curve.setData(self.heart_rate_data)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())