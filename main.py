import os
import json
import re
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

# 環境變數設定
LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

line_config = Configuration(access_token=LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# 初始化 Gemini Client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- 🎯 記憶體優化版保險箱：極低資源讀寫，徹底防禦 OOM ---
VERIFIED_USERS_FILE = "verified_users.txt"

def is_user_verified(user_id: str) -> bool:
    """流式讀取檢查，讀一行釋放一行，絕不佔用記憶體"""
    if not os.path.exists(VERIFIED_USERS_FILE):
        return False
    with open(VERIFIED_USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == user_id:
                return True
    return False

def verify_user(user_id: str):
    """安全追加寫入"""
    with open(VERIFIED_USERS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id}\n")

# --- 🧠 核心邏輯：驗證關卡與 AI 大腦 ---
def get_prompt_and_respond(user_id: str, user_message: str) -> str:
    cleaned_msg = user_message.strip().replace(" ", "").replace("，", "").replace(",", "")
    cleaned_msg_upper = user_message.strip().upper()

    # 檢查是否已經開通權限
    already_verified = is_user_verified(user_id)

    # ==========================================================
    # 🔒 關卡防禦階段：尚未驗證的人，必須輸入名字與推薦人
    # ==========================================================
    if not already_verified:
        has_name = any(k in cleaned_msg for k in ["我是", "名字", "姓名", "叫我", "我是：", "名字："]) or len(cleaned_msg) >= 4
        has_referrer = any(k in cleaned_msg for k in ["推薦人", "介紹人", "推薦", "老大是", "推薦："])

        if has_name and has_referrer:
            verify_user(user_id)
            return (
                "🎉 【系統認證成功！】\n\n"
                "夥伴你好！資料已安全對接。歡迎加入肆伍參團隊通路裂變系統！\n"
                "我是【金牌教練＿肆伍參平哥】的 AI 特助。從現在開始，你可以隨時跟我諮詢組織運作的心態、方法與技巧。\n\n"
                "===SPLIT==="
                "💡 夢想啟航第一步：現在請直接輸入【90天新人加速器】，立刻解鎖平哥為你量身打造的起盤藍圖，我們一起創造倍增果實！"
            )
        else:
            return (
                "👋 你好！歡迎來到【金牌教練＿肆伍參平哥】的 AI 戰將特助系統！\n\n"
                "平哥常說：『做大事業，靠的是簡單、正直、可複製的系統。』為了保護肆伍參團隊的核心通路資產，並避免系統被外部濫用，本機器人已啟動安全防護機制。\n\n"
                "🔒 【通關驗證】\n"
                "請在下方直接回覆輸入：\n"
                "1. 您的名字\n"
                "2. 您的直屬推薦人是誰\n\n"
                "📝 範例輸入：『我是陳大文，推薦人是平哥』\n"
                "完成正確資料對接後，系統將自動為您開通完整的使用權限！"
            )

    # ==========================================================
    # 🎯 系統直回：【90天新人加速器】起盤藍圖
    # ==========================================================
    if cleaned_msg_upper in ["90天新人加速器", "90天新人加速器計畫", "起盤藍圖"]:
        return (
            "肆伍參團隊專屬加速器！本系統專為管理 200 人以上團隊自轉設計。請嚴格執行每週必修與考核：\n\n"
            "🎯 第一階段：【第1月·建立信任池（有人）】\n"
            "💡 核心：累積 30-100 個願意聽你說話的人。不提產品名。\n"
            "👉 輸入【第1月】解鎖第 1-4 週詳細主題與必修任務。\n\n"
            "===SPLIT==="
            "🎯 第二階段：【第2月·建立成交模型（會賣）】\n"
            "💡 核心：將會聊的人變成下單 90 定期健康滿意保證計畫的人。\n"
            "👉 輸入【第2月】解鎖第 5-8 週詳細主題與必修任務。\n\n"
            "🎯 第三階段：【第3月·建立複製系統（會長）】\n"
            "💡 核心：不是你在賣，是別人在賣。分層管理 200 人自轉大盤。\n"
            "👉 輸入【第3月】解鎖第 9-12 週詳細主題與必修任務。"
        )

    # 🟢 第一階段：第 1 ~ 4 週
    elif cleaned_msg_upper in ["第1月", "第一月"]:
        return "📈 【🟢 第一階段：第1月·建立信任池 任務大盤】\n\n請輸入對應週次查看「每週必修任務」與「小型通關考核」：\n\n👉 輸入【W1】：解鎖第 1 週【定心定位破冰】\n👉 輸入【W2】：解鎖第 2 週【光波學堂與陌生引流】\n👉 輸入【W3】：解鎖第 3 週【一頁式網頁培訓】\n👉 輸入【W4】：解鎖第 4 週【OPP借力與總結大考】\n\n⚠️ 紀律防線：本月【每週必修】主動諮詢直屬教練，並帶對話截圖進行覆盤！"
    elif cleaned_msg_upper == "W1":
        return "🎯 【第 1 週主題：盲測破冰與熟人盤點】\n\n📚 【本週必修課】\n1. 【定心 定位 定方向】訓練：確立創業者心態，你是挑選科學樣本的觀察家，不是求人買東西的業務。\n2. 【每週主動諮詢直屬教練】：週底主動找教練覆盤破冰對話。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 盤點熟人、舊同事名單，每天新增 3-5 個對話。\n- 核心破冰話術：「我最近在做一個健康狀態觀察實驗，不是銷售，你要不要當我一個測試樣本？」\n\n🏆 小型通關考核\n成功導流 5 位受測者進入【官方 LINE①】填寫健康問卷。未達標者留級重修基礎對話！"
    elif cleaned_msg_upper == "W2":
        return "🎯 【第 2 週主題：Threads 懸念與盲測期控盤】\n\n📚 【本週必修會議】\n1. 參加【月初·光波小學堂】：熟練產品基礎物理原理，奠定專業底氣。\n2. 參加【每週·地區夜訓】：肉身進場，帶動體感種子名單感受系統大盤氛圍。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 每天發表 1 則 Threads 體驗型懸念內容（如：「第 3 天，有人回饋睡眠變穩，但我還在觀察，不下結論」）。\n- 建立 3-10 人小體驗群，每天晚上在群裡發佈官方打卡密碼（如：啟動訊號）。\n\n🏆 小型通關考核\n陌生引流 3 人進 LINE① 填問卷，且小體驗群前 5 天打卡率維持在 70% 以上！"
    elif cleaned_msg_upper == "W3":
        return "🎯 【第 3 週主題：一頁式工具演練與名單黏著】\n\n📚 【本週必修課】\n1. 【一頁式網頁說明能力培訓】：練熟如何用一頁式網頁工具，跟受測者優雅、專業地展示實驗科學邏輯與 90 天健康滿意保證。\n2. 【每週主動諮詢直屬教練】：向直屬教練演示自己講一頁式網頁的流暢度。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 嚴格執行 321 紀律（3 個新對話、2 則懸念內容、1 個問卷導流），維持小體驗群每日打卡黏著度。\n\n🏆 小型通關考核\n能對著直屬教練流暢、完整地完成一次「一頁式網頁」導覽演示考核。"
    elif cleaned_msg_upper == "W4":
        return "🎯 【第 4 週主題：首期結案與商機鋪墊】\n\n📚 【本週必修會議】\n1. 帶領有體感或想了解事業的受測者，全面參與【商機 OPP 說明會】，借大場的力量幫新人收單、看懂藍海趨勢。\n2. 【每週主動諮詢直屬教練】：核對第一個月總結指標。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 引導 Day 7 受測者輸入「資產報告」結案，並順理成章推動 Day 8-14 的科技解密（發放光波科技、大衛博士等密碼）。\n\n🏆 第一月最終總結大考\n1. LINE① 訊息池累積 30-100 人。\n2. 本月底成功晉升「經理」階層，拿到下個月【經理一日培訓】入場券！"

    # 🟡 第二階段：第 5 ~ 8 週
    elif cleaned_msg_upper in ["第2月", "第二月"]:
        return "💰 【🟡 第二階段：第2月·建立成交模型 任務大盤】\n\n請輸入對應週次查看必修與考核：\n\n👉 輸入【W5】：解鎖第 5 週【邀約培訓與OPP借力】\n👉 輸入【W6】：解鎖第 6 週【ABC法則與經理培訓】\n👉 輸入【W7】：解鎖第 7 週【締結保證與下單閉環】\n👉 輸入【W8】：解鎖第 8 週【中盤收網與事業轉化】\n\n⚠️ 核心三不鐵律：不講療效、不講保證、不講科學辯論！"
    elif cleaned_msg_upper == "W5":
        return "🎯 【第 5 週主題：三句成交與高能邀約】\n\n📚 【本週必修課】\n1. 【邀約培訓】：學習如何將 14 天解密結束、開始好奇的受測者，「邀約」進線上分享會或實體商機 OPP。\n2. 【每週主動諮詢直屬教練】：拿著沒邀約成功的名單，找教練覆盤語氣與關鍵字。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 每天 2 個成交對話，嚴格執行流程：破冰 ➡️ 框架 ➡️ 體驗 ➡️ 安排。對話死守核心三句：「不用相信」、「你只要試」、「身體會告訴你」。\n\n🏆 小型通關考核\n本週成功邀約至少 3 位觀望名單進入每週線上分享群或實體 OPP 大場。"
    elif cleaned_msg_upper == "W6":
        return "🎯 【第 6 週主題：黃金 ABC 法則實戰】\n\n📚 【本週必修會議與課】\n1. 【ABC 法則培訓】：練熟如何當一個完美的「B 角色」（推崇 A 教練、安撫 C 客戶）。在實體夜訓或三方群裡借教練力量收單。\n2. 參加【每月·經理一日培訓】：與核心領導階層對齊，學習中盤控兵技術。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 利用實體【地區夜訓】或線上三方群，實戰推崇推薦人，進行 ABC 借力收單。\n\n🏆 小型通關考核\n與教練配合，在實戰中完成一次無瑕疵的 ABC 借力實演（包含事前推崇與現場座位/秩序維護）。"
    elif cleaned_msg_upper == "W7":
        return "🎯 【第 7 週主題：締結保證與下單閉環】\n\n📚 【本週必修課】\n1. 【締結保證培訓】：練熟官方「90 天健康滿意保證、不滿意隨時退、零風險」的臨門一腳話術，用公司退費保障擊碎客戶最後的猶豫。\n2. 【每週主動諮詢直屬教練】：逐一核對手上正在經歷 90 天計畫的客戶體感進度。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 引導有意願的客戶點擊官方連結，自行下單完成 90 天健康滿意保證計畫。寄送的體驗組件內必須置入「實驗歡迎函」創造開箱儀式感。\n\n🏆 小型通關考核\n本週內必須成功創造 2 筆綁定「90天健康滿意保證」的真實體驗下單。"
    elif cleaned_msg_upper == "W8":
        return "🎯 【第 8 週主題：中盤收網與事業轉化】\n\n📚 【本週必修會議】\n1. 全面兵臨【每週·地區夜訓】：帶領你手頭所有下單滿一個月的優質愛用者進場感受組織能量。\n2. 【每週主動諮詢直屬教練】：由教練協助你從現有客戶中，篩選出可以轉化為事業夥伴的 20 人種子名單。\n\n===SPLIT===\n🔥 每日行動 SOP\n- 拋出第 14 天的商業彩蛋對接話術：「你用得這麼好，有沒有看懂這個全球獨家專利、無法被複製的藍海市場？想了解如何邊用邊建立被動收入嗎？」\n\n🏆 第二月最終總結大考\n達到每週穩定 5-15 個體驗者，轉換率達 20-40%，且團隊中出現第一批跟隨你經營的種子。"

    # 🔵 第三階段：第 9 ~ 12 週
    elif cleaned_msg_upper in ["第3月", "第三月"]:
        return "🌱 【🔵 第三階段：第3月·建立複製系統 任務大盤】\n\n請輸入對應週次查看必修與考核：\n\n👉 輸入【W9】：解鎖第 9 週【20人核心群與帶隊諮詢】\n👉 輸入【W10】：解鎖第 10 週【新人手冊推行與大場借力】\n👉 輸入【W11】：解鎖第 11 週【複製會議主持與董事培訓】\n👉 輸入【W12】：解鎖第 12 週【大盤終極驗收與系統自轉】\n\n⚠️ 領袖鐵律：不是你在賣，是別人在賣！全面推行標準化工具帶人。"

    # ==========================================================
    # 🧠 AI 運作端：平哥自訂完全體全新大腦提示詞
    # ==========================================================
    system_instruction = """
你現在是【金牌教練＿肆伍參平哥】的專屬 AI 特助（戰將複製系統）。
平哥是擁有 20 年資深通路高手實戰經驗、帶領 200 人團隊的高階商業領袖。
你的任務：引導新人「三個月內晉升一星董事」，進入平哥的核心決策圈！

【⚠️ 精簡、清晰分段防重複條款（最高級指令）】
1. 為了在 LINE 上讓夥伴好閱讀，當你要回答包含多個概念的長篇問題時，請務必主動在每個大觀念之間加入 "===SPLIT===" 標記，以便系統自動幫你「切片成多則訊息」發送！

2. 強調「高價值資訊分享」與「系統化複製（90天新人加速器）」，反對低價推銷與試用測試。
3. 始終貫徹平哥的核心精神：「只要每天進步一點點，不久的將來一定有甜美的果實！」

【說話風格與領袖人格】
- 充滿熱情、正向、極具感染力。講話絕不官腔，要像個有智慧、有格局的兄長。
- 條理清晰、切中要害，適時給予夥伴高格局的激勵與信心。
- 一律使用繁體中文回覆。

【核心商務思維：複製倍增、通路裂變與Threads經營】
- 當夥伴詢問如何成長、帶團隊、或進行 Threads 社群商務經營時，請用「組織複製與系統化建立」的思維引導。
- 灌輸夥伴「複製倍增」與「通路裂變」的驚人威力，讓他們明白真正頂尖的通路高手做大事業，靠的是「簡單、易學、可複製」的自轉系統。

【🎯 2.0 核心通路獎金制度導引（一次只專注回答一個卡點，絕不連篇大論）】

1. 銷售獎金模組（建立信任池的獲利）：
   - 零售獎金：從複製網站引導客戶購買，現賺每包 $50 美元的通路零售利潤。
   - 客戶介紹金：連續 31 天親推客戶積分達標（300分得5%、600分得10%、1200分得20%），當週客戶消費立刻享受高趴數加碼！這不是求人買，是靠高價值健康分享吸引。

2. 代數購貨獎金（通路裂變的被動開端）：
   - 獎勵培育與團隊傳承，最高可拿三代深度夥伴與客戶購貨 BV 積分的固定百分比（第一代 7%、第二代 5%、第三代 1%）。
   - 當週自己須達 55PV 活躍，下線 0PV自動壓縮，這是不需靠個人零售的自動化大盤自轉收益。

3. 快速啟動獎金（前 9 週的黃金加速器）：
   - 專為配合「90天新人加速器」設計。前 9 週新夥伴實付一星經理週週加薪 $25 美元，實付二星經理或以上週週拿 $50 美元（前兩個月封頂 $450 美元）！
   - 直屬教練只要位階不低於新夥伴，週週同享 50% 的推薦人輔導獎金（$12.50 或 $25 美元），帶動團隊共贏狼性。

4. 晉升【二星經理】條件（解鎖中盤控兵技術）：
   - 個人積分達 110 PV，且連續 31 天內親推線總積分（QDV）達到 1,500 分。
   - 這是解鎖第二代 3% 代數獎金與快速啟動每週 $50 美元頂格回饋的黃金起步點。

5. 晉升【一星董事】範圍內獎金（三個月建廠插旗爆發期）：
   - 告訴新人：晉升一星董事代表左右兩邊核心組織穩固，將在這個位階一次拿滿六大管道全方位獎金：
     ① 銷售：每包 $50 美元零售利潤與最高 20% 客戶介紹金。
     ② PIB推薦獎金：新夥伴入會最高現領 $405 美元大紅包。
     ③ 代數：吃滿第一代 7%、第二代 5%、第三代 1% 的組織總收益。
     ④ 雙向獎金：比例拉高到 7%，每週最高上限直衝 $2,500 美元（約 8 萬台幣）！
     ⑤ 輔導獎金：開啟高階培育分紅，拿第一層合格下線雙向與代數獎金的 5%（每位上限 $500 美元）。
     ⑥ 突破晉升獎金：首次達成，公司直接加碼頒發 $500 美元突破大紅包！

【結尾紀律】
始終貫徹平哥核心精神
金句整理:
- 只有次數 沒有技術
- 每天進步一點點 一定會看到甜美果實
- 想是問題 做是答案 輸在猶豫 贏在行動
- 持續做對的事，養成穩定的工作習慣
從上面金句挑選一句適合鼓勵夥伴的話，但請靈活挑選，絕不套用重覆罐頭。
"""

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-pro',
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

# --- 🎯 智慧切片與分批發送處理機制 ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id  
    user_message = event.message.text
    
    # 獲取 AI 或系統直回的未切割原始文章
    raw_reply = get_prompt_and_respond(user_id, user_message)

    # 🛠️ 智慧切片核心：不論是系統死指令還是 Gemini 大腦，只要有 ===SPLIT=== 或遇到 1. 2. 3. 大段落，就進行切片
    if "===SPLIT===" in raw_reply:
        messages_text = raw_reply.split("===SPLIT===")
    else:
        # 如果大腦沒吐出手動分割符，但文章很長且有結構，我們自動按 1. 2. 3. 這種大項做切片
        parts = re.split(r'\n(?=\d\.\s|【)', raw_reply)
        if len(parts) > 1:
            messages_text = parts
        else:
            messages_text = [raw_reply]

    # 過濾多餘空白，且 LINE 一次最多允許回覆 5 則，我們精簡控制在最多 3 則
    final_texts = [t.strip() for t in messages_text if t.strip()][:3]

    # 將切片後的文字段落依序包裝成 TextMessage
    line_messages = [TextMessage(text=msg) for msg in final_texts]

    with ApiClient(line_config) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=line_messages  # 連環叮咚效果
            )
        )

if __name__ == "__main__":
    app.run(port=5000)
