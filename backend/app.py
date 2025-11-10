from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import time
import threading
from backend.database import Database
from backend.scheduler import MLQScheduler

app = Flask(__name__)
CORS(app)

# Initialize database and scheduler
db = Database()
scheduler = MLQScheduler(db)

@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/api/processes', methods=['POST'])
def add_process():
    data = request.json
    required_fields = ['name', 'arrival_time', 'burst_time', 'priority', 'queue_type']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Generate PID
    processes = db.get_all_processes()
    next_pid = max([p[1] for p in processes]) + 1 if processes else 1
    
    process = {
        'pid': next_pid,
        'name': data['name'],
        'arrival_time': data['arrival_time'],
        'burst_time': data['burst_time'],
        'priority': data['priority'],
        'queue_type': data['queue_type']
    }
    
    success = db.add_process(process)
    if success:
        return jsonify({'message': 'Process added successfully', 'pid': next_pid})
    else:
        return jsonify({'error': 'Failed to add process'}), 500

@app.route('/api/processes', methods=['GET'])
def get_processes():
    processes = db.get_all_processes()
    process_list = []
    
    for p in processes:
        process_list.append({
            'id': p[0],
            'pid': p[1],
            'name': p[2],
            'arrival_time': p[3],
            'burst_time': p[4],
            'priority': p[5],
            'queue_type': p[6],
            'remaining_time': p[7],
            'waiting_time': p[8],
            'turnaround_time': p[9],
            'completed': bool(p[10])
        })
    
    return jsonify(process_list)

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    scheduler.load_processes_from_db()
    return jsonify({'message': 'Simulation started'})

@app.route('/api/simulation/step', methods=['POST'])
def simulation_step():
    process, execution_time, queue_type = scheduler.simulate_step()
    
    if process:
        result = {
            'process': {
                'pid': process['pid'],
                'name': process['name'],
                'execution_time': execution_time,
                'remaining_time': process.get('remaining_time', 0)
            },
            'queue_type': queue_type,
            'statistics': scheduler.get_statistics()
        }
        return jsonify(result)
    else:
        return jsonify({
            'message': 'No processes to execute',
            'statistics': scheduler.get_statistics()
        })

@app.route('/api/simulation/statistics', methods=['GET'])
def get_statistics():
    return jsonify(scheduler.get_statistics())

@app.route('/api/simulation/reset', methods=['POST'])
def reset_simulation():
    success = db.clear_processes()
    scheduler.reset()
    if success:
        return jsonify({'message': 'Simulation reset'})
    else:
        return jsonify({'error': 'Failed to reset simulation'}), 500

@app.route('/api/simulation/save', methods=['POST'])
def save_simulation_results():
    try:
        statistics = scheduler.get_statistics()
        
        # Only save if we have processes
        if statistics['total_processes'] > 0:
            success = db.save_simulation_result(statistics)
            if success:
                return jsonify({
                    'message': 'Simulation results saved successfully!',
                    'results': statistics
                })
            else:
                return jsonify({'error': 'Failed to save results to database'}), 500
        else:
            return jsonify({'error': 'No processes to save'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Error saving results: {str(e)}'}), 500

@app.route('/api/simulation/history', methods=['GET'])
def get_simulation_history():
    try:
        results = db.get_simulation_history()
        
        history = []
        for result in results:
            history.append({
                'id': result[0],
                'timestamp': result[1].strftime('%Y-%m-%d %H:%M:%S'),
                'total_processes': result[2],
                'completed_processes': result[3],
                'avg_waiting_time': float(result[4]) if result[4] else 0,
                'avg_turnaround_time': float(result[5]) if result[5] else 0,
                'starvation_count': result[6]
            })
        
        return jsonify(history)
        
    except Exception as e:
        return jsonify({'error': f'Error loading history: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)