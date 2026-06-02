import os
from flask import Flask, request, abort
from google import genai
from google.genai import types
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

import os

# 這是完全正確且安全的版本！
LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

line_config = Configuration(access_token=LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# 初始化 Gemini Client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- 核心邏輯：判斷訊息並選擇提示詞 ---
def get_prompt_and_respond(user_message: str) -> str:
    """
    根據使用者的訊息內容，選擇不同的 System Prompt，並送交 Gemini 處理
    """
    # 預設的系統提示詞（萬用助理）
    system_instruction = "你是一個親切且專業的繁體中文 AI 助理，請簡短且清晰地回答使用者的問題。"

    # 條件判斷範例 1：如果使用者問到減肥、運動、健康
    if any(keyword in user_message for keyword in ["減肥", "瘦身", "運動", "健身", "卡路里"]):
        system_instruction = (
            "你是一位專業的健身教練與營養師。請針對使用者的健康或減肥問題，"
            "給予鼓勵、並提供具體、好執行的運動或飲食建議。請用積極有活力的口吻回答。"
        )
    
    # 條件判斷範例 2：如果使用者問到程式、Code、Bug
    elif any(keyword in user_message.lower() for keyword in ["寫程式", "code", "bug", "報錯", "python"]):
        system_instruction = (
            "你是一位資深的軟體工程師。請用條理清晰、邏輯嚴謹的方式回答程式問題，"
            "如果有程式碼範例，請確保加上註解，並指出可能需要注意的地方。"
        )

    # 條件判斷範例 3：如果使用者心情不好、很累
    elif any(keyword in user_message for keyword in ["好累", "傷心", "難過", "壓力大", "煩"]):
        system_instruction = (
            "你是一位溫柔、充滿同理心的心理諮商師。請先好好安慰並同理使用者的情緒，"
            "給予溫暖的擁抱與正向引導，講話不要太官方，要像朋友一樣。"
        )

    try:
        # 打包傳送給 Gemini (使用推薦的 gemini-2.5-flash 模型)
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        return response.text
    except Exception as e:
        print(f"Gemini API 發生錯誤: {e}")
        return "對不起，我剛剛大腦稍微斷線了，請再試一次！"

# --- LINE Webhook 接收端點 ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# --- 處理 LINE 文字訊息 ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    
    # 1. 判斷訊息、套用 Prompt、並送去給 Gemini 拿到回覆
    ai_reply = get_prompt_and_respond(user_message)

    # 2. 將結果回傳給 LINE 使用者
    with ApiClient(line_config) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_reply)]
            )
        )

if __name__ == "__main__":
    # 本地測試使用 5000 埠
    app.run(port=5000)
