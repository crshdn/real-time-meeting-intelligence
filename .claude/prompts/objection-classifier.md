# Objection Classifier Prompt

Optional prompt for classifying objection types before generating responses.

```
Analyze the following statement from a sales prospect and classify the objection type.

Statement: "{prospect_statement}"

Classify into one of these categories:
- PRICE: Budget, cost, or ROI concerns
- TIMING: Not the right time, too busy, next quarter
- COMPETITOR: Already using another solution
- AUTHORITY: Need to discuss with others, not decision maker
- NEED: Don't see the value, unsure if needed
- TRUST: Concerns about company, product, or claims
- NONE: Not an objection (question, positive signal, or neutral)

Respond with only the category name and a confidence score (0-100).

Example response:
PRICE 85
```

## Usage

Use this for:
- Triggering specific playbook responses
- Analytics on objection frequency
- Customizing response tone based on objection type
