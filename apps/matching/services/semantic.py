"""LLM-based semantic skill matching.

The deterministic scorer matches the resume's skills list against the posting's
skills, so requirements expressed as experience ("3-5 years"), demonstrated
abilities, or anything outside the skills array fall into the gap list. This
layer asks Gemini to judge -- by reasoning over the *whole* resume (summary,
experience, and skills), not vector distance -- which of those the candidate
genuinely demonstrates, then folds the rescues back into the score with each
match labelled exact or semantic.
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


_JUDGE_PROMPT = """You are a precise technical recruiter judging whether a candidate demonstrates specific requirements, based on their full resume.

Candidate's resume:
-----
{resume_profile}
-----

For each requirement below, decide whether the candidate genuinely demonstrates it, based only on the resume above. Apply these principles:
- A specific, named technology is evidence for the broader category it clearly belongs to, and for closely synonymous terms.
- Demonstrated experience counts: a stated number of years, or responsibilities that clearly exercise an ability (e.g. debugging, problem-solving, building applications), can satisfy a requirement even when it is not listed as a discrete skill.
- Count a requirement as covered only when the evidence is clear; never on a weak, generic, or speculative basis. If the resume shows no real evidence, it is not covered.

Requirements to judge:
-----
{skills_to_judge}
-----

Return a verdict for every requirement in the list: the requirement text exactly as given, whether it is covered, and a short reason.
"""


def _resume_profile(resume_data: dict) -> str:
    """Compact text of the resume used to ground semantic judgments."""
    parts: list[str] = []

    summary = str(resume_data.get("summary", "")).strip()
    if summary:
        parts.append("Summary: " + summary)

    skills = [str(s).strip() for s in resume_data.get("skills", []) if str(s).strip()]
    if skills:
        parts.append("Skills: " + ", ".join(skills))

    experience = resume_data.get("experience", []) or []
    if experience:
        parts.append("Experience:")
        for exp in experience:
            title = str(exp.get("job_title", "")).strip()
            company = str(exp.get("company", "")).strip()
            start = str(exp.get("start_date", "")).strip()
            end = str(exp.get("end_date", "")).strip()
            header = " - ".join(b for b in (title, company) if b)
            dates = " to ".join(d for d in (start, end) if d)
            if header:
                parts.append(f"- {header}" + (f" ({dates})" if dates else ""))
            for resp in exp.get("responsibilities", []):
                text = str(resp).strip()
                if text:
                    parts.append(f"    * {text}")

    return "\n".join(parts)


def judge_missing_skills(resume_profile: str, skills_to_judge: list[str]) -> dict[str, str]:
    """Ask the LLM which of `skills_to_judge` the resume demonstrates.

    `resume_profile` is the compact resume text from `_resume_profile`. Returns
    {requirement: reason} (keyed by the original string) for those judged
    covered. Raises AIClientError on API or parsing failure.
    """
    if not skills_to_judge:
        return {}

    prompt = _JUDGE_PROMPT.format(
        resume_profile=resume_profile,
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
            matched.append({"skill": skill, "via": "semantic", "reason": covered[skill]})
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
    profile = _resume_profile(resume_data)
    covered = judge_missing_skills(profile, missing)

    required = _rebuild_category(base["required"], covered)
    preferred = _rebuild_category(base["preferred"], covered)

    return {
        "score": round(blended_score(required["coverage"], preferred["coverage"]) * 100, 1),
        "required": required,
        "preferred": preferred,
    }