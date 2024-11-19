import logging
import common.dff.integration.context as int_ctx

from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)


def task_processing(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    cap = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("voice_service", {})
        .get("task_id", "")
    )

    status = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("voice_service", {})
        .get("all_status", "")
    )

    error_response = "I couldn't caption the audio in your message, please try again with another file"
    success_response = f"Processing started for audiofile id: {cap}..." + \
        f"\n\n{status}" if status else ""

    rsp = error_response if not cap else success_response

    return rsp