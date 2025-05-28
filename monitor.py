#!/usr/bin/env python3
"""
CVLatex System Monitor
Monitors system resources, application health, and logs performance metrics
"""

import os
import sys
import time
import psutil
import logging
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
MONITOR_INTERVAL = 60  # seconds
LOG_FILE = 'cvlatex_monitor.log'
APP_URL = 'http://localhost:8000'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
ALERT_THRESHOLDS = {
    'cpu_percent': 80,
    'memory_percent': 85,
    'disk_percent': 90,
    'response_time': 10.0  # seconds
}

class CVLatexMonitor:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.stats_history = []
        self.is_running = False
        
    def setup_logging(self):
        """Set up logging with rotation"""
        # Rotate log if too large
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
            backup_name = f"{LOG_FILE}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(LOG_FILE, backup_name)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def get_system_stats(self):
        """Get current system statistics"""
        stats = {
            'timestamp': datetime.now(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory(),
            'disk': psutil.disk_usage('.'),
            'network': psutil.net_io_counters(),
            'processes': len(psutil.pids())
        }
        
        # Calculate percentages
        stats['memory_percent'] = stats['memory'].percent
        stats['disk_percent'] = (stats['disk'].used / stats['disk'].total) * 100
        
        return stats
    
    def check_app_health(self):
        """Check if CVLatex application is responding"""
        try:
            start_time = time.time()
            response = requests.get(f"{APP_URL}/", timeout=10)
            response_time = time.time() - start_time
            
            return {
                'is_healthy': response.status_code == 200,
                'status_code': response.status_code,
                'response_time': response_time,
                'error': None
            }
        except requests.exceptions.RequestException as e:
            return {
                'is_healthy': False,
                'status_code': None,
                'response_time': None,
                'error': str(e)
            }
    
    def check_latex_status(self):
        """Check LaTeX availability"""
        try:
            response = requests.get(f"{APP_URL}/debug/system", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'latex_available': data.get('latex', {}).get('available_global', False),
                    'pdflatex_path': data.get('latex', {}).get('pdflatex_path', 'Unknown')
                }
        except:
            pass
        
        # Fallback: check directly
        import shutil
        return {
            'latex_available': shutil.which('pdflatex') is not None,
            'pdflatex_path': shutil.which('pdflatex') or 'Not found'
        }
    
    def check_disk_space(self):
        """Check disk space and clean up if needed"""
        disk_usage = psutil.disk_usage('.')
        free_gb = disk_usage.free / (1024**3)
        
        # Clean up old files if space is low
        if free_gb < 1.0:  # Less than 1GB
            self.cleanup_old_files()
        
        return {
            'free_gb': free_gb,
            'total_gb': disk_usage.total / (1024**3),
            'used_percent': (disk_usage.used / disk_usage.total) * 100
        }
    
    def cleanup_old_files(self):
        """Clean up old upload and output files"""
        try:
            cutoff_time = datetime.now() - timedelta(days=7)  # 7 days old
            
            for folder in ['uploads', 'output']:
                if os.path.exists(folder):
                    for file_path in Path(folder).iterdir():
                        if file_path.is_file():
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_time < cutoff_time:
                                file_path.unlink()
                                self.logger.info(f"Cleaned up old file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def check_alerts(self, stats, app_health):
        """Check for alert conditions"""
        alerts = []
        
        # CPU alert
        if stats['cpu_percent'] > ALERT_THRESHOLDS['cpu_percent']:
            alerts.append(f"HIGH CPU: {stats['cpu_percent']:.1f}%")
        
        # Memory alert
        if stats['memory_percent'] > ALERT_THRESHOLDS['memory_percent']:
            alerts.append(f"HIGH MEMORY: {stats['memory_percent']:.1f}%")
        
        # Disk alert
        if stats['disk_percent'] > ALERT_THRESHOLDS['disk_percent']:
            alerts.append(f"HIGH DISK USAGE: {stats['disk_percent']:.1f}%")
        
        # Application health alert
        if not app_health['is_healthy']:
            alerts.append(f"APP DOWN: {app_health.get('error', 'Unknown error')}")
        elif app_health['response_time'] and app_health['response_time'] > ALERT_THRESHOLDS['response_time']:
            alerts.append(f"SLOW RESPONSE: {app_health['response_time']:.2f}s")
        
        return alerts
    
    def log_stats(self, stats, app_health, latex_status, disk_info):
        """Log current statistics"""
        log_message = (
            f"STATS | CPU: {stats['cpu_percent']:.1f}% | "
            f"MEM: {stats['memory_percent']:.1f}% | "
            f"DISK: {stats['disk_percent']:.1f}% | "
            f"APP: {'UP' if app_health['is_healthy'] else 'DOWN'} | "
            f"LATEX: {'OK' if latex_status['latex_available'] else 'MISSING'} | "
            f"FREE: {disk_info['free_gb']:.1f}GB"
        )
        
        if app_health['response_time']:
            log_message += f" | RESPONSE: {app_health['response_time']:.2f}s"
        
        self.logger.info(log_message)
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("CVLatex Monitor started")
        
        while self.is_running:
            try:
                # Collect stats
                stats = self.get_system_stats()
                app_health = self.check_app_health()
                latex_status = self.check_latex_status()
                disk_info = self.check_disk_space()
                
                # Log stats
                self.log_stats(stats, app_health, latex_status, disk_info)
                
                # Check for alerts
                alerts = self.check_alerts(stats, app_health)
                for alert in alerts:
                    self.logger.warning(f"ALERT: {alert}")
                
                # Store history (keep last 24 hours)
                self.stats_history.append({
                    'stats': stats,
                    'app_health': app_health,
                    'latex_status': latex_status
                })
                
                # Keep only last 24 hours of data
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.stats_history = [
                    item for item in self.stats_history 
                    if item['stats']['timestamp'] > cutoff_time
                ]
                
                # Wait for next interval
                time.sleep(MONITOR_INTERVAL)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                time.sleep(10)  # Wait before retrying
        
        self.logger.info("CVLatex Monitor stopped")
    
    def start(self):
        """Start monitoring"""
        self.is_running = True
        self.monitor_loop()
    
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
    
    def print_status(self):
        """Print current status to console"""
        try:
            stats = self.get_system_stats()
            app_health = self.check_app_health()
            latex_status = self.check_latex_status()
            disk_info = self.check_disk_space()
            
            print("\n" + "="*60)
            print("           CVLatex System Status")
            print("="*60)
            print(f"Timestamp: {stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"CPU Usage: {stats['cpu_percent']:.1f}%")
            print(f"Memory:    {stats['memory_percent']:.1f}% ({stats['memory'].used / (1024**3):.1f}GB / {stats['memory'].total / (1024**3):.1f}GB)")
            print(f"Disk:      {stats['disk_percent']:.1f}% ({disk_info['free_gb']:.1f}GB free)")
            print(f"Processes: {stats['processes']}")
            print(f"App Health: {'✅ UP' if app_health['is_healthy'] else '❌ DOWN'}")
            if app_health['response_time']:
                print(f"Response:   {app_health['response_time']:.2f}s")
            print(f"LaTeX:      {'✅ Available' if latex_status['latex_available'] else '❌ Missing'}")
            print(f"pdflatex:   {latex_status['pdflatex_path']}")
            print("="*60)
            
        except Exception as e:
            print(f"Error getting status: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        # Just print status and exit
        monitor = CVLatexMonitor()
        monitor.print_status()
        return
    
    # Start continuous monitoring
    monitor = CVLatexMonitor()
    
    try:
        print("🔍 CVLatex Monitor starting...")
        print(f"📊 Monitoring interval: {MONITOR_INTERVAL} seconds")
        print(f"📄 Log file: {LOG_FILE}")
        print(f"🌐 App URL: {APP_URL}")
        print("Press Ctrl+C to stop monitoring\n")
        
        monitor.start()
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 