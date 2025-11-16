#!/usr/bin/env python3
"""
Database initialization script for QuantCoach LiveKit Interview Platform

Usage:
    python init_db.py              # Initialize database
    python init_db.py --reset      # Reset database (delete all data!)
    python init_db.py --check      # Check database health
    python init_db.py --stats      # Show table statistics
"""

import sys
import argparse
import logging
from database import init_db, reset_db, check_db_health, get_table_counts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="QuantCoach Database Management")
    parser.add_argument("--reset", action="store_true", help="Reset database (WARNING: deletes all data!)")
    parser.add_argument("--check", action="store_true", help="Check database health")
    parser.add_argument("--stats", action="store_true", help="Show table statistics")

    args = parser.parse_args()

    try:
        if args.reset:
            confirm = input("⚠️  WARNING: This will DELETE ALL DATA! Type 'yes' to confirm: ")
            if confirm.lower() == "yes":
                reset_db()
                logger.info("✅ Database has been reset")
            else:
                logger.info("❌ Reset cancelled")
                return

        elif args.check:
            logger.info("🔍 Checking database health...")
            if check_db_health():
                logger.info("✅ Database is healthy")
            else:
                logger.error("❌ Database health check failed")
                sys.exit(1)

        elif args.stats:
            logger.info("📊 Fetching table statistics...")
            counts = get_table_counts()
            logger.info("\n📈 Table Row Counts:")
            logger.info("=" * 50)
            for table_name, count in sorted(counts.items()):
                logger.info(f"  {table_name:30s} : {count:>6d} rows")
            logger.info("=" * 50)
            total = sum(c for c in counts.values() if c >= 0)
            logger.info(f"  {'TOTAL':30s} : {total:>6d} rows\n")

        else:
            # Default: Initialize database
            logger.info("🚀 Initializing QuantCoach Interview Platform database...")
            init_db()
            logger.info("✅ Database initialization complete!")
            logger.info("\n📋 Next steps:")
            logger.info("  1. Start the backend server: python server.py")
            logger.info("  2. Start the frontend: cd ../frontend && npm run dev")
            logger.info("  3. Open http://localhost:5173 in your browser\n")

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
