#!/usr/bin/env python3
"""Automated architectural purity linter for Open Harness Protocol (OHP).

Enforces strict domain-agnostic separation:
1. ZERO domain-specific vocabulary (e.g. trading, finance, USDT, MFE) permitted in core skills/
2. ZERO domain-specific vocabulary in normative sections of RFC standards
3. ZERO domain-specific assumptions in schemas or template configurations
"""

import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Domain tokens that must never leak into generic normative specifications or core skills
FORBIDDEN_DOMAIN_PATTERNS = [
    r"\bmfe\b",
    r"\busdt\b",
    r"\bdrawdown\b",
    r"\bbinance\b",
    r"\bbuy-the-dip\b",
    r"\bexit-quality\b",
    r"\bentry-gate-diagnosis\b",
    r"\bcell\b",
    r"\bcampaign\b",
]

REGEX = re.compile("|".join(FORBIDDEN_DOMAIN_PATTERNS), re.IGNORECASE)


class GenericPurityTests(unittest.TestCase):
    def test_skills_directory_is_100_percent_generic(self):
        """Verify that skills/ contains ZERO domain-specific vocabulary."""
        skills_dir = ROOT / "skills"
        violations = []

        for root, _, files in os.walk(skills_dir):
            for f in files:
                if f.endswith((".md", ".py", ".json", ".yaml", ".sh")):
                    filepath = Path(root) / f
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    for line_no, line in enumerate(content.splitlines(), 1):
                        matches = REGEX.findall(line)
                        if matches:
                            rel_path = filepath.relative_to(ROOT)
                            violations.append(
                                f"{rel_path}:{line_no}: found {matches} -> {line.strip()}"
                            )

        self.assertEqual(
            violations,
            [],
            "Domain leakage detected in core skills:\n" + "\n".join(violations),
        )

    def test_normative_standards_are_domain_agnostic(self):
        """Verify that normative sections of docs/standards/ contain NO domain tokens.

        Domain tokens are only permitted inside explicitly designated non-normative case study sections.
        """
        standards_dir = ROOT / "docs" / "standards"
        violations = []

        for root, _, files in os.walk(standards_dir):
            for f in files:
                if f.endswith((".md", ".json", ".yaml")):
                    filepath = Path(root) / f
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    in_non_normative = False

                    for line_no, line in enumerate(content.splitlines(), 1):
                        # Detect non-normative section headers
                        if re.match(
                            r"^#{1,3}\s+.*Non-Normative\s+Case\s+Study",
                            line,
                            re.IGNORECASE,
                        ):
                            in_non_normative = True
                        elif (
                            re.match(r"^#{1,3}\s+\d+", line) and "non-normative" not in line.lower()
                        ):
                            in_non_normative = False

                        if in_non_normative:
                            continue

                        matches = REGEX.findall(line)
                        if matches:
                            rel_path = filepath.relative_to(ROOT)
                            violations.append(
                                f"{rel_path}:{line_no}: found {matches} -> {line.strip()}"
                            )

        self.assertEqual(
            violations,
            [],
            "Domain leakage detected in normative RFC specifications:\n" + "\n".join(violations),
        )

    def test_starter_templates_are_domain_agnostic(self):
        """Verify starter templates contain only systems engineering metrics."""
        templates_dir = ROOT / "skills" / "loop" / "assets" / "templates"
        violations = []

        for t_file in templates_dir.glob("*"):
            if t_file.is_file():
                content = t_file.read_text(encoding="utf-8", errors="ignore")
                for line_no, line in enumerate(content.splitlines(), 1):
                    matches = REGEX.findall(line)
                    if matches:
                        violations.append(
                            f"{t_file.name}:{line_no}: found {matches} -> {line.strip()}"
                        )

        self.assertEqual(
            violations,
            [],
            "Domain leakage detected in templates:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
