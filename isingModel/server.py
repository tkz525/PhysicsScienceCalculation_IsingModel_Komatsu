import http.server
import socketserver
import json
import os
import sys
import subprocess
import traceback
import numpy as np

# Import simulation logic
from ising_simulation import IsingModel, run_scaling_benchmark

PORT = 8000

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class IsingAPIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence standard HTTP logging to keep console clean unless needed
        pass

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status)

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # Parse URL
        path = self.path
        if path == "/" or path == "":
            path = "/index.html"

        # Remove query parameters if any
        path = path.split("?")[0]

        # Robust cross-platform path cleaning: convert backslashes and strip leading slashes
        clean_path = path.replace("\\", "/").lstrip("/")
        
        # Security check: prevent directory traversal
        if ".." in clean_path or clean_path.startswith("/"):
            self.send_error(403, "Access Denied")
            return

        # Determine file path relative to the server script location
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, clean_path)

        if os.path.exists(file_path) and not os.path.isdir(file_path):
            # Determine content type
            ext = os.path.splitext(file_path)[1].lower()
            content_type = 'text/plain'
            if ext == '.html':
                content_type = 'text/html; charset=utf-8'
            elif ext == '.css':
                content_type = 'text/css; charset=utf-8'
            elif ext == '.js':
                content_type = 'application/javascript; charset=utf-8'
            elif ext == '.json':
                content_type = 'application/json; charset=utf-8'
            elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
                content_type = f'image/{ext[1:]}'
            elif ext == '.svg':
                content_type = 'image/svg+xml; charset=utf-8'

            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f"Internal Server Error: {str(e)}")
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        # Handle POST endpoints
        path = self.path

        # Read JSON body
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body) if body else {}
            else:
                data = {}
        except Exception as e:
            self.send_error_json(f"Invalid JSON body: {str(e)}")
            return

        try:
            if path == "/api/simulate":
                self.handle_simulate(data)
            elif path == "/api/benchmark":
                self.handle_benchmark(data)
            elif path == "/api/run-tests":
                self.handle_run_tests()
            elif path == "/api/live-step":
                self.handle_live_step(data)
            else:
                self.send_error_json("API Endpoint Not Found", 404)
        except Exception as e:
            traceback.print_exc()
            self.send_error_json(f"Server Error during execution: {str(e)}", 500)

    def handle_simulate(self, data):
        # Extract inputs with robust fallbacks
        L_values = data.get("L_values", [8, 12, 16])
        T_start = float(data.get("T_start", 1.5))
        T_end = float(data.get("T_end", 3.0))
        T_step = float(data.get("T_step", 0.1))
        mcs_steps = int(data.get("mcs_steps", 1000))
        equilibration_steps = int(data.get("equilibration_steps", 500))

        # Generate temperature grid
        temperatures = list(np.arange(T_start, T_end + T_step/2.0, T_step))
        # Ensure values are float and not np.float64 (which is not JSON serializable easily)
        temperatures = [float(t) for t in temperatures]

        results = {}

        for L in L_values:
            L = int(L)
            model = IsingModel(L)
            
            e_list, m_list, cv_list, chi_list, u4_list = [], [], [], [], []
            
            for T in temperatures:
                # Use cold start at lowest T, warm start after (thermalization continuity)
                if T == temperatures[0]:
                    model.reset('up') # standard is starting fully ordered at low temp
                
                obs = model.run_simulation(T, mcs_steps, equilibration_steps)
                
                e_list.append(obs["energy"])
                m_list.append(obs["magnetization"])
                cv_list.append(obs["specific_heat"])
                chi_list.append(obs["susceptibility"])
                u4_list.append(obs["binder_cumulant"])

            results[str(L)] = {
                "temperatures": temperatures,
                "energies": e_list,
                "magnetizations": m_list,
                "specific_heats": cv_list,
                "susceptibilities": chi_list,
                "binder_cumulants": u4_list
            }

        self.send_json(results)

    def handle_benchmark(self, data):
        L_values = data.get("L_values", [8, 16, 32, 64, 128])
        mcs_steps = int(data.get("mcs_steps", 100))
        
        # Ensure L values are integer
        L_values = [int(L) for L in L_values]
        
        res = run_scaling_benchmark(L_values, mcs_steps)
        self.send_json(res)

    def handle_run_tests(self):
        # Run test_ising.py using the current python executable
        python_exe = sys.executable
        try:
            result = subprocess.run(
                [python_exe, "-m", "unittest", "test_ising.py"],
                capture_output=True,
                text=True,
                timeout=15
            )
            self.send_json({
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "stdout": "",
                "stderr": f"Error running tests: {str(e)}"
            })

    def handle_live_step(self, data):
        # Stateless live update
        L = int(data.get("L", 32))
        temperature = float(data.get("temperature", 2.269))
        spins_list = data.get("spins", None)
        steps = int(data.get("steps", 5)) # do 5 steps for smooth display

        model = IsingModel(L)
        if spins_list is not None:
            model.spins = np.array(spins_list, dtype=np.int8)
        else:
            model.reset('random')

        # Run some steps
        for _ in range(steps):
            model.step_mcs(temperature)

        # Get current observables
        E = model.compute_energy()
        M = model.compute_magnetization()

        self.send_json({
            "spins": model.spins.tolist(),
            "energy_density": float(E / model.N),
            "magnetization_density": float(abs(M) / model.N)
        })

def start_server():
    handler = IsingAPIHandler
    with ThreadingTCPServer(("", PORT), handler) as httpd:
        print(f"Ising Simulation Server started on port {PORT}")
        print(f"Open browser at: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
