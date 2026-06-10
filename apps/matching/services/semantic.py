"""LLM-based semantic skill matching.

The deterministic scorer leaves skills in the gap list when they don't match
lexically. This layer asks Gemini to judge -- by reasoning, not vector
distance -- which of those genuinely reflect the candidate's experience (e.g.
LLaMA/Groq experience covering "LLMs"), then folds the rescues back into the
score with each match labelled exact or semantic.
"""

from __future__ import annotations

import json

from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from apps.core.services.ai_client import AIClientError, generate_text
from apps.matching.services.scoring import blended_score, score_resume_against_job


class _SkillVerdict(BaseModel):
    skill: str
    covered: bool
    reason: str = ""


class _Verdicts(BaseModel):
    verdicts: list[_SkillVerdict] = Field(default_factory=list)


_JUDGE_PROMPT = """You are a precise technical recruiter judging whether a candidate demonstrates specific skills.

The candidate lists these skills:
-----
{resume_skills}
-----

For each skill below, decide whether the candidate genuinely demonstrates it, based only on the skills above. Apply these principles:
- A specific, named technology is evidence for the broader category it clearly belongs to, and for closely synonymous terms.
- Count a skill as covered only when the evidence is clear; never on a weak, generic, or speculative basis.

Skills to judge:
-----
{skills_to_judge}
-----

Return a verdict for every skill in the list: the skill name exactly as given, whether it is covered, and a short reason.
"""


def judge_missing_skills(
    resume_skills: list[str], skills_to_judge: list[str]
) -> dict[str, str]:
    """Ask the LLM which of `skills_to_judge` the resume demonstrates.

    Returns {skill: reason} (keyed by the original skill string) for those
    judged covered. Raises AIClientError on API or parsing failure.
    """
    if not skills_to_judge:
        return {}

    prompt = _JUDGE_PROMPT.format(
        resume_skills=", ".join(resume_skills),
        skills_to_judge="\n".join(f"- {s}" for s in skills_to_judge),
    )
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=_Verdicts,
        temperature=0,
    )

    raw_json = generate_text(prompt, config=config)

    try:
        parsed = _Verdicts.model_validate_json(raw_json)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise AIClientError(f"Gemini returned malformed verdicts: {exc}") from exc

    by_key = {skill.lower().strip(): skill for skill in skills_to_judge}
    covered: dict[str, str] = {}
    for verdict in parsed.verdicts:
        key = verdict.skill.lower().strip()
        if verdict.covered and key in by_key:
            covered[by_key[key]] = verdict.reason
    return covered


def _rebuild_category(category: dict, covered: dict[str, str]) -> dict:
    """Move semantically-covered skills from missing into matched, labelled."""
    matched = [{"skill": s, "via": "exact"} for s in category["matched"]]
    still_missing: list[str] = []
    for skill in category["missing"]:
        if skill in covered:
            matched.append(
                {"skill": skill, "via": "semantic", "reason": covered[skill]}
            )
        else:
            still_missing.append(skill)

    total = category["total"]
    coverage = round(len(matched) / total, 4) if total else None
    return {
        "total": total,
        "matched": matched,
        "missing": still_missing,
        "coverage": coverage,
    }


def score_resume_against_job_semantic(resume_data: dict, job_data: dict) -> dict:
    """Score with a deterministic pass plus an LLM semantic rescue of gaps.

    Same shape as the deterministic scorer, but each matched skill is labelled
    ``via`` exact or semantic (semantic ones carry a ``reason``), and the score
    reflects the rescued matches.
    """
    base = score_resume_against_job(resume_data, job_data)

    missing = list(
        dict.fromkeys(base["required"]["missing"] + base["preferred"]["missing"])
    )
    resume_skills = [s for s in resume_data.get("skills", []) if isinstance(s, str)]
    covered = judge_missing_skills(resume_skills, missing)

    required = _rebuild_category(base["required"], covered)
    preferred = _rebuild_category(base["preferred"], covered)

    return {
        "score": round(blended_score(required["coverage"], preferred["coverage"]) * 100, 1),
        "required": required,
        "preferred": preferred,
    }