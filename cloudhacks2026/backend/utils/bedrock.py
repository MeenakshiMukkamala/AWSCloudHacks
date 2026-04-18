import boto3
import json

bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")

MODEL_ID = "us.amazon.nova-pro-v1:0"

def call_bedrock(prompt):
    body = {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ]
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"]

if __name__ == "__main__":
    print(call_bedrock("Suggest a recipe using apple and milk"))