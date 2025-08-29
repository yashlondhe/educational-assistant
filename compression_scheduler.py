"""
Compression scheduler for running periodic compression of conversation history.
Can be run as a cron job or scheduled task.
"""

import os
import sys
import logging
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from llm_interface import LLMInterface
from history_manager import HistoryManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('compression_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_compression(db_path: str = None, dry_run: bool = False):
    """Run the compression cycle."""
    logger.info(f"Starting compression run at {datetime.now()}")
    
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    try:
        # Initialize components
        db = Database(db_path) if db_path else Database()
        llm = LLMInterface()
        history_manager = HistoryManager(db, llm)
        
        if dry_run:
            # Just show what would be compressed
            logger.info("Sessions that would be compressed:")
            
            # Check each compression level
            for days, level in [(7, 'none'), (30, 'light'), (90, 'medium')]:
                sessions = db.get_sessions_for_compression(days, level)
                if sessions:
                    logger.info(f"\n{level.upper()} -> next level ({len(sessions)} sessions):")
                    for session in sessions[:5]:  # Show first 5
                        logger.info(f"  - Session {session['session_id']} from {session['timestamp']}")
                    if len(sessions) > 5:
                        logger.info(f"  ... and {len(sessions) - 5} more")
        else:
            # Run actual compression
            results = history_manager.run_compression_cycle()
            
            logger.info("Compression results:")
            logger.info(f"  - Light compressions: {results['light_compressed']}")
            logger.info(f"  - Medium compressions: {results['medium_compressed']}")
            logger.info(f"  - Heavy compressions: {results['heavy_compressed']}")
            logger.info(f"  - Profiles updated: {results['profiles_updated']}")
            logger.info(f"  - Errors: {results['errors']}")
        
        logger.info(f"Compression run completed at {datetime.now()}")
        
    except Exception as e:
        logger.error(f"Error during compression run: {e}")
        raise


def setup_cron_job():
    """Print instructions for setting up a cron job."""
    script_path = os.path.abspath(__file__)
    python_path = sys.executable
    
    print("\nTo set up automatic compression, add this to your crontab:")
    print("(Run 'crontab -e' to edit your crontab)")
    print("\n# Run compression daily at 2 AM")
    print(f"0 2 * * * {python_path} {script_path}")
    print("\n# Or run compression weekly on Sundays at 3 AM")
    print(f"0 3 * * 0 {python_path} {script_path}")
    print("\n# With custom database path:")
    print(f"0 2 * * * {python_path} {script_path} --db-path /path/to/database.db")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run compression on conversation history"
    )
    parser.add_argument(
        '--db-path',
        type=str,
        help='Path to the database file (default: educational_assistant.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be compressed without making changes'
    )
    parser.add_argument(
        '--setup-cron',
        action='store_true',
        help='Show instructions for setting up a cron job'
    )
    
    args = parser.parse_args()
    
    if args.setup_cron:
        setup_cron_job()
    else:
        run_compression(args.db_path, args.dry_run)


if __name__ == "__main__":
    main()
