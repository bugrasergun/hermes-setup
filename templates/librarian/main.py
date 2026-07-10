import time
import datetime
import logger  # Initializes logging and exception hook
import logging
import watcher
import processor
import cron
from config import POLL_INTERVAL, CRON_HOUR

def main():
    logging.info("Librarian Daemon started.")
    last_cron_date = None
    
    while True:
        try:
            # 1. DB Polling
            watcher.poll_databases()
            
            # 2. Queue Processing
            # Process all pending tasks before sleeping
            while processor.process_queue():
                pass
                
            # 3. Cron Check
            now = datetime.datetime.now()
            today_str = now.date().isoformat()
            if now.hour == CRON_HOUR and last_cron_date != today_str:
                logging.info("Triggering daily report generation...")
                cron.generate_daily_report()
                last_cron_date = today_str
                
        except Exception as e:
            logging.error(f"Daemon error in main loop: {e}", exc_info=True)
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
