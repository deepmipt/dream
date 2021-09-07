import logging

from dff.core import Context, Actor
from common.utils import is_yes, is_no, get_emotions
from tools.detectors import get_subject, get_age


logger = logging.getLogger(__name__)


def emotion_detected(name="fear", threshold=0.8):
    def emotion_detected_handler(ctx: Context, actor: Actor, *args, **kwargs):
        emotion_probs = get_emotions(ctx.last_request, probs=True)
        return emotion_probs.get(name, 0) > threshold

    return emotion_detected_handler


def covid_facts_exhausted(ctx: Context, actor: Actor, *args, **kwargs):
    # In legacy version of code default value is "True", however
    # function becomes useless with it
    # (see coronavirus_skill.scenario: 375)
    return ctx.misc.get("covid_facts_exhausted", False)


def check_flag(flag: str, default: bool = False):
    def check_flag_handler(ctx: Context, actor: Actor, *args, **kwargs):
        return ctx.misc.get(flag, default)

    return check_flag_handler


def subject_detected(ctx: Context, actor: Actor, *args, **kwargs):
    # In order to increase performance
    # we need to cache value and use it
    # across all condition checks in the same 'turn'.
    # HOWEVER, there is no way to access 'context' object,
    # because it is just deepcopy, but not actual 'context'.
    # MOREOVER, we should to perform subject detection
    # again in 'processing', because we cannot just
    # save detected state into context here.
    subject = get_subject(ctx)

    if subject and subject["type"] != "undetected":
        return True

    return False


def age_detected(ctx: Context, actor: Actor, *args, **kwargs):
    # See note in subject_detected
    age = get_age(ctx)

    if age:
        return True

    return False


