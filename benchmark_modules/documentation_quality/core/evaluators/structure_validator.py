"""
Structure Validator module.
Validates Markdown structure checks (headings, code blocks, hierarchy).
"""

import re
from typing import List, Dict, Any
from ..constants import DOC_TYPE_SCHEMAS


class StructureValidator:
    """
    Validates the structural integrity of Markdown documentation.
    Checks for heading hierarchy, code block counts, and required sections.
    """

    @staticmethod
    def validate_markdown_structure(response: str, doc_type: str) -> Dict[str, Any]:
        """
        Validates markdown structure and returns violations and stats.
        """
        violations = []
        schema = DOC_TYPE_SCHEMAS.get(doc_type)
        if schema is None:
            schema = DOC_TYPE_SCHEMAS.get("readme", {})

        # Keep type checker happy
        assert schema is not None

        # 1. Heading Hierarchy
        hierarchy_violations = StructureValidator.check_heading_hierarchy(response)
        violations.extend(hierarchy_violations)

        # 2. Stats
        heading_count = len(re.findall(r"^#{1,6}\s", response, re.MULTILINE))
        code_block_count = StructureValidator.count_code_blocks(response)
        list_count = len(re.findall(r"^(\s*[-*+]|\s*\d+\.)\s+", response, re.MULTILINE))

        # 3. Schema checks (Code blocks)
        min_code_blocks = int(schema.get("min_code_blocks", 0))  # type: ignore
        if code_block_count < min_code_blocks:
            violations.append(
                f"Too few code blocks (found {code_block_count}, "
                f"expected {min_code_blocks})"
            )

        min_headings = int(schema.get("min_headings", 0))  # type: ignore
        if heading_count < min_headings:
            violations.append(
                f"Too few headings (found {heading_count}, "
                f"expected {min_headings})"
            )

        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "stats": {
                "heading_count": heading_count,
                "code_block_count": code_block_count,
                "list_count": list_count,
            },
        }

    @staticmethod
    def check_heading_hierarchy(response: str) -> List[str]:
        """
        Checks that headings do not skip levels (e.g. H1 to H3).
        """
        violations = []
        headings = re.findall(r"^(#{1,6})\s+(.+)$", response, re.MULTILINE)

        if not headings:
            return []

        prev_level = 0
        for i, (hashes, title) in enumerate(headings):
            level = len(hashes)
            # Check for skipping levels (next level > prev level + 1)
            # Exception: First heading can be H1, H2, etc? usually starts at 1.
            # Allowing start with H1 or H2.

            if i == 0:
                if level > 2:  # warning if starts with H3+
                    pass  # not strictly a hierarchy violation but odd
            else:
                if level > prev_level + 1:
                    violations.append(
                        f"Skipped heading level: H{prev_level} -> H{level} ('{title}')"
                    )

            prev_level = level

        return violations

    @staticmethod
    def count_code_blocks(response: str) -> int:
        """Counts code blocks (```)."""
        # Simple count of opening triple backticks
        # Note: This might overcount if nested or not properly specific, but standard regex
        # for code blocks is roughly ```.*?```
        matches = re.findall(r"```", response)
        # Divide by 2 to get block count? Or just count starts?
        # Usually checking pairs is better.
        # Let's count pairs.
        return len(matches) // 2

    @staticmethod
    def check_required_sections(response: str, doc_type: str) -> List[str]:
        """
        Checks for presence of required sections based on doc_type.
        """
        schema = DOC_TYPE_SCHEMAS.get(doc_type)
        if not schema:
            return []

        required = schema.get("required_sections", [])
        assert isinstance(required, list)
        missing = []

        # Simple case-insensitive check in headings
        headings_text = [
            h.lower() for h in re.findall(r"^#{1,6}\s+(.+)$", response, re.MULTILINE)
        ]

        for req in required:
            # Check if any heading contains the required word
            found = any(req.lower() in h for h in headings_text)
            if not found:
                missing.append(req)

        return missing
