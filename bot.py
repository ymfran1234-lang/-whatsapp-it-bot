"""
בוט WhatsApp — תמיכה טכנית IT צבאית
=====================================
pip install fastapi uvicorn twilio anthropic python-dotenv
"""

import os
import json
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

DB_PATH = "conversations.db"

# ─── Knowledge Base ──────────────────────────────────────────────────────────

KNOWLEDGE_BASE = """
=== מאגר תקלות IT צבאי ===

[תקלה: מדפסת לא מדפיסה]
שלבי פתרון:
1. בדוק שהמדפסת דלוקה ומחוברת לחשמל (אור ירוק/כחול)
2. בדוק שכבל USB/רשת מחובר משני הצדדים
3. לוח בקרה → מכשירים ומדפסות — האם המדפסת מופיעה? יש סימן ⚠️?
4. לחץ ימני על מדפסת → "ראה מה מודפס" → מחק את כל המשימות בתור
5. Win+R → services.msc → Print Spooler → לחץ ימני → הפעל מחדש
6. לחץ ימני על המדפסת → מאפיינים → הדפס דף בדיקה
הסלמה לטכנאי: אם המדפסת לא מופיעה בכלל, או אחרי כל השלבים עדיין לא עובד

[תקלה: דרייבר חסר / התקן לא מזוהה]
שלבי פתרון:
1. לחץ ימני על "המחשב שלי" → נהל → מנהל ההתקנים
2. חפש התקן עם ⚠️ צהוב
3. לחץ ימני → עדכן מנהל התקן → חפש אוטומטית
4. אם לא מצא — בדוק יצרן: HP: support.hp.com | Canon: canon.com/support | Dell: dell.com/support
5. הורד דרייבר, הפעל כמנהל מערכת (לחץ ימני → הפעל כמנהל)
6. הפעל מחדש את המחשב
הסלמה לטכנאי: אם המחשב נעול לאינטרנט ואי אפשר להוריד

[תקלה: מסך / פלזמה לא מזוהה]
שלבי פתרון:
1. בדוק שהמסך דלוק וכבל חשמל מחובר
2. הוצא והכנס כבל HDMI/VGA/DisplayPort משני הצדדים
3. בשלט: לחץ Source/Input → בחר HDMI1 / HDMI2 / PC
4. במחשב: Win+P → בחר "שכפל" (Duplicate)
5. לחץ ימני שולחן עבודה → הגדרות תצוגה → לחץ "זהה"
6. נסה כבל אחר / מחשב אחר
הסלמה לטכנאי: אם לא מגיב עם כבל ומחשב אחרים — ייתכן נזק פיזי

[תקלה: מקרן לא מתחבר]
שלבי פתרון:
1. המתן 30–60 שניות לחימום המקרן מרגע ההפעלה
2. בדוק כבל HDMI/VGA מחובר חזק משני הצדדים
3. לחץ Source/Input במקרן → בחר כניסה נכונה (HDMI / Computer / VGA)
4. Win+P → שכפל
5. הגדרות תצוגה → זהה
6. כוון פוקוס טבעת המקרן
הסלמה לטכנאי: אם מופיעה הודעת "Lamp Error" / נורה שרופה

[תקלה: אין רשת במחשב]
שלבי פתרון:
1. בדוק כבל רשת מחובר — נורה קטנה צריכה להדלק בחיבור
2. בדוק אם שאר המחשבים בחדר מחוברים — אם לא, בעיה בתשתית
3. לחץ ימני על סמל רשת → "פתרון בעיות"
4. פתח cmd כמנהל מערכת:
   - ipconfig /release
   - ipconfig /renew
   - ipconfig /flushdns
5. מנהל ההתקנים → בדוק כרטיס רשת — יש ⚠️?
6. כבה והדלק את המחשב
הסלמה לטכנאי: אם כל החדר ללא רשת, או אחרי כל השלבים עדיין תקוע
"""

SYSTEM_PROMPT_TECHNICIAN = f"""אתה בוט תמיכה טכנית IT צבאי. המשתמש הוא טכנאי מנוסה.
תן תשובות טכניות, מדויקות וקצרות. השתמש בטרמינולוגיה מקצועית.
אין צורך בהסברים ארוכים — פשוט תן את הפתרון הישיר.

{KNOWLEDGE_BASE}

חוקים:
- ענה בעברית בלבד
- אם התקלה לא מופיעה במאגר — ענה לפי הידע הכללי שלך
- אם הבעיה מורכבת מאוד — אמור זאת במפורש
"""

SYSTEM_PROMPT_USER = f"""אתה בוט תמיכה טכנית IT ידידותי. המשתמש הוא חייל שאינו טכנאי.
תסביר בצורה פשוטה, עם המון סבלנות. השתמש בשפה יומיומית.
צעד צעד, שאל האם הבעיה נפתרה לפני שממשיכים.
השתמש באימוג׳י כדי להפוך את ההסברים לנגישים יותר.

{KNOWLEDGE_BASE}

חוקים:
- ענה בעברית בלבד
- צעד אחד בכל הודעה — אל תציף את המשתמש
- תמיד שאל "האם זה עזר?" בסוף כל תשובה
- אם זה מורכב מדי — הפנה לטכנאי
"""

# ─── Database ─────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            user_type TEXT DEFAULT 'unknown',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            phone TEXT PRIMARY KEY,
            user_type TEXT DEFAULT 'unknown',
            state TEXT DEFAULT 'greeting',
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_session(phone: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_type, state FROM sessions WHERE phone = ?", (phone,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"user_type": row[0], "state": row[1]}
    return {"user_type": "unknown", "state": "greeting"}


def update_session(phone: str, user_type: str, state: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions (phone, user_type, state, last_active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET
            user_type=excluded.user_type,
            state=excluded.state,
            last_active=excluded.last_active
    """, (phone, user_type, state, datetime.now()))
    conn.commit()
    conn.close()


def save_message(phone: str, role: str, message: str, user_type: str = "unknown"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO conversations (phone, role, message, user_type, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (phone, role, message, user_type, datetime.now()))
    conn.commit()
    conn.close()


def get_history(phone: str, limit: int = 10) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT role, message FROM conversations
        WHERE phone = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (phone, limit))
    rows = c.fetchall()
    conn.close()
    # Return in chronological order
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


# ─── AI Logic ─────────────────────────────────────────────────────────────────

def detect_user_type(message: str) -> str | None:
    """Try to detect if the user indicated their type."""
    msg = message.strip().lower()
    technician_keywords = ["טכנאי", "מקצועי", "1", "א", "yes tech", "tech"]
    user_keywords = ["עזרה", "חייל", "לא טכנאי", "2", "ב", "רגיל"]
    
    for kw in technician_keywords:
        if kw in msg:
            return "technician"
    for kw in user_keywords:
        if kw in msg:
            return "user"
    return None


def get_ai_response(phone: str, user_message: str, user_type: str) -> str:
    history = get_history(phone, limit=10)
    
    system = SYSTEM_PROMPT_TECHNICIAN if user_type == "technician" else SYSTEM_PROMPT_USER
    
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=system,
        messages=history + [{"role": "user", "content": user_message}]
    )
    return response.content[0].text


# ─── Webhook ──────────────────────────────────────────────────────────────────

GREETING_MESSAGE = """שלום! 👋 אני הבוט לתמיכה טכנית IT.

לפני שנתחיל, ספר לי מי אתה:
1️⃣ *טכנאי* — אני מנוסה ורוצה תשובות מקצועיות
2️⃣ *זקוק לעזרה* — אני לא טכנאי, אני צריך הסבר פשוט

פשוט שלח 1 או 2 🙂"""


@app.post("/webhook")
async def webhook(
    request: Request,
    Body: str = Form(default=""),
    From: str = Form(default=""),
):
    phone = From
    user_message = Body.strip()
    
    session = get_session(phone)
    state = session["state"]
    user_type = session["user_type"]
    
    resp = MessagingResponse()
    
    # ── State: greeting (ask user type) ──
    if state == "greeting":
        save_message(phone, "assistant", GREETING_MESSAGE, user_type)
        update_session(phone, "unknown", "awaiting_type")
        resp.message(GREETING_MESSAGE)
        return PlainTextResponse(str(resp), media_type="application/xml")
    
    # ── State: awaiting_type ──
    if state == "awaiting_type":
        detected = detect_user_type(user_message)
        
        if detected == "technician":
            user_type = "technician"
            reply = "מעולה! 🔧 מה התקלה? אתן לך פתרון מקצועי ישיר."
        elif detected == "user":
            user_type = "user"
            reply = "מעולה! 😊 אני כאן בשבילך. ספר לי מה הבעיה ונפתור אותה צעד צעד."
        else:
            reply = "לא הבנתי 😅 שלח בבקשה 1 (אם אתה טכנאי) או 2 (אם אתה זקוק לעזרה)"
            resp.message(reply)
            return PlainTextResponse(str(resp), media_type="application/xml")
        
        save_message(phone, "user", user_message, user_type)
        save_message(phone, "assistant", reply, user_type)
        update_session(phone, user_type, "active")
        resp.message(reply)
        return PlainTextResponse(str(resp), media_type="application/xml")
    
    # ── State: active (normal conversation) ──
    if state == "active":
        # Allow user to reset
        if user_message.lower() in ["reset", "התחל מחדש", "restart", "מחדש"]:
            update_session(phone, "unknown", "greeting")
            reply = "בסדר! מתחילים מחדש 🔄\n\n" + GREETING_MESSAGE
            save_message(phone, "assistant", reply, user_type)
            update_session(phone, "unknown", "awaiting_type")
            resp.message(reply)
            return PlainTextResponse(str(resp), media_type="application/xml")
        
        save_message(phone, "user", user_message, user_type)
        
        try:
            ai_reply = get_ai_response(phone, user_message, user_type)
        except Exception as e:
            ai_reply = "מצטער, נתקלתי בבעיה טכנית 😅 נסה שוב עוד רגע."
            print(f"AI Error: {e}")
        
        save_message(phone, "assistant", ai_reply, user_type)
        resp.message(ai_reply)
        return PlainTextResponse(str(resp), media_type="application/xml")
    
    # Fallback
    resp.message("שגיאה לא צפויה. שלח 'התחל מחדש' לאיפוס.")
    return PlainTextResponse(str(resp), media_type="application/xml")


@app.get("/stats")
async def stats():
    """Simple stats endpoint — see what's being asked most"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(DISTINCT phone) FROM sessions")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM conversations WHERE role='user'")
    total_messages = c.fetchone()[0]
    
    c.execute("SELECT user_type, COUNT(*) FROM sessions GROUP BY user_type")
    type_breakdown = dict(c.fetchall())
    
    c.execute("""
        SELECT message FROM conversations
        WHERE role='user'
        ORDER BY timestamp DESC LIMIT 20
    """)
    recent = [r[0] for r in c.fetchall()]
    conn.close()
    
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "user_types": type_breakdown,
        "recent_questions": recent
    }


@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Bot started. DB initialized.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
