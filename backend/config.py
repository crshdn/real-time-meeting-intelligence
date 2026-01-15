"""
Hardcoded MVP configuration for Real-Time Sales Assistant.
In later phases, this will be loaded from playbook.json.
"""

# Product context for Claude system prompt
PRODUCT_CONTEXT = {
    "name": "Acme CRM Pro",
    "description": """Enterprise CRM solution with AI-powered lead scoring,
automated follow-ups, and deep analytics integration. Designed for
mid-market B2B companies with 50-500 employees.""",
    "pricing": [
        {"tier": "Starter", "price": "$50/user/month"},
        {"tier": "Professional", "price": "$100/user/month"},
        {"tier": "Enterprise", "price": "Custom pricing"},
    ],
}

VALUE_PROPOSITIONS = [
    "Reduces manual data entry by 80%",
    "Increases sales team productivity by 35%",
    "Integrates with 200+ tools out of the box",
    "Implementation in under 2 weeks",
    "24/7 customer support included",
]

# Phrases that trigger AI suggestion generation
OBJECTION_TRIGGERS = [
    # Price objections
    "too expensive",
    "over budget",
    "can't afford",
    "too much",
    "cost",
    "price",
    "cheaper",
    # Timing objections
    "not the right time",
    "too busy",
    "next quarter",
    "next year",
    "bad timing",
    # Need to think
    "think about it",
    "get back to you",
    "discuss internally",
    "need time",
    "consider",
    "sleep on it",
    # Competitor
    "already using",
    "have a solution",
    "current provider",
    "competitor",
    "salesforce",
    "hubspot",
    # Authority
    "check with my",
    "need approval",
    "not my decision",
    "talk to my boss",
    "committee",
    # Skepticism
    "not sure",
    "don't see",
    "why would",
    "prove it",
    "not convinced",
]

# Objection categories and recommended responses (for context)
OBJECTION_PLAYBOOK = {
    "price": {
        "triggers": ["too expensive", "over budget", "can't afford", "too much"],
        "responses": [
            "Reframe as ROI: Ask about cost of current manual processes",
            "Offer phased implementation to spread costs",
            "Highlight hidden costs of not switching",
            "Suggest starting with smaller team/tier",
        ],
    },
    "timing": {
        "triggers": ["not the right time", "too busy", "next quarter"],
        "responses": [
            "Ask what would need to change for timing to be right",
            "Offer lighter-touch pilot program",
            "Discuss cost of waiting (competitor advantage)",
            "Schedule follow-up for better timing",
        ],
    },
    "need_to_think": {
        "triggers": ["think about it", "get back to you", "discuss internally"],
        "responses": [
            "Ask what specific concerns need discussion",
            "Offer to join internal meeting to answer questions",
            "Set specific follow-up time before ending call",
            "Provide summary document for internal review",
        ],
    },
    "competitor": {
        "triggers": ["already using", "have a solution", "current provider"],
        "responses": [
            "Ask what they wish was better about current solution",
            "Offer comparison or migration support",
            "Share relevant case study of similar switch",
            "Highlight unique differentiators",
        ],
    },
    "authority": {
        "triggers": ["check with my", "need approval", "not my decision"],
        "responses": [
            "Offer to present to decision-makers directly",
            "Provide materials they can share internally",
            "Ask what would help them champion internally",
            "Identify who else should be in the conversation",
        ],
    },
}

# System prompt template for Claude
SYSTEM_PROMPT_TEMPLATE = """You are a real-time sales assistant helping a salesperson during a live call.

## Your Role
- Provide 2-3 concise response suggestions when the prospect raises objections or asks questions
- Keep suggestions brief (1-2 sentences each) so they can be quickly read
- Focus on overcoming objections and moving the conversation forward
- Match the tone to the conversation (professional but natural)

## Product/Service Context
Product: {product_name}
{product_description}

Pricing:
{pricing_info}

## Key Value Propositions
{value_props}

## Current Conversation
{conversation_transcript}

## Instructions
The prospect just said: "{last_prospect_statement}"

Provide 2-3 response options the salesperson could use. Format as:
1. [Response option 1]
2. [Response option 2]
3. [Response option 3 - optional]

Keep each under 30 words. Focus on the most effective response first."""


def get_system_prompt(conversation_transcript: str, last_statement: str) -> str:
    """Build the complete system prompt with current context."""
    pricing_info = "\n".join(
        [f"- {p['tier']}: {p['price']}" for p in PRODUCT_CONTEXT["pricing"]]
    )
    value_props = "\n".join([f"- {v}" for v in VALUE_PROPOSITIONS])

    return SYSTEM_PROMPT_TEMPLATE.format(
        product_name=PRODUCT_CONTEXT["name"],
        product_description=PRODUCT_CONTEXT["description"],
        pricing_info=pricing_info,
        value_props=value_props,
        conversation_transcript=conversation_transcript,
        last_prospect_statement=last_statement,
    )
