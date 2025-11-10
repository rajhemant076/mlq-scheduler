import time
from collections import deque
import threading

class MLQScheduler:
    def __init__(self, database, time_quantum=4, aging_threshold=10):
        self.db = database
        self.time_quantum = time_quantum
        self.aging_threshold = aging_threshold
        self.current_time = 0
        self.running = False
        self.simulation_speed = 1
        self.foreground_queue = deque()
        self.background_queue = deque()
        self.completed_processes = []
        
    def add_process(self, process):
        if process['queue_type'] == 'foreground':
            self.foreground_queue.append(process)
        else:
            self.background_queue.append(process)
    
    def load_processes_from_db(self):
        processes = self.db.get_pending_processes()
        self.foreground_queue.clear()
        self.background_queue.clear()
        self.completed_processes.clear()
        self.current_time = 0
        
        for process in processes:
            process_dict = {
                'id': process[0],
                'pid': process[1],
                'name': process[2],
                'arrival_time': process[3],
                'burst_time': process[4],
                'priority': process[5],
                'queue_type': process[6],
                'remaining_time': process[7],
                'waiting_time': process[8],
                'age': 0
            }
            self.add_process(process_dict)
    
    def apply_aging(self):
        processes_to_promote = []
        for process in list(self.background_queue):
            if process['waiting_time'] > self.aging_threshold:
                process['age'] += 1
                if process['age'] >= 2:
                    process['queue_type'] = 'foreground'
                    processes_to_promote.append(process)
        
        for process in processes_to_promote:
            self.background_queue.remove(process)
            self.foreground_queue.append(process)
    
    def run_foreground_rr(self):
        if self.foreground_queue:
            process = self.foreground_queue.popleft()
            execution_time = min(self.time_quantum, process['remaining_time'])
            process['remaining_time'] -= execution_time
            
            for p in self.foreground_queue:
                p['waiting_time'] += execution_time
            for p in self.background_queue:
                p['waiting_time'] += execution_time
            
            if process['remaining_time'] > 0:
                self.foreground_queue.append(process)
            else:
                process['turnaround_time'] = self.current_time + execution_time - process['arrival_time']
                self.completed_processes.append(process)
                self.db.update_process(process['pid'], {
                    'completed': True,
                    'turnaround_time': process['turnaround_time'],
                    'waiting_time': process['waiting_time'],
                    'remaining_time': 0
                })
            
            self.current_time += execution_time
            return process, execution_time
        return None, 0
    
    def run_background_fcfs(self):
        if self.background_queue:
            process = self.background_queue.popleft()
            execution_time = process['remaining_time']
            process['remaining_time'] = 0
            
            for p in self.foreground_queue:
                p['waiting_time'] += execution_time
            for p in self.background_queue:
                p['waiting_time'] += execution_time
            
            process['turnaround_time'] = self.current_time + execution_time - process['arrival_time']
            self.completed_processes.append(process)
            self.db.update_process(process['pid'], {
                'completed': True,
                'turnaround_time': process['turnaround_time'],
                'waiting_time': process['waiting_time'],
                'remaining_time': 0
            })
            
            self.current_time += execution_time
            return process, execution_time
        return None, 0
    
    def simulate_step(self):
        self.apply_aging()
        process, execution_time = self.run_foreground_rr()
        if process:
            self.check_and_save_completion()
            return process, execution_time, 'foreground'
        
        process, execution_time = self.run_background_fcfs()
        if process:
            self.check_and_save_completion()
            return process, execution_time, 'background'
        
        return None, 0, 'idle'

    def check_and_save_completion(self):
        stats = self.get_statistics()
        if stats['completed_processes'] > 0 and stats['completed_processes'] == stats['total_processes']:
            self.db.save_simulation_result(stats)
            print("Simulation completed! Results saved automatically.")
    
    def get_starvation_count(self):
        count = 0
        for process in self.background_queue:
            if process['waiting_time'] > self.aging_threshold * 2:
                count += 1
        return count
    
    def get_statistics(self):
        total_processes = len(self.completed_processes) + len(self.foreground_queue) + len(self.background_queue)
        completed_count = len(self.completed_processes)
        
        if completed_count > 0:
            avg_waiting = sum(p['waiting_time'] for p in self.completed_processes) / completed_count
            avg_turnaround = sum(p['turnaround_time'] for p in self.completed_processes) / completed_count
        else:
            avg_waiting = avg_turnaround = 0
        
        starvation_count = self.get_starvation_count()
        
        return {
            'total_processes': total_processes,
            'completed_processes': completed_count,
            'avg_waiting_time': round(avg_waiting, 2),
            'avg_turnaround_time': round(avg_turnaround, 2),
            'starvation_count': starvation_count,
            'current_time': self.current_time,
            'foreground_queue_size': len(self.foreground_queue),
            'background_queue_size': len(self.background_queue)
        }
    
    def reset(self):
        self.current_time = 0
        self.foreground_queue.clear()
        self.background_queue.clear()
        self.completed_processes.clear()