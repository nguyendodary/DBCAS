"""AI #2: strict evidence-based JSON with an explicit deterministic fallback."""
import logging
import math
import re
import time

from .llm.provider import ChatMessage
from .prompt_builder import Evaluation, build_prompt

LOG = logging.getLogger("dbcas.ai")


def validate_evaluation(value, data):
    result = Evaluation.model_validate(value).model_dump()
    expected = {(item["attempt_id"], item["question_id"]): item for item in data.get("items", [])}
    actual = [(item["attempt_id"], item["question_id"]) for item in result["question_comments"]]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise ValueError("evaluation_question_coverage")
    for item in result["question_comments"]:
        evidence = expected[item["attempt_id"], item["question_id"]]
        score = item["essay_score_proposal"]
        if score is not None and (evidence["type"] != "essay" or not math.isfinite(score) or not 0 <= score <= float(evidence["points"])):
            raise ValueError("evaluation_score_range")
    if data.get("attempt_count", 1) < 2 and result["trend"] is not None:
        raise ValueError("evaluation_insufficient_trend")
    for field in ("strengths", "weaknesses", "suggestions", "learning_path"):
        if any(not text.strip() or len(text) > 2000 for text in result[field]):
            raise ValueError("evaluation_text")
    return result


def essay_proposal(item):
    answer = str(item.get("answer") or "").lower().strip()
    reference = str(item.get("reference_answer") or "").lower().strip()
    if not answer:
        return 0.0
    words = set(re.findall(r"\w{3,}", reference))
    coverage = len(words.intersection(re.findall(r"\w{3,}", answer))) / max(1, len(words))
    ratio = 1 if reference and answer == reference else min(.8, .2 + .6 * coverage)
    return round(float(item["points"]) * ratio, 2)


def rule_evaluation(data):
    comments = []
    correct, total = 0, len(data.get("items", []))
    for item in data.get("items", []):
        score = float(item.get("score") or 0)
        full = item.get("score") is not None and score >= float(item["points"])
        correct += full
        essay = item["type"] == "essay"
        comments.append(dict(attempt_id=item["attempt_id"], question_id=item["question_id"],
            comment=("Đã đạt điểm tối đa theo kết quả chấm." if full else
                     "Đối chiếu câu trả lời với đáp án và rubric; luyện lại phần chưa đạt.") +
                    (" Điểm tự luận theo quy tắc chỉ là đề xuất, cần đối chiếu rubric." if essay else ""),
            essay_score_proposal=essay_proposal(item) if essay else None))
    count = data.get("attempt_count", 1)
    trend = None
    history = data.get("history", [])
    if count >= 2:
        first, last = float(history[0].get("percentage", 0)), float(history[-1].get("percentage", 0))
        trend = f"Điểm bài đầu {first:.2f}%, bài gần nhất {last:.2f}% (chênh lệch {last-first:+.2f} điểm phần trăm)."
    result = dict(summary=f"Đã tổng hợp {count} bài. {correct}/{total} câu trong dữ liệu chi tiết đạt điểm tối đa. "
                          "Đánh giá dự phòng theo quy tắc; chưa xác nhận chất lượng bởi mô hình thực.",
        question_comments=comments,
        strengths=[f"Có bằng chứng đạt điểm tối đa ở {correct} câu." if correct else "Đã hoàn thành bài và có dữ liệu để bắt đầu ôn tập."],
        weaknesses=[f"Cần rà soát {total-correct} câu chưa đạt tối đa." if total > correct else "Tiếp tục kiểm tra khả năng vận dụng ở bài khác."],
        suggestions=["Mở từng câu chưa đạt, đối chiếu đáp án và làm lại với dữ liệu khác."],
        learning_path=["Ôn khái niệm có tỷ lệ thấp trong bảng CLO/chủ đề.", "Luyện từ Dễ đến Vừa rồi Khó, sau đó làm bài mới."],
        trend=trend)
    recurring = data.get("recurring_weaknesses", [])
    weak = sorted((item for rows in data.get("dimensions", {}).values() for item in rows if item["percentage"] < 70), key=lambda item: (item["percentage"], item["label"]))
    if recurring:
        result["weaknesses"] = [f"{item['concept']}: chưa đạt điểm tối đa ở {item['attempts']} bài, cần luyện lại." for item in recurring[:8]]
    elif weak:
        result["weaknesses"] = [f"{item['label']}: tỷ lệ điểm {item['percentage']:.2f}%." for item in weak[:8]]
    if weak:
        result["learning_path"] = [f"Bước {i+1}: ôn {item['label']}, làm một bài mới và đối chiếu lỗi còn lặp lại." for i, item in enumerate(weak[:5])]
    return validate_evaluation(result, data)


def evaluate(data, llm=None, *, settings=None, force_fallback=False):
    prompt = build_prompt(data, model_path=getattr(settings, "prompt_builder_model_path", ""),
                          timeout=getattr(settings, "prompt_builder_timeout_seconds", 8))
    started = time.monotonic()
    fallback, status = True, "rules"
    try:
        delay = getattr(settings, "evaluation_fake_delay_seconds", 0)
        if delay and not force_fallback:
            time.sleep(delay)
        if getattr(settings, "evaluation_fake_error", False):
            raise ValueError("fake_provider_error")
        if not force_fallback and llm and llm.is_configured():
            result = llm.generate_structured("attempt_evaluation",
                [ChatMessage("system", "Bạn là Evaluator. Chỉ trả JSON theo schema và bằng chứng."),
                 ChatMessage("user", prompt.prompt)],
                json_schema={"name": "evaluation", "strict": True, "schema": Evaluation.model_json_schema()},
                validator=lambda value: validate_evaluation(value, data), max_tokens=8000)
            result = validate_evaluation(result, data)
            fallback, status = False, "ok"
        else:
            result = rule_evaluation(data)
    except Exception:
        result, status = rule_evaluation(data), "provider_or_validation_failed"
    LOG.info("ai_call role=evaluator hash=%s duration_ms=%d status=%s fallback=%s",
             prompt.prompt_hash, (time.monotonic() - started) * 1000, status, fallback)
    return {"evaluation": result, "prompt_hash": prompt.prompt_hash,
            "builder_fallback": prompt.fallback_used, "evaluator_fallback": fallback}
