class MLQSimulator {
    constructor() {
        // Use relative URL for deployment
        this.baseUrl = window.location.origin;
        this.currentTime = 0;
        this.initEventListeners();
        this.loadProcesses();
        this.loadStatistics();
    }

    initEventListeners() {
        document.getElementById('processForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addProcess();
        });

        document.getElementById('startSimulation').addEventListener('click', () => {
            this.startSimulation();
        });

        document.getElementById('stepSimulation').addEventListener('click', () => {
            this.stepSimulation();
        });

        document.getElementById('saveResults').addEventListener('click', () => {
            this.saveSimulationResults();
        });

        document.getElementById('resetSimulation').addEventListener('click', () => {
            this.resetSimulation();
        });

        document.getElementById('loadHistory').addEventListener('click', () => {
            this.loadSimulationHistory();
        });
    }

    async addProcess() {
        const formData = {
            name: document.getElementById('processName').value,
            arrival_time: parseInt(document.getElementById('arrivalTime').value),
            burst_time: parseInt(document.getElementById('burstTime').value),
            priority: parseInt(document.getElementById('priority').value),
            queue_type: document.getElementById('queueType').value
        };

        try {
            const response = await fetch(`${this.baseUrl}/api/processes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showMessage('Process added successfully!', 'success');
                this.loadProcesses();
                document.getElementById('processForm').reset();
            } else {
                const error = await response.json();
                this.showMessage(error.error || 'Error adding process', 'error');
            }
        } catch (error) {
            this.showMessage('Error connecting to server', 'error');
        }
    }

    async startSimulation() {
        try {
            const response = await fetch(`${this.baseUrl}/api/simulation/start`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showMessage('Simulation started!', 'success');
                this.loadProcesses();
            } else {
                const error = await response.json();
                this.showMessage(error.error || 'Error starting simulation', 'error');
            }
        } catch (error) {
            this.showMessage('Error starting simulation', 'error');
        }
    }

    async stepSimulation() {
        try {
            const response = await fetch(`${this.baseUrl}/api/simulation/step`, {
                method: 'POST'
            });

            const result = await response.json();

            if (response.ok) {
                if (result.process) {
                    this.addLogEntry(
                        `Time ${this.currentTime}: Executed ${result.process.name} ` +
                        `from ${result.queue_type} queue for ${result.process.execution_time} units`
                    );
                    this.currentTime += result.process.execution_time;
                } else {
                    this.addLogEntry(`Time ${this.currentTime}: No processes to execute`);
                }
                
                this.updateStatistics(result.statistics);
                this.loadProcesses();
            } else {
                this.showMessage(result.error || 'Error executing step', 'error');
            }
        } catch (error) {
            this.showMessage('Error executing simulation step', 'error');
        }
    }

    async saveSimulationResults() {
        try {
            const response = await fetch(`${this.baseUrl}/api/simulation/save`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showMessage(result.message, 'success');
                console.log('Saved results:', result.results);
            } else {
                this.showMessage(result.error, 'error');
            }
        } catch (error) {
            this.showMessage('Error saving simulation results', 'error');
        }
    }

    async resetSimulation() {
        try {
            const response = await fetch(`${this.baseUrl}/api/simulation/reset`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showMessage('Simulation reset!', 'success');
                this.currentTime = 0;
                document.getElementById('logContent').innerHTML = '';
                this.loadProcesses();
                this.loadStatistics();
            } else {
                const error = await response.json();
                this.showMessage(error.error || 'Error resetting simulation', 'error');
            }
        } catch (error) {
            this.showMessage('Error resetting simulation', 'error');
        }
    }

    async loadSimulationHistory() {
        try {
            const response = await fetch(`${this.baseUrl}/api/simulation/history`);
            const history = await response.json();
            
            if (response.ok) {
                this.displayHistory(history);
            } else {
                this.showMessage(history.error || 'Error loading history', 'error');
            }
        } catch (error) {
            console.error('Error loading history:', error);
            this.showMessage('Error loading simulation history', 'error');
        }
    }

    displayHistory(history) {
        const historyContent = document.getElementById('historyContent');
        
        if (history.length === 0) {
            historyContent.innerHTML = '<p>No simulation history found.</p>';
            return;
        }
        
        historyContent.innerHTML = history.map(result => `
            <div class="history-item">
                <strong>Simulation at ${result.timestamp}</strong><br>
                <strong>Processes:</strong> ${result.completed_processes}/${result.total_processes} completed<br>
                <strong>Average Waiting Time:</strong> ${result.avg_waiting_time} units<br>
                <strong>Average Turnaround Time:</strong> ${result.avg_turnaround_time} units<br>
                <strong>Starvation Cases:</strong> ${result.starvation_count}
            </div>
        `).join('');
    }

    async loadProcesses() {
        try {
            const response = await fetch(`${this.baseUrl}/api/processes`);
            const processes = await response.json();

            if (response.ok) {
                this.updateProcessTable(processes);
                this.updateQueueDisplays(processes);
            }
        } catch (error) {
            console.error('Error loading processes:', error);
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch(`${this.baseUrl}/api/simulation/statistics`);
            const stats = await response.json();
            
            if (response.ok) {
                this.updateStatistics(stats);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    updateProcessTable(processes) {
        const tbody = document.getElementById('processTableBody');
        tbody.innerHTML = '';

        processes.forEach(process => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td>${process.pid}</td>
                <td>${process.name}</td>
                <td>${process.arrival_time}</td>
                <td>${process.burst_time}</td>
                <td>${process.priority}</td>
                <td>${process.queue_type}</td>
                <td>${process.completed ? 'Completed' : 'Pending'}</td>
            `;

            if (process.waiting_time > 10) {
                row.classList.add('starvation-warning');
            }

            tbody.appendChild(row);
        });
    }

    updateQueueDisplays(processes) {
        const foregroundContent = document.getElementById('foregroundContent');
        const backgroundContent = document.getElementById('backgroundContent');

        foregroundContent.innerHTML = '';
        backgroundContent.innerHTML = '';

        const pendingProcesses = processes.filter(p => !p.completed);

        pendingProcesses.forEach(process => {
            const processElement = document.createElement('div');
            processElement.className = `process-item ${process.queue_type}`;
            
            processElement.innerHTML = `
                <strong>${process.name}</strong> (PID: ${process.pid})<br>
                Remaining: ${process.remaining_time}<br>
                Waiting: ${process.waiting_time}
                ${process.waiting_time > 10 ? '<br>⚠️ Starvation Risk' : ''}
            `;

            if (process.queue_type === 'foreground') {
                foregroundContent.appendChild(processElement);
            } else {
                backgroundContent.appendChild(processElement);
            }
        });

        if (foregroundContent.children.length === 0) {
            foregroundContent.innerHTML = '<em>No processes in foreground queue</em>';
        }

        if (backgroundContent.children.length === 0) {
            backgroundContent.innerHTML = '<em>No processes in background queue</em>';
        }
    }

    updateStatistics(stats) {
        const statsContent = document.getElementById('statsContent');
        
        statsContent.innerHTML = `
            <div class="stats-item">
                <span>Current Time:</span>
                <span>${stats.current_time || 0}</span>
            </div>
            <div class="stats-item">
                <span>Total Processes:</span>
                <span>${stats.total_processes || 0}</span>
            </div>
            <div class="stats-item">
                <span>Completed Processes:</span>
                <span>${stats.completed_processes || 0}</span>
            </div>
            <div class="stats-item">
                <span>Foreground Queue Size:</span>
                <span>${stats.foreground_queue_size || 0}</span>
            </div>
            <div class="stats-item">
                <span>Background Queue Size:</span>
                <span>${stats.background_queue_size || 0}</span>
            </div>
            <div class="stats-item">
                <span>Average Waiting Time:</span>
                <span>${stats.avg_waiting_time || 0}</span>
            </div>
            <div class="stats-item">
                <span>Average Turnaround Time:</span>
                <span>${stats.avg_turnaround_time || 0}</span>
            </div>
            <div class="stats-item">
                <span>Starvation Count:</span>
                <span>${stats.starvation_count || 0}</span>
            </div>
        `;
    }

    addLogEntry(message) {
        const logContent = document.getElementById('logContent');
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    showMessage(message, type) {
        // Simple message display
        const color = type === 'success' ? '#28a745' : '#dc3545';
        alert(`${type.toUpperCase()}: ${message}`);
    }
}

// Initialize the simulator when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MLQSimulator();
});