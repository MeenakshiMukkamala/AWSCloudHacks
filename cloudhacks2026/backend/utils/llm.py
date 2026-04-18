from app.utils.bedrock import call_bedrock

def generate_meals(ingredients):
    prompt = f"""
You are a sustainability-focused cooking assistant.

Given these ingredients:
{ingredients}

Generate 2 simple meals that:
- prioritize ingredients that will spoil soon
- minimize food waste
- use common household items

Return JSON:
[
  {{
    "name": "...",
    "ingredients_used": [...],
    "reason": "..."
  }}
]
"""

    response = call_bedrock(prompt)

    try:
        import json
        return json.loads(response)
    except:
        return [{"name": "Fallback Meal", "ingredients_used": ingredients}]
        
def preservation_advice(ingredient):
    prompt = f"""
This ingredient is about to spoil: {ingredient}.

Give:
- 1 quick way to cook it today
- 1 way to preserve it (freeze, pickle, etc.)

Keep it short.
"""

    return call_bedrock(prompt)