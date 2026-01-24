"""
Historical learning module for Carlos the Architect.

Queries past deployment feedback to inform new designs with:
- Successful patterns to recommend (high ratings, success=true)
- Patterns to warn about (low ratings, issues_encountered)
- Cloud provider-specific insights

This enables Carlos and Ronei to learn from real deployment outcomes.
"""

import asyncio
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from feedback import StoredFeedback, get_feedback_store


# Configuration constants
MIN_FEEDBACK_FOR_LEARNING = 3       # Minimum feedback records to include learning
HIGH_RATING_THRESHOLD = 4           # 4-5 stars = successful pattern
LOW_RATING_THRESHOLD = 2            # 1-2 stars = problematic pattern
MAX_HISTORICAL_RESULTS = 20         # Maximum feedback records to analyze
LEARNING_TIMEOUT_SECONDS = 5.0      # Timeout for historical queries

# Common stop words to filter out from keyword extraction
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "i", "me", "my", "we", "our", "you", "your", "it", "its", "this",
    "that", "these", "those", "which", "what", "who", "whom", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "also", "now", "here",
    "want", "build", "create", "system", "application", "app", "service",
    "use", "using", "need", "needs", "like", "please", "help", "make",
}


@dataclass
class HistoricalInsight:
    """A single insight from historical feedback."""
    insight_type: str  # "success_pattern" | "warning" | "common_issue"
    description: str
    source_count: int  # How many feedback records support this insight
    cloud_provider: Optional[str] = None
    avg_rating: Optional[float] = None


@dataclass
class HistoricalContext:
    """Aggregated historical context for prompt injection."""
    success_patterns: List[HistoricalInsight] = field(default_factory=list)
    warnings: List[HistoricalInsight] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)
    total_feedback_analyzed: int = 0
    has_relevant_history: bool = False


class HistoricalLearningService:
    """Service to query and analyze historical feedback for learning."""

    def __init__(self, feedback_store=None):
        self._store = feedback_store

    def _get_store(self):
        """Get the feedback store (lazy initialization)."""
        if self._store is None:
            try:
                self._store = get_feedback_store()
            except RuntimeError:
                return None
        return self._store

    def _extract_keywords(self, requirements: str) -> List[str]:
        """
        Extract meaningful keywords from requirements for matching.

        Returns a list of lowercase keywords, filtered for relevance.
        """
        # Normalize text: lowercase, remove special chars except hyphens
        text = requirements.lower()
        text = re.sub(r'[^\w\s-]', ' ', text)

        # Tokenize
        words = text.split()

        # Filter out stop words and short words
        keywords = [
            word for word in words
            if word not in STOP_WORDS
            and len(word) >= 3
            and not word.isdigit()
        ]

        # Also extract potential tech terms (containing hyphens or specific patterns)
        tech_patterns = [
            r'\b(kubernetes|k8s|docker|container)\b',
            r'\b(azure|aws|gcp|cloud)\b',
            r'\b(api|rest|graphql|grpc)\b',
            r'\b(database|sql|nosql|redis|cosmos|dynamo)\b',
            r'\b(authentication|auth|oauth|jwt)\b',
            r'\b(microservice|monolith|serverless|lambda)\b',
            r'\b(ci/cd|pipeline|deployment|terraform)\b',
            r'\b(load.?balancer|cdn|cache|queue)\b',
            r'\b(real.?time|streaming|event.?driven)\b',
            r'\b(web|mobile|frontend|backend)\b',
            r'\b(scale|scaling|high.?availability|ha)\b',
            r'\b(security|encryption|firewall|waf)\b',
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, requirements.lower())
            keywords.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:20]  # Limit to top 20 keywords

    def _calculate_similarity_score(
        self,
        requirements_keywords: List[str],
        feedback: StoredFeedback
    ) -> float:
        """
        Calculate keyword-based similarity between requirements and stored feedback.

        Returns 0.0-1.0 score based on keyword overlap.
        """
        if not feedback.requirements_summary:
            return 0.0

        feedback_keywords = set(self._extract_keywords(feedback.requirements_summary))
        requirements_set = set(requirements_keywords)

        if not requirements_set or not feedback_keywords:
            return 0.0

        # Jaccard similarity with boost for exact matches
        intersection = requirements_set & feedback_keywords
        union = requirements_set | feedback_keywords

        if not union:
            return 0.0

        base_score = len(intersection) / len(union)

        # Boost score if multiple keywords match
        if len(intersection) >= 3:
            base_score = min(1.0, base_score * 1.2)

        return base_score

    async def find_similar_feedback(
        self,
        requirements: str,
        cloud_provider: Optional[str] = None,
        limit: int = MAX_HISTORICAL_RESULTS
    ) -> List[Tuple[StoredFeedback, float]]:
        """
        Find feedback records similar to given requirements.

        Returns list of (feedback, similarity_score) tuples, sorted by relevance.
        """
        store = self._get_store()
        if store is None:
            return []

        keywords = self._extract_keywords(requirements)
        if not keywords:
            return []

        try:
            # Search for feedback matching keywords
            all_feedback = await store.search_by_keywords(
                keywords=keywords,
                cloud_provider=cloud_provider,
                limit=limit * 2  # Get more than needed for scoring
            )

            if not all_feedback:
                return []

            # Score and sort by similarity
            scored_feedback = [
                (fb, self._calculate_similarity_score(keywords, fb))
                for fb in all_feedback
            ]

            # Filter out low similarity scores
            scored_feedback = [
                (fb, score) for fb, score in scored_feedback
                if score > 0.1
            ]

            # Sort by similarity score (descending)
            scored_feedback.sort(key=lambda x: x[1], reverse=True)

            return scored_feedback[:limit]

        except Exception as e:
            print(f"  Error finding similar feedback: {e}")
            return []

    def _categorize_feedback(
        self,
        feedback_list: List[Tuple[StoredFeedback, float]]
    ) -> Tuple[List[StoredFeedback], List[StoredFeedback]]:
        """Split feedback into successful (high-rated) and problematic (low-rated)."""
        successful = []
        problematic = []

        for feedback, _ in feedback_list:
            if feedback.satisfaction_rating >= HIGH_RATING_THRESHOLD and feedback.success:
                successful.append(feedback)
            elif feedback.satisfaction_rating <= LOW_RATING_THRESHOLD or not feedback.success:
                problematic.append(feedback)

        return successful, problematic

    def _extract_success_patterns(
        self,
        successful_feedback: List[StoredFeedback]
    ) -> List[HistoricalInsight]:
        """Extract patterns from successful deployments."""
        patterns = []

        # Group by modifications made (what worked well)
        modifications_count = {}
        for fb in successful_feedback:
            if fb.modifications_made:
                # Normalize and truncate
                mod = fb.modifications_made.strip()[:200]
                if mod:
                    key = mod.lower()
                    if key not in modifications_count:
                        modifications_count[key] = {
                            "description": mod,
                            "count": 0,
                            "ratings": []
                        }
                    modifications_count[key]["count"] += 1
                    modifications_count[key]["ratings"].append(fb.satisfaction_rating)

        # Convert to insights
        for key, data in modifications_count.items():
            if data["count"] >= 1:
                avg_rating = sum(data["ratings"]) / len(data["ratings"])
                patterns.append(HistoricalInsight(
                    insight_type="success_pattern",
                    description=data["description"],
                    source_count=data["count"],
                    avg_rating=round(avg_rating, 1)
                ))

        # Also extract from positive comments
        comments_insights = {}
        for fb in successful_feedback:
            if fb.comments and fb.satisfaction_rating >= 4:
                comment = fb.comments.strip()[:200]
                if comment and len(comment) > 20:  # Filter very short comments
                    key = comment.lower()[:50]  # Use first 50 chars as key
                    if key not in comments_insights:
                        comments_insights[key] = {
                            "description": comment,
                            "count": 0
                        }
                    comments_insights[key]["count"] += 1

        for key, data in comments_insights.items():
            patterns.append(HistoricalInsight(
                insight_type="success_pattern",
                description=f"User feedback: {data['description']}",
                source_count=data["count"]
            ))

        # Sort by source count and return top patterns
        patterns.sort(key=lambda x: x.source_count, reverse=True)
        return patterns[:5]

    def _extract_warnings(
        self,
        problematic_feedback: List[StoredFeedback]
    ) -> List[HistoricalInsight]:
        """Extract warnings from problematic deployments."""
        warnings = []

        # Group by issues encountered
        issues_count = {}
        for fb in problematic_feedback:
            if fb.issues_encountered:
                for issue in fb.issues_encountered:
                    issue = issue.strip()[:150]
                    if issue:
                        key = issue.lower()
                        if key not in issues_count:
                            issues_count[key] = {
                                "description": issue,
                                "count": 0
                            }
                        issues_count[key]["count"] += 1

        # Convert to insights
        for key, data in issues_count.items():
            warnings.append(HistoricalInsight(
                insight_type="warning",
                description=data["description"],
                source_count=data["count"]
            ))

        # Also extract from negative comments
        for fb in problematic_feedback:
            if fb.comments and fb.satisfaction_rating <= 2:
                comment = fb.comments.strip()[:150]
                if comment and len(comment) > 20:
                    warnings.append(HistoricalInsight(
                        insight_type="warning",
                        description=f"User reported: {comment}",
                        source_count=1
                    ))

        # Sort by source count and return top warnings
        warnings.sort(key=lambda x: x.source_count, reverse=True)
        return warnings[:5]

    def _aggregate_common_issues(
        self,
        feedback_list: List[Tuple[StoredFeedback, float]]
    ) -> List[str]:
        """Aggregate common issues across all feedback."""
        issues_count = {}

        for fb, _ in feedback_list:
            if fb.issues_encountered:
                for issue in fb.issues_encountered:
                    issue = issue.strip().lower()[:100]
                    if issue:
                        issues_count[issue] = issues_count.get(issue, 0) + 1

        # Sort by count and return top issues
        sorted_issues = sorted(
            issues_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [issue for issue, count in sorted_issues[:5] if count >= 1]

    async def get_historical_context(
        self,
        requirements: str,
        cloud_provider: Optional[str] = None
    ) -> HistoricalContext:
        """
        Main entry point: Get historical learning context for new design.

        This is called by the LangGraph workflow before design generation.
        """
        context = HistoricalContext()

        if not requirements:
            return context

        try:
            # Find similar feedback
            similar_feedback = await self.find_similar_feedback(
                requirements=requirements,
                cloud_provider=cloud_provider
            )

            if not similar_feedback:
                return context

            context.total_feedback_analyzed = len(similar_feedback)

            # Categorize feedback
            successful, problematic = self._categorize_feedback(similar_feedback)

            # Extract insights
            context.success_patterns = self._extract_success_patterns(successful)
            context.warnings = self._extract_warnings(problematic)
            context.common_issues = self._aggregate_common_issues(similar_feedback)

            # Mark as having relevant history if we have enough data
            context.has_relevant_history = (
                context.total_feedback_analyzed >= MIN_FEEDBACK_FOR_LEARNING
                or len(context.success_patterns) > 0
                or len(context.warnings) > 0
            )

            return context

        except Exception as e:
            print(f"  Error getting historical context: {e}")
            return context

    def format_for_prompt(self, context: HistoricalContext) -> str:
        """
        Format historical context as text for prompt injection.

        Returns empty string if no relevant history exists.
        """
        if not context.has_relevant_history:
            return ""

        if context.total_feedback_analyzed < MIN_FEEDBACK_FOR_LEARNING:
            if not context.success_patterns and not context.warnings:
                return ""

        lines = [
            "## Historical Learning from Past Deployments",
            "",
            f"Based on {context.total_feedback_analyzed} similar past designs, here are insights to consider:",
            ""
        ]

        # Success patterns
        if context.success_patterns:
            lines.append("### Patterns That Worked Well (from successful deployments rated 4-5 stars):")
            for pattern in context.success_patterns:
                rating_info = f" (avg rating: {pattern.avg_rating}/5)" if pattern.avg_rating else ""
                count_info = f" - appeared in {pattern.source_count} successful deployment(s)"
                lines.append(f"- {pattern.description}{rating_info}{count_info}")
            lines.append("")

        # Warnings
        if context.warnings:
            lines.append("### Patterns to Avoid (from deployments with issues):")
            for warning in context.warnings:
                count_info = f" - caused problems in {warning.source_count} deployment(s)"
                lines.append(f"- **Warning**: {warning.description}{count_info}")
            lines.append("")

        # Common issues
        if context.common_issues:
            lines.append("### Common Issues Encountered:")
            for issue in context.common_issues:
                lines.append(f"- {issue}")
            lines.append("")

        lines.append("Apply these learnings while designing, but use your judgment - every project is different.")
        lines.append("")

        return "\n".join(lines)


# Singleton instance
_learning_service: Optional[HistoricalLearningService] = None


async def get_historical_context(
    requirements: str,
    cloud_provider: Optional[str] = None
) -> str:
    """
    Convenience function to get formatted historical context.

    Returns formatted string ready for prompt injection, or empty string.
    Includes timeout handling to prevent blocking the design workflow.
    """
    global _learning_service
    if _learning_service is None:
        _learning_service = HistoricalLearningService()

    try:
        context = await asyncio.wait_for(
            _learning_service.get_historical_context(requirements, cloud_provider),
            timeout=LEARNING_TIMEOUT_SECONDS
        )
        return _learning_service.format_for_prompt(context)
    except asyncio.TimeoutError:
        print("  Historical learning timed out")
        return ""
    except Exception as e:
        print(f"  Historical learning failed: {e}")
        return ""
