#!/usr/bin/env python3
"""Run analysis on Liverpool - Aston Villa match."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database.session import SessionLocal
from src.models import Coupon, Match
from src.analysis.value_calculator import ValueCalculator
from src.analysis.expert_summarizer import ExpertSummarizer
from src.analysis.row_generator import RowGenerator

def main():
    """Run analysis on week 44 coupon."""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("ANALYZING WEEK 44 COUPON (Liverpool - Aston Villa)")
        print("=" * 60)

        # Get week 44 coupon
        coupon = db.query(Coupon).filter(
            Coupon.week_number == 44,
            Coupon.year == 2025
        ).first()

        if not coupon:
            print("ERROR: Week 44 coupon not found!")
            return

        print(f"\n✓ Found coupon: Week {coupon.week_number}, {coupon.year}")

        # Get matches
        matches = db.query(Match).filter(Match.coupon_id == coupon.id).all()
        print(f"✓ Found {len(matches)} match(es)")

        for match in matches:
            print(f"  {match.match_number}. {match.home_team} - {match.away_team}")

        # Step 1: Calculate value
        print("\n" + "-" * 60)
        print("Step 1: Calculating value for all matches")
        print("-" * 60)

        calculator = ValueCalculator(db)
        analyses = calculator.calculate_all_matches(coupon.id)
        print(f"✓ Calculated value for {len(analyses)} match(es)")

        for analysis in analyses:
            match = db.query(Match).filter(Match.id == analysis.match_id).first()
            print(f"\n  Match {match.match_number}: {match.home_team} - {match.away_team}")
            print(f"    Avg odds: 1={analysis.avg_home_odds:.2f} X={analysis.avg_draw_odds:.2f} 2={analysis.avg_away_odds:.2f}")
            print(f"    True prob: 1={analysis.true_home_prob:.1%} X={analysis.true_draw_prob:.1%} 2={analysis.true_away_prob:.1%}")
            print(f"    Value: 1={analysis.home_value:.2f} X={analysis.draw_value:.2f} 2={analysis.away_value:.2f}")
            print(f"    Recommended: {analysis.recommended_signs}")

        # Step 2: Summarize expert opinions
        print("\n" + "-" * 60)
        print("Step 2: Summarizing expert opinions")
        print("-" * 60)

        summarizer = ExpertSummarizer(db)
        summaries = summarizer.summarize_all_matches(coupon.id)
        print(f"✓ Summarized opinions for {len(summaries)} match(es)")

        for match_id, summary in summaries.items():
            match = db.query(Match).filter(Match.id == match_id).first()
            analysis = db.query(Analysis).filter(Analysis.match_id == match_id).first()
            if analysis and analysis.expert_summary:
                print(f"\n  Match {match.match_number}: {analysis.expert_summary}")

        # Step 3: Generate suggested rows
        print("\n" + "-" * 60)
        print("Step 3: Generating suggested rows")
        print("-" * 60)

        generator = RowGenerator(db)
        suggested_rows = generator.generate_rows(coupon.id, max_rows=5)
        print(f"✓ Generated {len(suggested_rows)} suggested row(s)")

        if suggested_rows:
            print("\nTOP SUGGESTED ROWS:")
            for i, row in enumerate(suggested_rows[:3], 1):
                print(f"\n  Row {i}:")
                print(f"    Signs: {row.row_data}")
                print(f"    Expected Value: {row.expected_value:.2f}")
                print(f"    Half covers: {row.half_cover_count}")
                print(f"    Cost factor: {row.cost_factor:.1f}x")
                if row.reasoning:
                    print(f"    Reasoning: {row.reasoning}")

        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE!")
        print("=" * 60)
        print("\nView results at: http://localhost:8000/")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    # Import Analysis here to avoid circular import
    from src.models.analysis import Analysis
    main()
