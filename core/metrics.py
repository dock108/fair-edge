"""
Prometheus label hygiene helper - Phase 3.6
Prevents high-cardinality labels as warned in Prometheus documentation

This module provides utilities to sanitize and validate metric labels
to maintain Prometheus performance and avoid cardinality explosions.
"""

import logging
import re
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

# Configuration constants
MAX_LABEL_LENGTH = 32
MAX_DISTINCT_VALUES_PER_LABEL = 100
ALLOWED_LABEL_CHARS = re.compile(r"^[a-zA-Z0-9_]+$")

# Track distinct values per label to monitor cardinality
_label_cardinality_tracker: Dict[str, Set[str]] = {}


def safe_label(value: Any, label_name: str = "unknown") -> Optional[str]:
    """
    Sanitize label value for Prometheus compatibility

    Args:
        value: Raw label value to sanitize
        label_name: Name of the label (for tracking cardinality)

    Returns:
        Sanitized label value or None if should be dropped

    Following Prometheus best practices to avoid high cardinality
    """
    if value is None or (isinstance(value, str) and not value):
        return None

    # Convert to string and strip
    clean_value = str(value).strip()

    if not clean_value:
        return None

    # Check length limit
    if len(clean_value) > MAX_LABEL_LENGTH:
        logger.debug(f"Label value too long, truncating: {label_name}={clean_value[:10]}...")
        return None

    # Check if contains only safe characters
    # For numeric input (int/float), allow decimal points in the string representation
    # For string input, use stricter validation, with exceptions for endpoint
    # labels
    if isinstance(value, (int, float, bool)):
        # Numeric values converted to strings can have decimal points
        safe_chars_pattern = re.compile(r"^[a-zA-Z0-9_.]+$")
    elif label_name == "endpoint":
        # Endpoint labels can contain forward slashes and curly braces (API
        # paths with placeholders)
        safe_chars_pattern = re.compile(r"^[a-zA-Z0-9_/{}]+$")
    else:
        # String values must be alphanumeric + underscores only (strict
        # Prometheus labels)
        safe_chars_pattern = ALLOWED_LABEL_CHARS

    if not safe_chars_pattern.match(clean_value):
        logger.debug(f"Label value contains invalid characters: {label_name}={clean_value}")
        return None

    # Track cardinality
    if label_name not in _label_cardinality_tracker:
        _label_cardinality_tracker[label_name] = set()

    # Check cardinality limit
    if len(_label_cardinality_tracker[label_name]) >= MAX_DISTINCT_VALUES_PER_LABEL:
        if clean_value not in _label_cardinality_tracker[label_name]:
            logger.warning(
                f"High cardinality detected for label {label_name}, dropping value: {clean_value}"
            )
            return None

    # Add to tracker
    _label_cardinality_tracker[label_name].add(clean_value)

    return clean_value


def sanitize_labels(labels: Dict[str, Any]) -> Dict[str, str]:
    """
    Sanitize a dictionary of labels for Prometheus

    Args:
        labels: Dictionary of label names to values

    Returns:
        Dictionary with sanitized labels (invalid ones removed)
    """
    sanitized = {}

    for label_name, label_value in labels.items():
        # Sanitize label name
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", str(label_name))

        # Sanitize label value
        clean_value = safe_label(label_value, clean_name)

        if clean_value is not None:
            sanitized[clean_name] = clean_value
        else:
            logger.debug(f"Dropping label due to sanitization: {label_name}={label_value}")

    return sanitized


def get_cardinality_stats() -> Dict[str, Dict[str, Any]]:
    """
    Get current cardinality statistics for all tracked labels

    Returns:
        Dictionary with cardinality info per label
    """
    stats = {}

    for label_name, values in _label_cardinality_tracker.items():
        stats[label_name] = {
            "distinct_values": len(values),
            "is_high_cardinality": len(values)
            >= MAX_DISTINCT_VALUES_PER_LABEL * 0.8,  # 80% threshold
            # First 5 values as examples
            "sample_values": (list(values)[:5] if values else []),
        }

    return stats


def reset_cardinality_tracker():
    """Reset the cardinality tracker (useful for testing or periodic cleanup)"""
    _label_cardinality_tracker.clear()
    logger.info("Cardinality tracker reset")


def validate_metric_labels(metric_name: str, labels: Dict[str, Any]) -> bool:
    """
    Validate that metric labels are within acceptable cardinality limits

    Args:
        metric_name: Name of the metric
        labels: Labels to validate

    Returns:
        True if labels are valid, False if they would cause high cardinality
    """
    try:
        sanitized = sanitize_labels(labels)

        # Check if we lost too many labels during sanitization
        if len(sanitized) < len(labels) * 0.5:  # Lost more than 50% of labels
            logger.warning(f"Metric {metric_name} lost many labels during sanitization")
            return False

        # Check overall cardinality projection
        total_combinations = 1
        for label_name in sanitized.keys():
            if label_name in _label_cardinality_tracker:
                total_combinations *= len(_label_cardinality_tracker[label_name])

        if total_combinations > 10000:  # Arbitrary high limit
            logger.warning(
                f"Metric {metric_name} may cause high cardinality: {total_combinations} "
                "combinations"
            )
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating metric labels for {metric_name}: {e}")
        return False


class MetricLabelSanitizer:
    """
    Context manager for safely recording metrics with label sanitization

    Usage:
        with MetricLabelSanitizer("api_requests") as sanitizer:
            sanitizer.record(counter_metric, {"endpoint": "/api/data", "status": 200})
    """

    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.sanitized_labels: Dict[str, Any] = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, _exc_tb):
        if exc_type:
            logger.error(f"Error in metric recording for {self.metric_name}: {exc_val}")

    def record(self, metric, labels: Dict[str, Any], value: float = 1.0):
        """
        Record metric with sanitized labels

        Args:
            metric: Prometheus metric object
            labels: Labels to apply
            value: Value to record (for histograms/gauges)
        """
        try:
            # Validate and sanitize labels
            if not validate_metric_labels(self.metric_name, labels):
                logger.warning(f"Skipping metric {self.metric_name} due to validation failure")
                return

            clean_labels = sanitize_labels(labels)

            if hasattr(metric, "labels"):
                # Counter, Histogram, Gauge with labels
                labeled_metric = metric.labels(**clean_labels)

                if hasattr(labeled_metric, "observe"):
                    # Histogram
                    labeled_metric.observe(value)
                elif hasattr(labeled_metric, "set"):
                    # Gauge
                    labeled_metric.set(value)
                else:
                    # Counter
                    labeled_metric.inc(value)
            else:
                # Simple metric without labels
                if hasattr(metric, "observe"):
                    metric.observe(value)
                elif hasattr(metric, "set"):
                    metric.set(value)
                else:
                    metric.inc(value)

        except Exception as e:
            logger.error(f"Failed to record metric {self.metric_name}: {e}")


# Convenience functions for common use cases
def safe_sport_label(sport: str) -> Optional[str]:
    """Sanitize sport names for metrics"""
    # Map common sports to consistent labels
    sport_mapping = {
        "americanfootball_nfl": "nfl",
        "basketball_nba": "nba",
        "baseball_mlb": "mlb",
        "icehockey_nhl": "nhl",
    }

    mapped_sport = sport_mapping.get(sport, sport)
    return safe_label(mapped_sport, "sport")


def safe_endpoint_label(endpoint: str) -> Optional[str]:
    """Sanitize API endpoint names for metrics"""
    if not endpoint:
        return None

    # Normalize endpoint paths to reduce cardinality
    normalized = endpoint.lower()

    # Remove query parameters
    if "?" in normalized:
        normalized = normalized.split("?")[0]

    # Replace dynamic segments with placeholders
    # Replace UUIDs first (more specific pattern)
    normalized = re.sub(
        r"/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
        "/{uuid}",
        normalized,
    )
    # Replace numeric IDs (but only pure numbers, not UUIDs that start with
    # numbers)
    normalized = re.sub(r"/\d+(?![a-f0-9-])", "/{id}", normalized)

    # Remove special characters (but keep curly braces for placeholders)
    normalized = re.sub(r"[^a-zA-Z0-9_/{}]", "_", normalized)

    return safe_label(normalized, "endpoint")


def safe_status_code_label(status_code: int) -> Optional[str]:
    """Sanitize HTTP status codes for metrics"""
    # Group status codes to reduce cardinality
    if 200 <= status_code < 300:
        return "2xx"
    elif 300 <= status_code < 400:
        return "3xx"
    elif 400 <= status_code < 500:
        return "4xx"
    elif 500 <= status_code < 600:
        return "5xx"
    else:
        return "other"


# Export main interfaces
__all__ = [
    "safe_label",
    "sanitize_labels",
    "get_cardinality_stats",
    "reset_cardinality_tracker",
    "validate_metric_labels",
    "MetricLabelSanitizer",
    "safe_sport_label",
    "safe_endpoint_label",
    "safe_status_code_label",
]
