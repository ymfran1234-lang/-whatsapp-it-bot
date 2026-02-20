"""
בוט WhatsApp — תמיכה טכנית IT צבאית
"""

import os
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

KNOWLEDGE_BASE = """
=== מאגר תקלות IT צבאי ===

[תקלה: מדפסת לא מדפיסה]
1. בדוק שהמדפסת דלוקה ומחוברת
2. בדוק כבל USB/רשת
3. לוח בקרה → מכשירים ומדפסות → בדוק סימן ⚠️
4. לחץ ימני על מדפסת → ראה מה מודפס → מחק תור
5. Win+R → services.msc → Print Spooler → הפעל מחדש
6. הדפס דף בדיקה
הסלמה: אם לא מופיעה בכלל

[תקלה: דרייבר חסר]
1. לחץ ימני על המחשב שלי → נהל → מנהל ההתקנים
2. חפש ⚠️ צהוב
3. לחץ ימני → עדכן מנהל התקן
4. אם לא מצא — הורד מאתר היצרן
5. הפעל כמנהל מערכת
6. הפעל מחדש

[תקלה: אין רשת]
1. בדוק כבל רשת — נורה צריכה להדלק
2. בדוק אם שאר המחשבים מחוברים
3. לחץ ימני על סמל רשת → פתרון בעיות
4. פתח cmd כמנהל: ipconfig /release → ipconfig /renew → ipconfig /flushdns
5. כבה והדלק

[תקלה: שגיאות התחברות למחשב - כרטיס חכם / מפל"ז]

שגיאה: "The User Profile Service service failed to sign-in" / "User Profile cannot be loaded"
פתרון: פרופיל מקומי בעייתי. יש למחוק פרופיל מקומי באמצעות MamramDelProof ולדאוג לגיבוי.
פתרון מתקדם: להיכנס עם משתמש חזק, לפתוח regedit, לגשת לנתיב:
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList
למצוא תיקייה עם המספר האישי של המשתמש ולמחוק אותה.
אם לא עובד: לפתוח cmd ולהריץ: gpupdate /force

שגיאה: "The security database on the server does not have a computer account for this workstation trust relationship"
פתרון: שם מחשב בעייתי או נמחק מהאקטיב. להכניס לדומיין עם שם מחשב חדש. לפנות למנהלי רשת.

שגיאה: "Kerberos" / שגיאת כרטיס חכם KDC
פתרון: תקלה בדרייבר קורא כרטיסים. למחוק דרייבר ולהתקין מחדש גרסה ARX 5.2.1

שגיאה: "Windows cannot connect to the domain"
פתרון: לבדוק שם מחשב ובעיות רשת. כנראה לא בדומיין או אין רשת.

שגיאה: "The Group Policy Client service failed to sign-in. Access is denied"
פתרון: למחוק פרופיל מקומי באמצעות MamramDelProof ולדאוג לגיבוי.

שגיאה: "No valid certificates were found on this smart card"
פתרון רגיל: לנקות את הצ'יפ או לקודד מחדש.
אם לכל כרטיס זה קורה: לעדכן ARX לגרסה 5.2.1
פתרון מפל"ז: יש לבצע קידוד מפל"ז

שגיאה: "The smart card certificate used for authentication has been revoked" / "האישורים בוטלו"
פתרון: בעיה ב"מית". לבדוק אם מפליז מוגדר בעמדת הקידוד (עין הסערה).

שגיאה: "The smart card is Blocked" / "חסום"
פתרון: לקודד מחדש בב"מ / מפל"ז.

שגיאה: "Your account has been disabled/locked" / "החשבון שלך הפך ללא זמין"
פתרון: לפתוח בניהו"ז באופציה הראשונה, או שהמשתמש נמצא בארכיון.

שגיאה: "Your account has been locked out"
פתרון: לפתוח בניהול זהויות (באופציה השנייה).

שגיאה: "The referenced account is currently locked out" / "האדמין נעול"
פתרון: להתחבר באמצעות לא אכוף, לאפס ולשחרר את האדמין מנעילה (בניהול מחשב).

שגיאה: "Your certificates cannot be verified"
פתרון: לפי המערכת המשתמש לא קיים. לפתוח משתמש אם אין, לוודא שקיים באקטיב, לנסות בניהול זהויות או למחוק ולפתוח חדש.

שגיאה: "The revocation status of the smart card certificate could not be determined"
פתרון: לעדכן תאריך ושעה בעמדת הקצה.

שגיאה: "An untrusted certificate authority was detected" / "זוהתה רשות אישורים לא מהימנה"
פתרון: המחשב לא בדומיין. להכניס מחדש לדומיין.

שגיאה: "There is a time and/or date difference between the client and server"
פתרון: ריסטארט פותר את התקלה.

שגיאה: "There are currently no logon servers available" / "לא קיימים כעת שרתי כניסה"
פתרון: אין רשת.

שגיאה: "The domain specified is not available"
פתרון: בעיית רשת. לפנות למנהלי רשת.

שגיאה: "We can't sign you in with this credential because your domain isn't available"
פתרון: אין רשת.

שגיאה: "This computer is locked. Only the signed-in user can unlock"
פתרון: ללחוץ על Switch User.

שגיאה: "מחשבך אינו רשאי להתחבר... SCCM של ממרם"
פתרון: להפיץ SCCM למחשב דרך האתר או להכניס מחדש לדומיין עם שם מחשב קצר יותר. אם לא עוזר — לפרמט.

שגיאה: "מחשבך אינו מכיל אנטי וירוס מקאפי"
פתרון: לוודא שיש מקאפי (כולל 4 רכיבים תקינים). להתקין מקאפי מתיקיות רשת.

שגיאה: "The remote procedure call failed"
פתרון: לנסות להיכנס עם לא אכוף, אם לא עובד — לפרמט.

שגיאה: "You must use Windows Hello or a smart card to sign in"
פתרון: נגמר הלא אכוף.

שגיאה: "The smart card requires drivers that are not present on this system"
פתרון: לתאם עם מנהלי רשת להתקנת רכיב ARX.

שגיאה: "The smart card cannot perform the requested operation"
פתרון: לפתוח certmgr.msc → Personal → למחוק הכל חוץ מ-communication server → ריסטארט.

שגיאה: "The smart card was not recognized"
פתרון: אם נורה בצד הימין של המקלדת לא נדלקת — צריך להחליף את המפל"ז.

[תקלה: PROXY - כרום מבקש שם משתמש וסיסמא]
1. לחפש Internet Options בשורת חיפוש
2. להיכנס ללשונית Security
3. ללחוץ Custom Level
4. לגלול למטה ל-User Authentication
5. ב-Logon לבחור: Automatic Logon with current username and password
6. ללחוץ החל ושמור, ריפרש לעמוד

[תקלה: מסך לא מזוהה]
1. בדוק שהמסך דלוק וכבל חשמל מחובר
2. הוצא והכנס כבל HDMI/VGA/DisplayPort
3. בשלט: לחץ Source/Input → בחר HDMI
4. Win+P → שכפל
5. הגדרות תצוגה → זהה
הסלמה: נזק פיזי

[תקלה: מקרן לא מתחבר]
1. המתן 30-60 שניות לחימום
2. בדוק כבל HDMI/VGA
3. לחץ Source/Input במקרן
4. Win+P → שכפל
5. הגדרות תצוגה → זהה
הסלמה: Lamp Error — נורה שרופה
"""

SYSTEM_PROMPT_TECHNICIAN = f"""אתה בוט תמיכה טכנית IT צבאי. המשתמש הוא טכנאי מנוסה.
תן תשובות טכניות, מדויקות וקצרות.

{KNOWLEDGE_BASE}

חוקים:
- ענה בעברית בלבד
- אם התקלה לא מופיעה במאגר — ענה לפי הידע הכללי שלך
- אם הבעיה מורכבת — אמור זאת במפורש
"""

SYSTEM_PROMPT_USER = f"""אתה בוט תמיכה טכנית IT ידידותי. המשתמש הוא חייל שאינו טכנאי.
תסביר בצורה פשוטה, עם סבלנות. צעד צעד. השתמש באימוג׳י.

{KNOWLEDGE_BASE}

חוקים:
- ענה בעברית בלבד
- צעד אחד בכל הודעה
- תמיד שאל "האם זה עזר?" בסוף
- אם זה מורכב מדי — הפנה לטכנאי
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL, role TEXT NOT NULL,
        message TEXT NOT NULL, user_type TEXT DEFAULT 'unknown',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        phone TEXT PRIMARY KEY, user_type TEXT DEFAULT 'unknown',
        state TEXT DEFAULT 'greeting',
        last_active DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def get_session(phone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_type, state FROM sessions WHERE phone = ?", (phone,))
    row = c.fetchone()
    conn.close()
    return {"user_type": row[0], "state": row[1]} if row else {"user_type": "unknown", "state": "greeting"}

def update_session(phone, user_type, state):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO sessions (phone, user_type, state, last_active) VALUES (?, ?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET user_type=excluded.user_type,
        state=excluded.state, last_active=excluded.last_active""",
        (phone, user_type, state, datetime.now()))
    conn.commit()
    conn.close()

def save_message(phone, role, message, user_type="unknown"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO conversations (phone, role, message, user_type, timestamp) VALUES (?, ?, ?, ?, ?)",
        (phone, role, message, user_type, datetime.now()))
    conn.commit()
    conn.close()

def get_history(phone, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, message FROM conversations WHERE phone = ? ORDER BY timestamp DESC LIMIT ?", (phone, limit))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def detect_user_type(message):
    msg = message.strip().lower()
    for kw in ["טכנאי", "מקצועי", "1"]:
        if kw in msg: return "technician"
    for kw in ["עזרה", "חייל", "לא טכנאי", "2"]:
        if kw in msg: return "user"
    return None

def get_ai_response(phone, user_message, user_type):
    history = get_history(phone, limit=10)
    system = SYSTEM_PROMPT_TECHNICIAN if user_type == "technician" else SYSTEM_PROMPT_USER
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600, system=system,
        messages=history + [{"role": "user", "content": user_message}])
    return response.content[0].text

GREETING_MESSAGE = """שלום! 👋 אני הבוט לתמיכה טכנית IT.

לפני שנתחיל, ספר לי מי אתה:
1️⃣ *טכנאי* — אני מנוסה ורוצה תשובות מקצועיות
2️⃣ *זקוק לעזרה* — אני לא טכנאי, אני צריך הסבר פשוט

פשוט שלח 1 או 2 🙂"""

@app.post("/webhook")
async def webhook(request: Request, Body: str = Form(default=""), From: str = Form(default="")):
    phone = From
    user_message = Body.strip()
    session = get_session(phone)
    state = session["state"]
    user_type = session["user_type"]
    resp = MessagingResponse()

    if state == "greeting":
        save_message(phone, "assistant", GREETING_MESSAGE, user_type)
        update_session(phone, "unknown", "awaiting_type")
        resp.message(GREETING_MESSAGE)
        return PlainTextResponse(str(resp), media_type="application/xml")

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

    if state == "active":
        if user_message.lower() in ["reset", "התחל מחדש", "restart", "מחדש"]:
            update_session(phone, "unknown", "awaiting_type")
            reply = "בסדר! מתחילים מחדש 🔄\n\n" + GREETING_MESSAGE
            save_message(phone, "assistant", reply, user_type)
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

    resp.message("שגיאה לא צפויה. שלח 'התחל מחדש' לאיפוס.")
    return PlainTextResponse(str(resp), media_type="application/xml")

@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Bot started.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
