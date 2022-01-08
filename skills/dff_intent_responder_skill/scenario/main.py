import logging

import df_engine.conditions as cnd
from df_engine.core import Actor
from df_engine.core.keywords import GLOBAL, LOCAL, PROCESSING, RESPONSE, TRANSITIONS

import scenario.response as rsp
import scenario.condition as loc_cnd
import common.dff.integration.processing as int_prs

logger = logging.getLogger(__name__)

ZERO_CONFIDENCE = 0.0

flows = {
    "service": {
        "start": {RESPONSE: ""},
        "fallback": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
    },
    GLOBAL: {
        TRANSITIONS: {("context_driven_response", "intent_catcher"): loc_cnd.intent_catcher_exists_condition},
    },
    "context_driven_response": {
        "intent_catcher": {RESPONSE: rsp.intent_catcher_response},
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
