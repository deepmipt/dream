import logging

from df_engine.core.keywords import TRANSITIONS, RESPONSE, LOCAL, PROCESSING, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.processing as int_prs
import common.dff.integration.condition as int_cnd
import common.set_is_final_answer as is_final_answer

from . import response as loc_rsp
from . import condition as loc_cnd

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

flows = {
    # GLOBAL: {
    #     TRANSITIONS: {
    #         # ("api", "api_usage_approved"): cnd.all(
    #         #     [loc_cnd.is_last_utt_approval, int_cnd.is_yes_vars]
    #         # ),
    #         # ("api", "api_usage_not_approved"): cnd.all(
    #         #     [loc_cnd.is_last_utt_approval, int_cnd.is_no_vars]
    #         # ),
    #         # ("api", "thought_node"): cnd.true(),
    #     }
    # },
    "api": {
        LOCAL: {PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)}},
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {"thought_node": cnd.true()},
        },
        "thought_node": {
            RESPONSE: loc_rsp.thought,
            PROCESSING: {
                "set_is_final_answer_flag": is_final_answer.set_is_final_answer_flag(False)
            },
            TRANSITIONS: {"check_if_needs_details": cnd.true()},
        },
        "check_if_needs_details": {
            RESPONSE: loc_rsp.check_if_needs_details,
            PROCESSING: {
                "set_is_final_answer_flag": is_final_answer.set_is_final_answer_flag(False)
            },
            TRANSITIONS: {
                "clarify_details": loc_cnd.needs_details,
                "api_response_node": cnd.neg(loc_cnd.needs_details)
            },
        },
        "clarify_details": {
            RESPONSE: loc_rsp.clarify_details,
            PROCESSING: {
                "set_is_final_answer_flag": is_final_answer.set_is_final_answer_flag(True)
            },
            TRANSITIONS: {"api_response_node": cnd.true()},
        },
        "api_usage_approved": {
            RESPONSE: loc_rsp.response_with_approved_api,
            PROCESSING: {
                "set_is_final_answer_flag": is_final_answer.set_is_final_answer_flag(True)
            },
            TRANSITIONS: {},
        },
        "api_usage_not_approved": {
            RESPONSE: "Sorry, I'm afraid I don't know what I can do then.",
            PROCESSING: {
                "set_is_final_answer_flag": is_final_answer.set_is_final_answer_flag(True)
            },
            TRANSITIONS: {},
        },
        "api_response_node": {
            RESPONSE: loc_rsp.response_with_chosen_api,
            PROCESSING: {
                "set_is_final_answer_flag": is_final_answer.set_is_final_answer_flag(True)
            },
            TRANSITIONS: {
                "api_usage_approved": cnd.all(
                [loc_cnd.is_last_utt_approval, int_cnd.is_yes_vars]
            ),
                "api_usage_not_approved": cnd.all(
                [loc_cnd.is_last_utt_approval, int_cnd.is_no_vars]
            )
            },
        },
    },
}

actor = Actor(
    flows,
    start_label=("api", "start_node"),
    fallback_node_label=("api", "api_response_node"),
)
