"""Script to manually run analysis on a coupon."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.session import SessionLocal
from src.analysis.value_calculator import ValueCalculator
from src.analysis.expert_summarizer import ExpertSummarizer
from src.analysis.row_generator import RowGenerator
from src.models import Coupon


def main() -> None:
    """Run analysis on latest active coupon."""
    db = SessionLocal()

    try:
        # Get latest active coupon
        coupon = db.query(Coupon).filter(Coupon.is_active == True).order_by(
            Coupon.week_number.desc()
        ).first()

        if not coupon:
            print("No active coupon found. Run update_coupon.py first.")
            return

        print(f"Analyzing coupon: Week {coupon.week_number}/{coupon.year}")

        # Calculate value
        print("\n1. Calculating value for all matches...")
        calculator = ValueCalculator(db)
        analyses = calculator.calculate_all_matches(coupon.id)
        print(f"   ✓ Calculated value for {len(analyses)} matches")

        # Summarize experts
        print("\n2. Summarizing expert opinions...")
        summarizer = ExpertSummarizer(db)
        summaries = summarizer.summarize_all_matches(coupon.id)
        print(f"   ✓ Summarized opinions for {len(summaries)} matches")

        # Generate rows
        print("\n3. Generating suggested rows...")
        generator = RowGenerator(db)
        rows = generator.generate_rows(coupon.id, max_rows=3)
        print(f"   ✓ Generated {len(rows)} suggested rows")

        # Display results
        print("\n" + "="*60)
        print("SUGGESTED ROWS")
        print("="*60)

        for i, row in enumerate(rows, 1):
            print(f"\nRow {i}:")
            print(f"  Expected Value: {row.expected_value:.3f}")
            print(f"  Half Covers: {row.half_cover_count}")
            print(f"  Cost Factor: {row.cost_factor}x")
            print(f"  Signs: {', '.join(f'{k}:{v}' for k, v in sorted(row.row_data.items(), key=lambda x: int(x[0])))}")
            print(f"  Reasoning: {row.reasoning}")

        print("\n✓ Analysis complete!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
