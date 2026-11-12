"""Blueprint gap constructors with pending Vietnamese drafts.

English content is what the bank validates and scores. The Vietnamese draft is
stored only in the pending manifest with ``review_status`` pending_human_review;
the builder never imports it.
"""

from lib import essay, mcq

_VI_LEVELS = (
    ("Incomplete", "Chưa đạt"),
    ("Partial", "Một phần"),
    ("Mostly Complete", "Phần lớn đầy đủ"),
    ("Complete", "Đầy đủ"),
)


def _vi_rubrics(criteria):
    return {
        name: {"label": label, "criteria": text}
        for (name, label), text in zip(_VI_LEVELS, criteria)
    }


def mcq_vi(key, concepts, diff, prompt, options, correct, explanation, refs,
           *, vi_prompt, vi_options, vi_explanation, tags=()):
    item = mcq(key, concepts, diff, prompt, options, correct, explanation, refs,
               tags=tags)
    item["vi_draft"] = {
        "prompt": vi_prompt,
        "explanation": vi_explanation,
        "option_texts": {
            label: text for label, text in zip("ABCD", vi_options)
        },
        "rubrics": {},
    }
    return item


def essay_vi(key, concepts, diff, prompt, reference, explanation, criteria,
             refs, *, vi_prompt, vi_reference, vi_explanation, vi_criteria,
             tags=()):
    item = essay(key, concepts, diff, prompt, reference, explanation, criteria,
                 refs, tags=tags)
    item["vi_draft"] = {
        "prompt": vi_prompt,
        "explanation": vi_explanation,
        "option_texts": {},
        "rubrics": _vi_rubrics(vi_criteria),
    }
    return item
