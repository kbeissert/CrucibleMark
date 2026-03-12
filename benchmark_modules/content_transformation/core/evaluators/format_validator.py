"""
Format Validator
Validates structure of specific content types (Twitter threads, JSON, Landing Pages)
"""

import json
import re
from typing import Dict, List, Tuple
from ..constants import FORMAT_SCHEMAS


class FormatValidator:
    """Validates specific content formats like Twitter threads, JSON, etc."""

    @staticmethod
    def validate_twitter_thread(
        response: str, config: Dict = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates a Twitter thread structure.
        Expects tweets to be separated by newlines or numbered like 1/X.
        """
        config = config or FORMAT_SCHEMAS.get("twitter_thread", {})
        min_tweets = config.get("min_tweets", 3)
        max_chars = config.get("max_chars_per_tweet", 280)
        pattern_str = config.get("pattern", r"^\d+/\d+")

        issues = []
        tweets = []

        # Strategy 1: Look for explicit numbering (e.g., 1/5)
        pattern = re.compile(pattern_str, re.MULTILINE)
        matches = list(pattern.finditer(response))

        if matches:
            # Extract content between matches
            for i, match in enumerate(matches):
                start = match.end()
                if i + 1 < len(matches):
                    end = matches[i + 1].start()
                else:
                    end = len(response)
                content = response[start:end].strip()
                tweets.append(content)
        elif "\n\n" in response:
            # Strategy 2: Split by double newlines if no numbering found
            # Filter out short lines that might be just spacers
            potential_tweets = response.split("\n\n")
            tweets = [t.strip() for t in potential_tweets if len(t.strip()) > 10]

        if not tweets:
            # Fallback: treat lines as tweets if there are multiple lines
            lines = [
                line.strip() for line in response.splitlines() if len(line.strip()) > 10
            ]
            if len(lines) >= min_tweets:
                tweets = lines

        # Validate constraints
        if len(tweets) < min_tweets:
            issues.append(f"Found {len(tweets)} tweets, expected at least {min_tweets}")

        for i, tweet in enumerate(tweets):
            if len(tweet) > max_chars:
                issues.append(
                    f"Tweet {i + 1} length {len(tweet)} exceeds limit of {max_chars}"
                )

        return len(issues) == 0, issues

    @staticmethod
    def validate_json_structure(
        response: str, schema: Dict = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates if the response contains valid JSON and optionally matches a schema.
        """
        config = FORMAT_SCHEMAS.get("json_export", {})
        issues = []
        json_content = response

        # Extract JSON from markdown code blocks if present
        if "```" in response:
            # Try to match optional "json" identifier
            match = re.search(r"```(?:json)?(.*?)```", response, re.DOTALL)
            if match:
                json_content = match.group(1).strip()

        try:
            data = json.loads(json_content)

            # Simple schema validation (keys presence)
            if schema:
                if isinstance(schema, list):
                    # If schema is just a list of required keys
                    required_keys = schema
                else:
                    required_keys = schema.get("required_keys", [])

                if isinstance(data, dict):
                    missing = [k for k in required_keys if k not in data]
                    if missing:
                        issues.append(
                            f"Missing required JSON keys: {', '.join(missing)}"
                        )
                elif isinstance(data, list) and required_keys:
                    # Check first item if it's a list
                    if data and isinstance(data[0], dict):
                        missing = [k for k in required_keys if k not in data[0]]
                        if missing:
                            issues.append(
                                f"Missing required keys: {', '.join(missing)}"
                            )

            is_strict = config.get("strict_mode", False)
            if is_strict and isinstance(data, dict) and schema:
                # Check for extra keys if strict mode is on and we have a schema
                required_set = set(schema.get("required_keys", []))
                actual_set = set(data.keys())
                extra = actual_set - required_set
                if extra:
                    issues.append(f"Found unauthorized extra keys: {', '.join(extra)}")

        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            issues.append(f"JSON validation error: {str(e)}")

        return len(issues) == 0, issues

    @staticmethod
    def validate_landing_page_structure(
        response: str, config: Dict = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates markdown structure for landing pages (Headers, CTA).
        """
        config = config or FORMAT_SCHEMAS.get("landing_page", {})
        required_sections = config.get("required_sections", [])
        max_headline_len = config.get("max_headline_chars", 60)

        issues = []
        lower_response = response.lower()

        # Check required sections loosely
        for section in required_sections:
            if section.lower() not in lower_response:
                issues.append(f"Missing required section: '{section}'")

        # Check headline length (assuming first H1 or first line)
        h1_match = re.search(r"^#\s+(.+)$", response, re.MULTILINE)
        if h1_match:
            headline = h1_match.group(1).strip()
            if len(headline) > max_headline_len:
                issues.append(
                    f"Main headline exceeds {max_headline_len} chars ({len(headline)})"
                )

        return len(issues) == 0, issues
