"""FastAPI route handlers for the moderation engine."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from classifiers import classify_image, classify_text, decode_image, detect_deepfake_suspect
from gdpr import log_moderation_event
from models import (
    ImageRequest,
    ModerationResult,
    ModerationScores,
    TextRequest,
    VideoRequest,
)
from verdict import decide

logger = structlog.get_logger()
router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: build score dict for audit logging
# ---------------------------------------------------------------------------


def _score_dict(scores: ModerationScores) -> dict[str, float]:
    return {
        "violence": scores.violence,
        "sexual_violence": scores.sexual_violence,
        "nsfw": scores.nsfw,
        "deepfake_suspect": scores.deepfake_suspect,
        "cyberbullying": scores.cyberbullying,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/moderate_text", response_model=ModerationResult)
async def moderate_text(
    request: Request, req: TextRequest, background_tasks: BackgroundTasks
) -> ModerationResult:
    """Classify plain text and return a moderation verdict."""
    from i18n.detector import detect_language

    lang_code = req.language or detect_language(req.text)
    text_scores = classify_text(req.text, lang_code)

    scores = ModerationScores(
        violence=text_scores["violence"],
        sexual_violence=text_scores["sexual_violence"],
        nsfw=text_scores["nsfw"],
        deepfake_suspect=0.0,
        cyberbullying=text_scores.get("cyberbullying", 0.0),
    )
    result = decide(scores)
    result = result.model_copy(update={"language": lang_code})
    logger.info(
        "text_moderation",
        verdict=result.verdict,
        reasons=result.reasons,
        language=lang_code,
        text_preview=req.text[:80],
    )

    if req.user_id or req.group_id:
        background_tasks.add_task(
            log_moderation_event,
            req.platform,
            req.user_id,
            req.group_id,
            "text",
            result.verdict,
            result.reasons,
            _score_dict(scores),
            lang_code,
        )

    return result


@router.post("/moderate_image", response_model=ModerationResult)
async def moderate_image(
    request: Request, req: ImageRequest, background_tasks: BackgroundTasks
) -> ModerationResult:
    """Classify an image and return a moderation verdict."""
    image = decode_image(req.image_base64, req.image_url)
    if image is None:
        raise HTTPException(status_code=400, detail="Provide image_base64 or image_url")

    img_scores = classify_image(image)
    deepfake_score = detect_deepfake_suspect(image)

    scores = ModerationScores(
        violence=img_scores["violence"],
        sexual_violence=img_scores["sexual_violence"],
        nsfw=img_scores["nsfw"],
        deepfake_suspect=deepfake_score,
        cyberbullying=0.0,
    )
    result = decide(scores)
    logger.info(
        "image_moderation",
        verdict=result.verdict,
        reasons=result.reasons,
    )

    if req.user_id or req.group_id:
        background_tasks.add_task(
            log_moderation_event,
            req.platform,
            req.user_id,
            req.group_id,
            "image",
            result.verdict,
            result.reasons,
            _score_dict(scores),
            None,
        )

    return result


@router.post("/moderate_video", response_model=ModerationResult)
async def moderate_video(
    request: Request, req: VideoRequest, background_tasks: BackgroundTasks
) -> ModerationResult:
    """Classify a video by sampling frames.

    TODO: Implement proper frame extraction (e.g. via OpenCV or decord).
    Current implementation: returns a stub "allow" result so the endpoint is
    wired and ready for real video analysis.
    """
    if not req.video_base64 and not req.video_url:
        raise HTTPException(status_code=400, detail="Provide video_base64 or video_url")

    # TODO: Extract key frames, run classify_image + detect_deepfake_suspect
    # on each frame, and aggregate scores.
    scores = ModerationScores(
        violence=0.0,
        sexual_violence=0.0,
        nsfw=0.0,
        deepfake_suspect=0.0,
        cyberbullying=0.0,
    )
    result = decide(scores)
    logger.info(
        "video_moderation",
        verdict=result.verdict,
        reasons=result.reasons,
        note="stub – frame extraction not yet implemented",
    )

    if req.user_id or req.group_id:
        background_tasks.add_task(
            log_moderation_event,
            req.platform,
            req.user_id,
            req.group_id,
            "video",
            result.verdict,
            result.reasons,
            _score_dict(scores),
            None,
        )

    return result
