import psycopg2
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.init_database()
    
    def get_connection(self):
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None
    
    def init_database(self):
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Processes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processes (
                    id SERIAL PRIMARY KEY,
                    pid INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    arrival_time INTEGER NOT NULL,
                    burst_time INTEGER NOT NULL,
                    priority INTEGER NOT NULL,
                    queue_type VARCHAR(50) NOT NULL,
                    remaining_time INTEGER NOT NULL,
                    waiting_time INTEGER DEFAULT 0,
                    turnaround_time INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Simulation results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulation_results (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_processes INTEGER,
                    completed_processes INTEGER,
                    avg_waiting_time FLOAT,
                    avg_turnaround_time FLOAT,
                    starvation_count INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            print("Database and tables created successfully!")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    def add_process(self, process):
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processes (pid, name, arrival_time, burst_time, priority, queue_type, remaining_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (process['pid'], process['name'], process['arrival_time'], 
                  process['burst_time'], process['priority'], process['queue_type'],
                  process['burst_time']))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding process: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    def get_all_processes(self):
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM processes ORDER BY arrival_time')
            processes = cursor.fetchall()
            return processes
        except Exception as e:
            print(f"Error getting processes: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    def get_pending_processes(self):
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM processes WHERE completed = FALSE ORDER BY arrival_time')
            processes = cursor.fetchall()
            return processes
        except Exception as e:
            print(f"Error getting pending processes: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    def update_process(self, pid, updates):
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{key} = %s" for key in updates.keys()])
            values = list(updates.values())
            values.append(pid)
            cursor.execute(f'UPDATE processes SET {set_clause} WHERE pid = %s', values)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating process: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    def save_simulation_result(self, result):
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO simulation_results 
                (total_processes, completed_processes, avg_waiting_time, avg_turnaround_time, starvation_count)
                VALUES (%s, %s, %s, %s, %s)
            ''', (result['total_processes'], result['completed_processes'],
                  result['avg_waiting_time'], result['avg_turnaround_time'],
                  result['starvation_count']))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving simulation result: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    def clear_processes(self):
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM processes')
            conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing processes: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    def get_simulation_history(self):
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM simulation_results ORDER BY timestamp DESC LIMIT 10')
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error getting simulation history: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                conn.close()