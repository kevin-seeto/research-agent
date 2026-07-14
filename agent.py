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
from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup
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
def fetch_article(url):
    """Fetch full text from a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=5, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs[:20])
        return clean(text[:2000])
    except:
        return ""
    
def web_search(query, max_results=5):
    """Try Tavily first, fall back to DuckDuckGo."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_raw_content=True
        )
        results = []
        for r in response["results"]:
            results.append(
                "Title: " + clean(r.get("title", "")) + "\n" +
                "Content: " + clean(r.get("content", "")) + "\n" +
                "URL: " + clean(r.get("url", ""))
            )
        return "\n\n".join(results)
    except Exception:
        # Fallback to DuckDuckGo if Tavily fails
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
    
# ── 6. Prepare LinkedIn draft for approval ────────────────────────────────────
def prepare_linkedin_draft(briefing, linkedin_post, topic):
    """Save LinkedIn post draft to file for manual review before posting."""
    try:
        today = datetime.date.today().strftime("%d %b %Y")
        now = datetime.datetime.now().strftime("%d %b %Y at %I:%M %p")
        post_text = clean(
            "=== DRAFT GENERATED: " + now + " ===\n\n"
            "=== FULL RESEARCH BRIEFING ===\n\n"
            "The AI Research Digest - " + today + "\n\n"
            + briefing
            + "\n\n"
            "=" * 50 + "\n\n"
            "=== LINKEDIN POST (ready to publish) ===\n"
            "Characters: " + str(len(linkedin_post)) + " of 2800 limit\n\n"
            + linkedin_post
        )

        os.makedirs("drafts", exist_ok=True)
        today_file = datetime.date.today().strftime("%Y-%m-%d")
        filename = "drafts/linkedin_draft_" + today_file + ".txt"
        with open(filename, "w") as f:
            f.write(post_text)
        return "LinkedIn draft saved to linkedin_draft.txt - review and edit before posting."
    except Exception as e:
        return "Draft save error: " + str(e)

# ── 7. Post approved draft to LinkedIn ───────────────────────────────────────
def post_to_linkedin(post_text):
    """Post approved text to LinkedIn."""
    try:
        import requests
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": "Bearer " + os.getenv("LINKEDIN_ACCESS_TOKEN"),
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        payload = {
            "author": "urn:li:person:" + os.getenv("LINKEDIN_PERSON_ID"),
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            return "LinkedIn post published successfully."
        else:
            return "LinkedIn post failed: " + str(response.status_code) + " " + response.text
    except Exception as e:
        return "LinkedIn error: " + str(e)

# ── 8. ReAct agent ────────────────────────────────────────────────────────────
def run_agent(topic):
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=ANTHROPIC_API_KEY,
        max_tokens=1500,
        temperature=0.3,
    )

    print("  [Act] Searching the web...")
    queries = [topic, 
        topic + " latest update 2026", 
        topic + " expert analysis",
        topic + " case studies",
        topic + " challenges and risks",
        topic + " future trends"
    ]
    raw_data = []
    for q in queries:
        print("    -> " + q)
        raw_data.append(web_search(q))
    combined = clean("\n\n===\n\n".join(raw_data)[:8000])

    print("  [Reason] Claude is writing your briefing...")

    # Load memory to tell Claude what was already covered
    mem = load_memory()
    recent_topics = str(mem["topics_covered"][-5:]) if mem["topics_covered"] else "none"

    system_msg = SystemMessage(content=(
        "You are a concise research analyst. Write clear factual briefings. "
        "Use only basic ASCII characters. No special quotes, em dashes, "
        "bullet symbols or accented letters. Use only letters, numbers, "
        "spaces, hyphens, and standard punctuation."
    ))
    user_msg = HumanMessage(content=(
        "Research topic: " + topic + "\n\n"
        "Topics already covered in recent runs: " + recent_topics + "\n"
        "Focus on NEW developments not already covered above.\n\n"
        "Raw search data:\n" + combined + "\n\n"
        "Write The AI Research Digest with these sections:\n\n"
        "KEY HEADLINES\n"
        "- [3-5 points, one sentence each]\n\n"
        "SUMMARY\n"
        "[2-3 paragraphs]\n\n"
        "WHY IT MATTERS\n"
        "[1 paragraph]\n\n"
        "SOURCES\n"
        "[2-3 URLs from the search data]"
    ))

    response = llm.invoke(
        [system_msg, user_msg],
        config={"run_name": "write_briefing", "tags": ["briefing"]},
    )
    briefing = clean(response.content)

    # Second Claude call - write LinkedIn post within 2800 char limit
    print("  [Reason] Claude is writing LinkedIn post...")
    linkedin_msg = HumanMessage(content=(
            "Based on this research briefing, write a LinkedIn post.\n\n"
            "STRICT RULES:\n"
            "- Maximum 2800 characters total including hashtags\n"
            "- Must be complete and coherent - no cutting off mid-sentence\n"
            "- Structure: hook opening line, key findings, why it matters, call to action\n"
            "- End with: #AI #AgenticAI #EnterpriseAI #Research #LLM\n"
            "- Use only plain ASCII characters\n"
            "- Write as if you are a human expert sharing insights\n"
            "- Do not mention it was AI generated\n"
            "- DO NOT include any URLs, links, or web addresses\n"
            "- DO NOT include any source references with URLs\n"
            "- DO NOT use http, https, www or any domain names\n"
            "- DO NOT include a Sources or References section\n"
            "- Reference sources by name only e.g. 'According to McKinsey' not a URL\n"
            "- The post must be entirely self-contained with no external links\n"
            "- End with a thought-provoking question to encourage comments\n"
            "- Put the question directly before the hashtags\n"
            "- The question should relate directly to the topic and invite opinion\n\n"
            "Research briefing:\n" + briefing
        ))

    linkedin_response = llm.invoke(
        [system_msg, linkedin_msg],
        config={"run_name": "write_linkedin_post", "tags": ["linkedin"]},
    )
    linkedin_post = clean(linkedin_response.content)

    # Verify length and ask Claude to shorten if needed
    if len(linkedin_post) > 2800:
        print("  [Reason] Post too long - Claude is shortening...")
        shorten_msg = HumanMessage(content=(
            "This LinkedIn post is " + str(len(linkedin_post)) + " characters. "
            "Rewrite it to be under 2800 characters total. "
            "STRICT RULES when shortening:\n"
            "- Keep it complete and coherent - do not cut off mid-sentence\n"
            "- Shorten the middle body sections first\n"
            "- ALWAYS preserve the thought-provoking question near the end\n"
            "- ALWAYS preserve the hashtags at the very end\n"
            "- NEVER remove the opening hook line\n"
            "- NEVER remove the closing question\n"
            "- NEVER remove the hashtags\n"
            "- Do not include any URLs, links, http, https, www or domain names\n\n"
            "Post to shorten:\n" + linkedin_post
        ))
        linkedin_response = llm.invoke(
            [system_msg, shorten_msg],
            config={"run_name": "shorten_linkedin_post", "tags": ["linkedin", "retry"]},
        )
        linkedin_post = clean(linkedin_response.content)

    return briefing, linkedin_post

# ── 9. Main ───────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  Personal Research Agent")
    print("  Topic : " + RESEARCH_TOPIC)
    print("  Date  : " + datetime.date.today().isoformat())
    print("="*55 + "\n")

    mem = load_memory()
    print("  Last run : " + str(mem["last_run"] or "never"))
    print("  Topics logged : " + str(len(mem["topics_covered"])) + "\n")

    briefing, linkedin_post = run_agent(RESEARCH_TOPIC)

    print("\n-- Briefing preview ------------------------------------------")
    print(briefing[:300] + "...")

    today = datetime.date.today().strftime("%d %b %Y")
    subject = "The AI Research Digest - " + RESEARCH_TOPIC + " - " + today
    print("\n  [Email] Sending to " + str(EMAIL_RECIPIENT) + "...")
    status = send_email(subject, briefing)
    print("  " + status)

# Save LinkedIn draft for manual approval
    print("\n  [LinkedIn] Saving draft for your approval...")
    li_draft = prepare_linkedin_draft(briefing, linkedin_post, RESEARCH_TOPIC)
    print("  " + li_draft)
    print("  Review linkedin_draft.txt then run: python post_now.py")

    save_memory(RESEARCH_TOPIC)
    print("\n  Memory updated. Run complete.\n")

if __name__ == "__main__":
    main()
