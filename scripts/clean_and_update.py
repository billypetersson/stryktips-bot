#!/usr/bin/env python3
"""
Clean existing coupon and run update.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.session import SessionLocal
from src.models.coupon import Coupon


def clean_and_update():
    """Delete existing coupons and run update."""
    print("🗑️  Cleaning existing coupons...")

    db = SessionLocal()
    try:
        # Delete all coupons (this will cascade delete related data)
        deleted_count = db.query(Coupon).delete()
        db.commit()
        print(f"✓ Deleted {deleted_count} existing coupon(s)")
    except Exception as e:
        db.rollback()
        print(f"✗ Error cleaning database: {e}")
        raise
    finally:
        db.close()

    print("\n🔄 Now run: python -m src.jobs.update_coupon")


if __name__ == "__main__":
    clean_and_update()
