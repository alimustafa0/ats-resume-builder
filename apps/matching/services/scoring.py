"""Deterministic ATS scoring.

Compares a resume's structured skills against a job posting's required and
preferred skills, producing an explainable coverage score and a concrete list
of missing skills. Pure functions, no AI calls -- fast, free, reproducible.
"""

from __future__ import annotations

import re

# Connector words that carry no matching signal.
_STOPWORDS = frozenset(
    {"with", "and", "or", "for", "the", "of", "in", "to", "a", "an", "&"}
)

# Blend weights when a posting lists both kinds of skill.
_REQUIRED_WEIGHT = 0.7
_PREFERRED_WEIGHT = 0.3


def _tokenize(skill: str) -> frozenset[str]:
    """Reduce a skill phrase to a set of comparable tokens.

    Lowercases, keeps alphanumerics plus the symbols that distinguish skills
    like ``c++`` / ``c#`` / ``.net``, splits on everything else, and drops
    connector words.
    """
    tokens = re.findall(r"[a-z0-9.+#]+", skill.lower())
    return frozenset(t for t in tokens if t not in _STOPWORDS)


def _is_covered(
    job_tokens: frozenset[str], resume_token_sets: list[frozenset[str]]
) -> bool:
    """True if a job skill is covered by any resume skill.

    A match holds when one token set is fully contained in the other, so
    "rest api" matches "rest api design" and "python" matches "python
    (primary)", while "java" never matches "javascript".
    """
    if not job_tokens:
        return False
    for resume_tokens in resume_token_sets:
        if resume_tokens and (
            job_tokens <= resume_tokens or resume_tokens <= job_tokens
        ):
            return True
    return False


def _coverage(
    job_skills: list[str], resume_token_sets: list[frozenset[str]]
) -> dict:
    """Split a list of job skills into matched/missing against the resume."""
    matched: list[str] = []
    missing: list[str] = []
    for skill in job_skills:
        if _is_covered(_tokenize(skill), resume_token_sets):
            matched.append(skill)
        else:
            missing.append(skill)

    total = len(job_skills)
    ratio = len(matched) / total if total else None
    return {
        "total": total,
        "matched": matched,
        "missing": missing,
        "coverage": round(ratio, 4) if ratio is not None else None,
    }


def score_resume_against_job(resume_data: dict, job_data: dict) -> dict:
    """Score how well a resume covers a posting's skill requirements.

    Returns an overall 0-100 ``score`` plus per-category (``required`` /
    ``preferred``) coverage with the matched/missing breakdown.
    """
    resume_token_sets = [
        _tokenize(s) for s in resume_data.get("skills", []) if isinstance(s, str)
    ]

    required = _coverage(job_data.get("required_skills", []), resume_token_sets)
    preferred = _coverage(job_data.get("preferred_skills", []), resume_token_sets)

    req_cov = required["coverage"]
    pref_cov = preferred["coverage"]

    if req_cov is not None and pref_cov is not None:
        blended = _REQUIRED_WEIGHT * req_cov + _PREFERRED_WEIGHT * pref_cov
    elif req_cov is not None:
        blended = req_cov
    elif pref_cov is not None:
        blended = pref_cov
    else:
        blended = 0.0

    return {
        "score": round(blended * 100, 1),
        "required": required,
        "preferred": preferred,
    }