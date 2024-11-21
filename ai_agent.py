# ai_agent.py

import boto3
import json
import os
from dotenv import load_dotenv
from botocore.config import Config
import time

def ai_agent_clean(prompt, retries=3, delay=5):
    """
    Cleans the provided text using Amazon Bedrock's Claude model.

    Parameters:
        prompt (str): The raw text to be cleaned.
        retries (int): Number of retry attempts in case of failure.
        delay (int): Delay between retries in seconds.

    Returns:
        str: The cleaned text or an error message.
    """
    # Load environment variables
    load_dotenv()

    # Configure the boto3 client with increased timeout settings
    custom_config = Config(
        connect_timeout=60,  # Connection timeout in seconds
        read_timeout=120     # Read timeout in seconds
    )

    # Set up Amazon Bedrock client with custom config
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        config=custom_config  # Apply the custom timeout settings
    )

    # Configure the model
    # model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
    # model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    model_id = 'anthropic.claude-3-haiku-20240307-v1:0'


    # Define the system prompt
    system_prompt = """
    אתה אפליקציית תמלול מקצועית. קיבלת קטע טקסט ותפקידך לבצע את המשימות הבאות:

    ניקוי שגיאות: נקה את הטקסט משגיאות כתיב, טעויות דקדוקיות ומילים חוזרות. ודא שהמשפטים זורמים בצורה טבעית.
    הוספת סימני פיסוק: הוסף סימני פיסוק מתאימים (כגון פסיקים, נקודות, סימני שאלה וקריאה) בכל מקום שנדרש, על מנת לשפר את הקריאות.
    המרת מספרים ותאריכים: המרה של מספרים (למשל, "שמונה" ל-8), תאריכים (למשל, "חמישה בספטמבר אלפיים עשרים ושלוש" ל-5.9.2023), וזמנים (למשל, "שתיים וחצי" ל-2:30), אם ישנם כאלו בטקסט.
    דוגמה: טקסט קלט: "היום יש לי פגישה בשעה שתיים וחצי אחרי הצהריים. אני מקווה שהיא תסתיים עד ארבע וחצי." תוצאה מבוקשת: "היום יש לי פגישה בשעה 2:30 אחרי הצהריים. אני מקווה שהיא תסתיים עד 4:30."
    
    תרשום ישירות את הטקסט המתוקן ואל תרשום לי כל פעם שאתה משנה משהו
    
    """

    # Prepare the request body
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": system_prompt + "\n" + prompt}]
            }
        ],
    }

    # Invoke the model with retry logic
    for attempt in range(1, retries + 1):
        try:
            response = bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
            )

            # Parse the response
            result = json.loads(response["body"].read())

            # Extract and return the content
            return result['content'][0]['text']

        except Exception as e:
            if attempt < retries:
                print(f"Attempt {attempt} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return f"An error occurred after {retries} attempts: {str(e)}"

def ai_agent_summary(prompt, retries=3, delay=5):
    """
    Summarizes the provided text using Amazon Bedrock's Claude model.

    Parameters:
        prompt (str): The text to be summarized.
        retries (int): Number of retry attempts in case of failure.
        delay (int): Delay between retries in seconds.

    Returns:
        str: The summary text or an error message.
    """
    # Load environment variables
    load_dotenv()

    # Configure the boto3 client with increased timeout settings
    custom_config = Config(
        connect_timeout=60,  # Connection timeout in seconds
        read_timeout=120     # Read timeout in seconds
    )

    # Set up Amazon Bedrock client with custom config
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        config=custom_config  # Apply the custom timeout settings
    )

    # Configure the model
    model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

    # Define the system prompt
    system_prompt = """
    תסכם את התמלול של הדו-שיח הרפואי
    הסיכום שלך צריך להתחלק לשלושה חלקים:
    תלונה עיקרית
    היסטוריה רפואית ותלונות החולה
    תוכנית טיפול והמלצות
    """

    # Prepare the request body
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": system_prompt + "\n" + prompt}]
            }
        ],
    }

    # Invoke the model with retry logic
    for attempt in range(1, retries + 1):
        try:
            response = bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
            )

            # Parse the response
            result = json.loads(response["body"].read())

            # Extract and return the content
            return result['content'][0]['text']

        except Exception as e:
            if attempt < retries:
                print(f"Attempt {attempt} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return f"An error occurred after {retries} attempts: {str(e)}"
