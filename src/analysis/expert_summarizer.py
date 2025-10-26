"""Expert opinion summarizer - aggregates and summarizes expert predictions."""

import logging
from collections import Counter
from sqlalchemy.orm import Session

from src.models import Match, ExpertOpinion

logger = logging.getLogger(__name__)


class ExpertSummarizer:
    """Summarize expert opinions for matches."""

    def __init__(self, db: Session) -> None:
        """Initialize expert summarizer."""
        self.db = db

    def summarize_match(self, match: Match) -> str:
        """
        Summarize expert opinions for a single match.

        Args:
            match: Match to summarize opinions for

        Returns:
            Summary string describing expert consensus
        """
        if not match.expert_opinions:
            return "Inga experttips tillgängliga."

        # Count predictions
        predictions = [op.prediction for op in match.expert_opinions]
        prediction_counts = Counter(predictions)

        # Build summary
        total_experts = len(predictions)
        most_common = prediction_counts.most_common(1)[0]
        consensus_prediction = most_common[0]
        consensus_count = most_common[1]
        consensus_percentage = (consensus_count / total_experts) * 100

        # Build summary text
        summary_parts = [
            f"{total_experts} experter tippat.",
        ]

        if consensus_percentage >= 60:
            summary_parts.append(
                f"Stark konsensus för {consensus_prediction} ({consensus_count}/{total_experts}, "
                f"{consensus_percentage:.0f}%)."
            )
        elif consensus_percentage >= 40:
            summary_parts.append(
                f"Svag konsensus för {consensus_prediction} ({consensus_count}/{total_experts}, "
                f"{consensus_percentage:.0f}%)."
            )
        else:
            summary_parts.append(
                f"Delade meningar. Vanligast: {consensus_prediction} "
                f"({consensus_count}/{total_experts})."
            )

        # Add breakdown of all predictions
        breakdown = ", ".join(
            f"{pred}={count}" for pred, count in prediction_counts.most_common()
        )
        summary_parts.append(f"Fördelning: {breakdown}.")

        # Add sample reasoning if available
        opinions_with_reasoning = [
            op for op in match.expert_opinions if op.reasoning
        ]
        if opinions_with_reasoning:
            sample_opinion = opinions_with_reasoning[0]
            summary_parts.append(
                f"Exempel: {sample_opinion.source} tippar {sample_opinion.prediction} - "
                f"{sample_opinion.reasoning[:100]}..."
            )

        return " ".join(summary_parts)

    def summarize_all_matches(self, coupon_id: int) -> dict[int, str]:
        """
        Summarize expert opinions for all matches on a coupon.

        Args:
            coupon_id: ID of the coupon

        Returns:
            Dict mapping match_number to summary string
        """
        from src.models import Coupon

        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            raise ValueError(f"Coupon {coupon_id} not found")

        summaries = {}
        for match in coupon.matches:
            summary = self.summarize_match(match)
            summaries[match.match_number] = summary

            # Update analysis with summary
            if match.analysis:
                match.analysis.expert_summary = summary

        self.db.commit()
        logger.info(f"Summarized expert opinions for {len(summaries)} matches")

        return summaries
