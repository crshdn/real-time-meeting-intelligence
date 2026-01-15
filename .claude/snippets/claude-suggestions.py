# Claude API Suggestion Generator Snippet
# Generate sales response suggestions using Claude

import anthropic
import os
from typing import Optional

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SYSTEM_TEMPLATE = """You are a real-time sales assistant helping a salesperson during a live call.

## Your Role
- Provide 2-3 concise response suggestions when the prospect raises objections or asks questions
- Keep suggestions brief (1-2 sentences each) so they can be quickly read
- Focus on overcoming objections and moving the conversation forward
- Match the tone to the conversation (professional but natural)

## Product/Service Context
{product_description}

## Common Objections & Recommended Responses
{objection_playbook}

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


def generate_suggestions(
    conversation_context: str,
    last_statement: str,
    playbook: dict,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 300
) -> Optional[str]:
    """
    Generate response suggestions using Claude.

    Args:
        conversation_context: Recent conversation transcript
        last_statement: Most recent prospect statement
        playbook: Dict with product, objections, value_props keys
        model: Claude model to use
        max_tokens: Maximum response tokens

    Returns:
        String with numbered suggestions
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = SYSTEM_TEMPLATE.format(
        product_description=playbook.get("product", ""),
        objection_playbook=playbook.get("objections", ""),
        value_props=playbook.get("value_props", ""),
        conversation_transcript=conversation_context,
        last_prospect_statement=last_statement
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": "Generate response suggestions now."}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return None


def parse_suggestions(response: str) -> list[str]:
    """Parse numbered suggestions from Claude response."""
    suggestions = []
    lines = response.strip().split("\n")

    for line in lines:
        line = line.strip()
        # Match lines starting with number and period/parenthesis
        if line and line[0].isdigit() and len(line) > 2:
            # Remove number prefix
            if line[1] in ".)" or (line[1] == " " and line[2] in ".)"):
                suggestion = line.split(" ", 1)[-1].strip()
                # Remove surrounding quotes if present
                if suggestion.startswith('"') and suggestion.endswith('"'):
                    suggestion = suggestion[1:-1]
                suggestions.append(suggestion)

    return suggestions


# Usage example:
if __name__ == "__main__":
    playbook = {
        "product": "Acme CRM Pro - Enterprise CRM with AI-powered lead scoring",
        "objections": """
        - Price: Emphasize ROI and cost savings
        - Timing: Offer phased implementation
        - Competitor: Highlight unique features
        """,
        "value_props": """
        - Reduces manual data entry by 80%
        - Increases sales team productivity by 35%
        - Implementation in under 2 weeks
        """
    }

    context = """
    Salesperson: So as you can see, our AI scoring has helped similar companies increase close rates by 40%.
    Prospect: That sounds impressive, but honestly, it's more than we budgeted for this quarter.
    """

    last_statement = "That sounds impressive, but honestly, it's more than we budgeted for this quarter."

    response = generate_suggestions(context, last_statement, playbook)
    print("Raw response:")
    print(response)
    print("\nParsed suggestions:")
    for i, s in enumerate(parse_suggestions(response), 1):
        print(f"{i}. {s}")
