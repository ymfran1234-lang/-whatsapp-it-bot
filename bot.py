"""
בוט WhatsApp — תמיכה טכנית IT צבאית
"""

import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

app = FastAPI()
DB_PATH = "conversations.db"

KNOWLEDGE_BASE = """
=== מאגר תקלות IT צבאי ===

[תקלה: מדפסת לא מדפיסה]
1. בדוק שהמדפסת דלוקה ומחוברת
2. בדוק כבל USB/רשת
3. לוח בקרה → מכשירים ומדפסות → בדוק סימן ⚠️
4. לחץ ימני על מדפסת → ראה מה מודפס → מחק תור
5. Win+R → services.msc → Print Spooler → הפעל מחדש
6. הדפס דף בדיקה

[תקלה: אין רשת]
1. בדוק כבל רשת — נורה צריכה להדלק
2. בדוק אם שאר המחשבים מחוברים
3. לחץ ימני על סמל רשת → פתרון בעיות
4. פתח cmd כמנהל: ipconfig /release → ipconfig /renew → ipconfig /flushdns
5. כבה והדלק

[תקלה: שגיאות התחברות - כרטיס חכם / מפל"ז]

שגיאה: "The User Profile Service failed to sign-in"
פתרון: מחק פרופיל מקומי עם MamramDelProof. אם לא עובד: regedit → HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList → מחק תיקייה עם המספר האישי. אם לא עובד: cmd → gpupdate /force

שגיאה: "The security database does not have a computer account"
פתרון: להכניס לדומיין עם שם מחשב חדש.

שגיאה: Kerberos / KDC
פתרון: תקלה בדרייבר קורא כרטיסים. התקן ARX 5.2.1

שגיאה: "Windows cannot connect to the domain"
פתרון: לבדוק שם מחשב ורשת.

שגיאה: "No valid certificates were found"
פתרון: לנקות צ'יפ או לקודד מחדש. אם לכל כרטיס: עדכן ARX 5.2.1

שגיאה: "The smart card is Blocked"
פתרון: לקודד מחדש בב"מ.

שגיאה: "Your account has been disabled/locked"
פתרון: לפתוח בניהו"ז באופציה הראשונה.

שגיאה: "Your account has been locked out"
פתרון: לפתוח בניהול זהויות (באופציה השנייה).

שגיאה: "The referenced account is currently locked out"
פתרון: להתחבר עם לא אכוף ולשחרר אדמין מנעילה.

שגיאה: "Your certificates cannot be verified"
פתרון: משתמש לא קיים. לפתוח באקטיב או למחוק ולפתוח חדש.

שגיאה: "time and/or date difference"
פתרון: ריסטארט.

שגיאה: "no logon servers available" / "domain not available"
פתרון: אין רשת.

שגיאה: "This computer is locked"
פתרון: Switch User.

שגיאה: SCCM של ממרם
פתרון: להפיץ SCCM מתיקיות רשת. אם לא עוזר — לפרמט.

שגיאה: מקאפי חסר
פתרון: להתקין מקאפי מתיקיות רשת (4 רכיבים).

שגיאה: "remote procedure call failed"
פתרון: להיכנס עם לא אכוף. אם לא עובד — לפרמט.

שגיאה: "You must use Windows Hello or a smart card"
פתרון: נגמר הלא אכוף.

שגיאה: "smart card requires drivers"
פתרון: להתקין ARX עם מנהלי רשת.

שגיאה: "smart card cannot perform the requested operation"
פתרון: certmgr.msc → Personal → מחק הכל חוץ מ-communication server → ריסטארט.

שגיאה: "smart card was not recognized"
פתרון: אם נורה ימנית לא נדלקת — להחליף מפל"ז.

[תקלה: PROXY - כרום מבקש סיסמא]
1. Internet Options → Security → Custom Level
2. User Authentication → Logon
3. בחר: Automatic Logon with current username and password
4. החל ושמור → ריפרש

[תקלה: מסך לא מזוהה]
1. הוצא והכנס כבל HDMI/VGA
2. Source/Input בשלט → בחר HDMI
3. Win+P → שכפל
4. הגדרות תצוגה → זהה

[תקלה: מקרן לא מתחבר]
1. המתן 60 שניות לחימום
2. Source/Input במקרן
3. Win+P → שכפל
"""

SYSTEM_TECHNICIAN = f"""אתה בוט תמיכה טכנית IT צבאי. המשתמש הוא טכנאי מנוסה.
תן תשובות טכניות, מדויקות וקצרות. ענה בעברית בלבד.
{KNOWLEDGE_BASE}"""

SYSTEM_USER = f"""אתה בוט תמיכה טכנית IT ידידותי. המשתמש הוא חייל שאינו טכנאי.
תסביר בצורה פשוטה, צעד צעד, עם אימוג׳י. ענה בעברית בלבד.
בסוף כל תשובה שאל: האם זה עזר?
{KNOWLEDGE_BASE}"""

GREETING = """שלום! 👋 אני הבוט לתמיכה טכנית IT.

ספר לי מי אתה:
1️⃣ *טכנאי* — רוצה תשובות מקצועיות
2️⃣ *זקוק לעזרה* — צריך הסבר פשוט

שלח 1 או 2 🙂"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        phone TEXT PRIMARY KEY, user_type TEXT DEFAULT 'unknown',
        state TEXT DEFAULT 'greeting', history TEXT DEFAULT '',
        last_active DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def get_session(phone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_type, state, history FROM sessions WHERE phone = ?", (phone,))
    row = c.fetchone()
    conn.close()
    return {"user_type": row[0], "state": row[1], "history": row[2]} if row else {"user_type": "unknown", "state": "greeting", "history": ""}

def update_session(phone, user_type, state, history=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO sessions (phone, user_type, state, history, last_active) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET user_type=excluded.user_type,
        state=excluded.state, history=excluded.history, last_active=excluded.last_active""",
        (phone, user_type, state, history, datetime.now()))
    conn.commit()
    conn.close()

def get_ai_response(user_message, user_type, history_text):
    system = SYSTEM_TECHNICIAN if user_type == "technician" else SYSTEM_USER
    prompt = f"{system}\n\nהיסטוריית שיחה:\n{history_text}\n\nמשתמש: {user_message}\nבוט:"
    response = model.generate_content(prompt)
    return response.text

def detect_type(message):
    msg = message.strip().lower()
    if any(k in msg for k in ["1", "טכנאי", "מקצועי"]):
        return "technician"
    if any(k in msg for k in ["2", "עזרה", "חייל", "לא טכנאי"]):
        return "user"
    return None

@app.post("/webhook")
async def webhook(request: Request, Body: str = Form(default=""), From: str = Form(default="")):
    phone = From
    msg = Body.strip()
    session = get_session(phone)
    state = session["state"]
    user_type = session["user_type"]
    history = session["history"]
    resp = MessagingResponse()

    if state == "greeting":
        update_session(phone, "unknown", "awaiting_type", "")
        resp.message(GREETING)
        return PlainTextResponse(str(resp), media_type="application/xml")

    if state == "awaiting_type":
        detected = detect_type(msg)
        if detected == "technician":
            update_session(phone, "technician", "active", "")
            resp.message("מעולה! 🔧 מה התקלה?")
        elif detected == "user":
            update_session(phone, "user", "active", "")
            resp.message("מעולה! 😊 ספר לי מה הבעיה.")
        else:
            resp.message("שלח 1 (טכנאי) או 2 (זקוק לעזרה)")
        return PlainTextResponse(str(resp), media_type="application/xml")

    if state == "active":
        if msg.lower() in ["reset", "התחל מחדש", "restart"]:
            update_session(phone, "unknown", "awaiting_type", "")
            resp.message("מתחילים מחדש 🔄\n\n" + GREETING)
            return PlainTextResponse(str(resp), media_type="application/xml")
        try:
            reply = get_ai_response(msg, user_type, history)
            new_history = history + f"\nמשתמש: {msg}\nבוט: {reply}"
            new_history = new_history[-3000:]
            update_session(phone, user_type, "active", new_history)
        except Exception as e:
            reply = "מצטער, נתקלתי בבעיה. נסה שוב."
            print(f"Error: {e}")
        resp.message(reply)
        return PlainTextResponse(str(resp), media_type="application/xml")

    resp.message("שלח 'התחל מחדש' לאיפוס.")
    return PlainTextResponse(str(resp), media_type="application/xml")

@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Bot started with Gemini.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
