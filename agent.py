# =============================================================================
# agent.py - Personal Research Agent
# Stack: LangChain + Claude Haiku + DuckDuckGo + Gmail SMTP
# Run:   python agent.py
# Deps:  pip install langchain langchain-community langchain-anthropic
#               anthropic duckduckgo-search python-dotenv
# =============================================================================

import os, json, smtplib, datetime, time
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

# ── 1. Config ─────────────────────────────────────────────────────────────────
load_dotenv()

ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
EMAIL_RECIPIENT    = os.getenv("EMAIL_RECIPIENT")
RESEARCH_TOPIC     = os.getenv("RESEARCH_TOPIC", "AI news today")
MEMORY_FILE        = "memory.json"

# ── 2. Memory ─────────────────────────────────────────────────────────────────
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {"last_run": None, "topics_covered": []}

def save_memory(topic):
    mem = load_memory()
    mem["last_run"] = datetime.date.today().isoformat()
    mem["topics_covered"].append(topic)
    mem["topics_covered"] = mem["topics_covered"][-30:]
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)

# ── 3. Clean - removes ALL non-ASCII characters ───────────────────────────────
def clean(text):
    if text is None:
        return ""
    text = text.replace("\xa0", " ")
    text = text.replace("\u2014", "-")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2018", "'")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201c", '"')
    text = text.replace("\u201d", '"')
    text = text.replace("\u2022", "*")
    text = text.replace("\u2026", "...")
    text = text.replace("\u2192", "->")
    return "".join(c if ord(c) < 128 else " " for c in text)

# ── 4. Web search ─────────────────────────────────────────────────────────────
def web_search(query, max_results=5):
    for attempt in range(2):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No results found for: " + query
            formatted = []
            for r in results:
                formatted.append(
                    "Title: " + clean(r.get("title", "N/A")) + "\n" +
                    "Snippet: " + clean(r.get("body", "N/A")) + "\n" +
                    "URL: " + clean(r.get("href", "N/A"))
                )
            return "\n\n".join(formatted)
        except Exception as e:
            if attempt == 0:
                time.sleep(3)
            else:
                return "Search error: " + str(e)

# ── 5. Send email ─────────────────────────────────────────────────────────────
def send_email(subject, body):
    try:
        subject = clean(subject)
        body = clean(body)
        raw = (
            "From: " + GMAIL_ADDRESS + "\r\n"
            + "To: " + EMAIL_RECIPIENT + "\r\n"
            + "Subject: " + subject + "\r\n"
            + "Content-Type: text/plain\r\n"
            + "\r\n"
            + body
        )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(
                GMAIL_ADDRESS,
                EMAIL_RECIPIENT,
                raw.encode("ascii", "replace")
            )
        return "Email sent successfully."
    except smtplib.SMTPAuthenticationError:
        return "Auth failed - check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env"
    except Exception as e:
        return "Email failed: " + str(e)

# ── 6. ReAct agent ────────────────────────────────────────────────────────────
def run_agent(topic):
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=ANTHROPIC_API_KEY,
        max_tokens=1500,
        temperature=0.3,
    )

    print("  [Act] Searching the web...")
    queries = [topic, topic + " latest update", topic + " expert analysis"]
    raw_data = []
    for q in queries:
        print("    -> " + q)
        raw_data.append(web_search(q))
    combined = clean("\n\n===\n\n".join(raw_data)[:5000])

    print("  [Reason] Claude is writing your briefing...")
    system_msg = SystemMessage(content=(
        "You are a concise research analyst. Write clear factual briefings. "
        "Use only basic ASCII characters. No special quotes, em dashes, "
        "bullet symbols or accented letters. Use only letters, numbers, "
        "spaces, hyphens, and standard punctuation."
    ))
    user_msg = HumanMessage(content=(
        "Research topic: " + topic + "\n\n"
        "Raw search data:\n" + combined + "\n\n"
        "Write a daily research briefing with these sections:\n\n"
        "KEY HEADLINES\n"
        "- [3-5 points, one sentence each]\n\n"
        "SUMMARY\n"
        "[2-3 paragraphs]\n\n"
        "WHY IT MATTERS\n"
        "[1 paragraph]\n\n"
        "SOURCES\n"
        "[2-3 URLs from the search data]"
    ))

    response = llm.invoke([system_msg, user_msg])
    return clean(response.content)

# ── 7. Main ───────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  Personal Research Agent")
    print("  Topic : " + RESEARCH_TOPIC)
    print("  Date  : " + datetime.date.today().isoformat())
    print("="*55 + "\n")

    mem = load_memory()
    print("  Last run : " + str(mem["last_run"] or "never"))
    print("  Topics logged : " + str(len(mem["topics_covered"])) + "\n")

    briefing = run_agent(RESEARCH_TOPIC)

    print("\n-- Briefing preview ------------------------------------------")
    print(briefing[:300] + "...")

    today = datetime.date.today().strftime("%d %b %Y")
    subject = "Research Briefing - " + RESEARCH_TOPIC + " - " + today
    print("\n  [Email] Sending to " + str(EMAIL_RECIPIENT) + "...")
    status = send_email(subject, briefing)
    print("  " + status)

    save_memory(RESEARCH_TOPIC)
    print("\n  Memory updated. Run complete.\n")

if __name__ == "__main__":
    main()
