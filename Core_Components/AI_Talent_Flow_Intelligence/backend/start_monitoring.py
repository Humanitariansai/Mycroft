#!/usr/bin/env python3
"""
Standalone script to start the real-time monitoring service.
Runs the monitoring server on WebSocket port 8005.
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.real_time_monitor import start_monitoring_server

def main():
    """Start the monitoring server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Talent Flow Intelligence Real-Time Monitor")
    
    try:
        asyncio.run(start_monitoring_server())
    except KeyboardInterrupt:
        logger.info("Monitoring server stopped by user")
    except Exception as e:
        logger.error(f"Monitoring server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()