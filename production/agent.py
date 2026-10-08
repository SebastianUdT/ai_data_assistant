"""
Production Finance Agent

PURPOSE
-------
Configure the AI agent that can perform customer financial operations.

ARCHITECTURE
------------

Application / Runner
        ↓
trusted AppContext
        ↓
Finance Agent
        ↓
Tool
        ↓
CustomerService
        ↓
CustomerRepository
        ↓
Database


TRUST BOUNDARY
--------------

The model may propose:

    customer_id
    amount

The model does NOT control:

    authenticated user
    permissions
    operation_id
    HITL decision
    business validation
    database transaction


CURRENT MODEL
-------------
ScriptedModel keeps development deterministic and avoids external API
calls while we build the production architecture.
"""

from agents import Agent
from agents.testing import (
    ScriptedModel,
    assistant_message,
    function_call,
)

from production.context import AppContext
from production.tools.customer_tools import (
    apply_customer_credit,
    get_customer_balance,
)


# =====================================================================
# SCRIPTED MODEL
# =====================================================================


model = ScriptedModel(
    [
        [
            function_call(
                "apply_customer_credit",
                {
                    "customer_id": (
                        "customer_001"
                    ),
                    "amount": 500.0,
                },
                call_id="credit_call",
            )
        ],

        [
            assistant_message(
                "The customer credit request "
                "has been processed."
            )
        ],
    ]
)


# =====================================================================
# AGENT
# =====================================================================


finance_agent = Agent[AppContext](
    name="Finance Agent",

    instructions=(
        "Help with customer financial operations. "
        "Use tools for financial information and actions. "
        "Never invent financial values."
    ),

    model=model,

    tools=[
        get_customer_balance,
        apply_customer_credit,
    ],
)