# Electricity Waste Monitor

A software-based **electricity consumption analysis web application** for an Internet Programming (college) project.

It helps users estimate appliance-level electricity consumption (kWh), estimate electricity cost, store historical records, detect possible high-usage patterns, visualize trends with Chart.js, and stay ready for future device integration.

**No physical sensors or IoT hardware are required** for the initial version.

## Quick start (Windows)

```bat
git clone https://github.com/akshaya-murarishetti/electricity-waste-monitor.git
cd electricity-waste-monitor
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**

## Linux / macOS

```bash
git clone https://github.com/akshaya-murarishetti/electricity-waste-monitor.git
cd electricity-waste-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Features

- Dashboard with estimated daily/monthly energy and cost
- Appliance management (add / edit / delete)
- Consumption calculator (Power × Qty × Hours ÷ 1000)
- Historical records + CSV export
- Analytics charts (Chart.js)
- Rule-based possible high-usage alerts
- Energy-saving recommendations
- Device integration API (starts as not connected)

## Example calculation

Fan 75 W × 1 × 12 h ÷ 1000 = **0.9 kWh/day**  
30 days → **27 kWh**  
At ₹8/kWh → **₹216**

## Technologies

HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js, Python, Flask, SQLite, pytest

## Project structure

```
electricity-waste-monitor/
├── app.py
├── database.py
├── calculations.py
├── detection.py
├── requirements.txt
├── README.md
├── templates/
├── static/
└── tests/
```

## Testing

```bat
pytest tests/ -v
```

## License

Educational / college project use.
