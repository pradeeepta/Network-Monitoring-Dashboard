
import os
import time
import json
import platform
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from pymongo import MongoClient
import collections

# Initialize MongoDB client
client = MongoClient('mongodb://localhost:27017/')
# Access or create a database named 'network_monitoring'
db = client['network_monitoring']
# Access or create a collection named 'status_history'
collection = db['status_history']


# List of addresses to monitor
addresses = {
    'Localhost': '127.0.0.1',
    'Google': 'google.com',
    'Cloudflare': 'cloudflare.com',
    'GitHub': 'github.com',
    'LinkedIn': 'linkedin.com',
    'Wikipedia': 'wikipedia.org',
    'Stack Overflow': 'stackoverflow.com',
    'Amazon': 'amazon.com',
    'Facebook': 'facebook.com',
    'Twitter': 'twitter.com',
    'Microsoft': 'microsoft.com',
    'Apple': 'apple.com',
    'Netflix': 'netflix.com',
    'Instagram': 'instagram.com',
    'YouTube': 'youtube.com'
}

# Determine the OS to use the appropriate ping command
is_windows = platform.system().lower() == 'windows'

def ping_address(address):
    if is_windows:
        # For Windows
        command = f"ping -n 1 -w 2000 {address} > nul"
    else:
        # For Unix-like systems (Linux, macOS)
        command = f"ping -c 1 -W 2 {address} > /dev/null 2>&1"
    return os.system(command) == 0

# Function to check the status of each address
def check_status():
    status = {}
    for name, address in addresses.items():
        start_time = time.time()
        Status = ping_address(address)
        end_time = time.time()
        elapsed_time = (end_time - start_time) * 1000  # Convert to milliseconds
        status[name] = {
            'Status': Status,
            'Response_time': elapsed_time if Status else None,
            'Last_checked': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
    return status

# Store historical data
history = collections.defaultdict(list)

def update_history(status):
    for name, data in status.items():
        history[name].append(data)
        # Keep history limited to the last 100 records
        if len(history[name]) > 100:
            history[name].pop(0)
        # Insert data into MongoDB collection
        collection.insert_one({name: data})


# Simple HTML template for the dashboard
html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Network Monitoring Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
            scroll-behavior: smooth; /* Smooth scrolling */
        }
        .container {
            width: 80%;
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            text-align: center;
            height: 80vh;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        h1 {
            color: #fff;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        .status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            margin: 10px 0;
            border-radius: 5px;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            font-weight: bold;
        }
        .color-indicator {
            width: 10px;
            border-radius: 5px 0 0 5px;
        }
        .Good {
            background-color: rgba(40, 167, 69, 0.2);
        }
        .color-indicator.Good {
            background-color: #28a745;
        }
        .Low {
            background-color: rgba(255, 193, 7, 0.2);
        }
        .color-indicator.Low {
            background-color: #ffc107;
        }
        .Down {
            background-color: rgba(220, 53, 69, 0.2);
        }
        .color-indicator.Down {
            background-color: #dc3545;
        }
        .status-info {
            display: flex;
            flex-direction: column;
            text-align: left;
            margin-left: 10px;
            flex-grow: 1;
        }
        .status-name {
            font-size: 1.2em;
            display: flex;
            align-items: center;
        }
        .status-name img {
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 50%;
        }
        .status-time, .status-last-checked {
            font-size: 0.9em;
            color: #ddd;
        }
        .timestamp {
            text-align: center;
            margin-top: 20px;
            color: #ddd;
        }
        #spinner {
            display: none;
            margin: 20px auto;
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        #refresh-rate {
            margin: 20px 0;
            font-size: 1.2em;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        select {
            background-color: rgba(255, 255, 255, 0.2);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 1em;
            outline: none;
            appearance: none;
            cursor: pointer;
            transition: background-color 0.3s ease, border-color 0.3s ease;
            margin-top: 10px;
        }
        select:hover {
            background-color: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.6);
        }
        select option {
            background-color: #764ba2;
            color: #fff;
        }
        #view-data-button {
            margin-top: 20px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: #fff;
            border: none;
            border-radius: 50px;
            padding: 15px 30px;
            cursor: pointer;
            text-decoration: none;
            font-size: 1.2em;
            transition: background 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        #view-data-button:hover {
            background: linear-gradient(135deg, #2980b9 0%, #2577b5 100%);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Network Monitoring Dashboard</h1>
        <div id="status-container"></div>
        <div id="spinner"></div>
        <div class="timestamp" id="timestamp"></div>
        <div id="refresh-rate">
            Refresh rate:
            <select id="rate" onchange="updateRefreshRate()">
                <option value="2000">2 seconds</option>
                <option value="5000" selected>5 seconds</option>
                <option value="10000">10 seconds</option>
                <option value="30000">30 seconds</option>
                <option value="60000">1 minute</option>
            </select>
        </div>
        <a id="view-data-button" href="/view-data" target="_blank">View Database</a>
    </div>
    <script>
        const logos = {
            'Localhost': 'https://via.placeholder.com/20',
            'Google': 'https://www.google.com/favicon.ico',
            'Cloudflare': 'https://www.cloudflare.com/favicon.ico',
            'GitHub': 'https://github.githubassets.com/favicons/favicon.png',
            'LinkedIn': 'https://www.linkedin.com/favicon.ico',
            'Wikipedia': 'https://www.wikipedia.org/static/favicon/wikipedia.ico',
            'Stack Overflow': 'https://stackoverflow.com/favicon.ico',
            'Amazon': 'https://www.amazon.com/favicon.ico',
            'Facebook': 'https://www.facebook.com/favicon.ico',
            'Twitter': 'https://twitter.com/favicon.ico',
            'Microsoft': 'https://www.microsoft.com/favicon.ico',
            'Apple': 'https://www.apple.com/favicon.ico',
            'Netflix': 'https://www.netflix.com/favicon.ico',
            'Instagram': 'https://static.vecteezy.com/system/resources/previews/018/930/413/original/instagram-logo-instagram-icon-transparent-free-png.png',
            'YouTube': 'https://www.youtube.com/favicon.ico'
        };

        let refreshRate = 5000;

        function fetchStatus() {
            const spinner = document.getElementById('spinner');
            spinner.style.display = 'block';

            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('status-container');
                    const timestamp = document.getElementById('timestamp');
                    container.innerHTML = '';
                    for (const [name, details] of Object.entries(data)) {
                        const div = document.createElement('div');
                        div.className = `status ${details.Status ? (details.Response_time < 100 ? 'Good' : 'Low') : 'Down'}`;

                        const colorIndicator = document.createElement('div');
                        colorIndicator.className = `color-indicator ${details.Status ? (details.Response_time < 100 ? 'Good' : 'Low') : 'Down'}`;
                        div.appendChild(colorIndicator);

                        const statusInfoDiv = document.createElement('div');
                        statusInfoDiv.className = 'status-info';

                        const nameDiv = document.createElement('div');
                        nameDiv.className = 'status-name';
                        
                        const img = document.createElement('img');
                        img.src = logos[name] || 'https://via.placeholder.com/20';
                        nameDiv.appendChild(img);
                        
                        const textNode = document.createTextNode(name);
                        nameDiv.appendChild(textNode);

                        const timeDiv = document.createElement('div');
                        timeDiv.className = 'status-time';
                        timeDiv.textContent = `Status: ${details.Status ? (details.Response_time < 100 ? 'Good' : 'Low') : 'Down'} ${details.Response_time !== null ? `(${details.Response_time.toFixed(2)} ms)` : ''}`;

                        const lastCheckedDiv = document.createElement('div');
                        lastCheckedDiv.className = 'status-last-checked';
                        lastCheckedDiv.textContent = `Last Checked: ${details.Last_checked}`;

                        statusInfoDiv.appendChild(nameDiv);
                        statusInfoDiv.appendChild(timeDiv);
                        statusInfoDiv.appendChild(lastCheckedDiv);

                        div.appendChild(statusInfoDiv);

                        container.appendChild(div);
                    }
                    const now = new Date();
                    timestamp.textContent = `Last updated: ${now.toLocaleTimeString()}`;
                    spinner.style.display = 'none';

                    // Show the refresh rate selector after the first fetch
                    document.getElementById('refresh-rate').style.display = 'block';
                });
        }

        function updateRefreshRate() {
            const rate = document.getElementById('rate').value;
            refreshRate = parseInt(rate);
            clearInterval(fetchInterval);
            fetchInterval = setInterval(fetchStatus, refreshRate);
        }

        let fetchInterval = setInterval(fetchStatus, refreshRate);
        fetchStatus();  // Initial fetch
    </script>
</body>
</html>




'''

# HTML template for the database data webpage
data_html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Database</title>
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 0;
        background: #f0f0f0;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }
    .container {
        width: 80%;
        padding: 20px;
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        text-align: center;
    }
    h1 {
        color: #333;
        font-size: 2.5em;
        margin-bottom: 20px;
    }
    .record {
        padding: 10px 20px;
        margin: 10px 0;
        border-radius: 5px;
        background-color: #f9f9f9;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: left;
    }
    .record p {
        margin: 5px 0;
    }
    .timestamp {
        margin-top: 20px;
        color: #555;
    }
</style>
</head>
<body>
    <div class="container">
        <h1>Database</h1>
        <div id="data-container"></div>
        <div class="timestamp" id="timestamp"></div>
    </div>
    <script>
        function fetchData() {
            fetch('/get-data')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('data-container');
                    container.innerHTML = '';
                    data.forEach(record => {
                        const div = document.createElement('div');
                        div.className = 'record';
                        const content = Object.entries(record).map(([key, value]) => `<p><strong>${key}:</strong> ${JSON.stringify(value)}</p>`).join('');
                        div.innerHTML = content;
                        container.appendChild(div);
                    });
                    const now = new Date();
                    document.getElementById('timestamp').textContent = `Last updated: ${now.toLocaleTimeString()}`;
                });
        }

        fetchData();  // Initial fetch
    </script>
</body>
</html>

'''

# HTTP server handler
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html_template.encode('utf-8'))
        elif self.path == '/status':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            status = check_status()
            update_history(status)
            self.wfile.write(json.dumps(status).encode('utf-8'))
        elif self.path == '/view-data':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(data_html_template.encode('utf-8'))
        elif self.path == '/get-data':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = list(collection.find())
            for record in data:
                record.pop('_id', None)  # Remove the MongoDB ObjectId for cleaner display
            self.wfile.write(json.dumps(data).encode('utf-8'))

# Function to run the server
def run_server():
    server_address = ('127.0.0.1', 8050)
    httpd = HTTPServer(server_address, RequestHandler)
    print('Starting server at http://127.0.0.1:8050')
    httpd.serve_forever()

# Start the server in a separate thread
server_thread = Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# Keep the main thread alive
while True:
    time.sleep(1)
