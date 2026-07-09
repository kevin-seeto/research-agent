# Personal Research Agent

An autonomous AI agent that searches the web across multiple angles,
scrapes full article content, synthesises findings using Claude AI,
and emails a structured daily research briefing automatically.

## What it does
- Searches the web across 6 query dimensions per topic
- Scrapes full article content from top results
- Synthesises findings using Claude Haiku ReAct reasoning
- Emails a formatted briefing to your inbox every morning
- Remembers past topics to avoid repeating content
- Runs automatically via Windows Task Scheduler daily

## Stack
- LangChain - agent orchestration and ReAct loop
- Anthropic Claude Haiku - LLM reasoning and synthesis
- Tavily API - primary deep search (AI-optimised)
- DuckDuckGo - fallback search if Tavily unavailable
- BeautifulSoup - full article web scraping
- Gmail SMTP - automated email delivery
- Windows Task Scheduler - daily automation
- JSON - session memory persistence

## Architecture
- Multi-angle search: 6 query dimensions per topic
- Resilient search: Tavily primary with DuckDuckGo fallback
- Deep content: Full article scraping via BeautifulSoup
- ReAct loop: Reason, Act, Observe, Reason, Act
- Fault tolerant: Error handling at every layer
- Memory: JSON session persistence across runs
- Schedule: Runs automatically every morning

## How it works
1. Task Scheduler triggers agent.py every morning
2. Agent loads memory to check what was covered recently
3. Generates 6 search queries from your chosen topic
4. Searches via Tavily API with DuckDuckGo fallback
5. Scrapes full article content from top 2 results per query
6. Passes all data to Claude Haiku for ReAct reasoning
7. Claude synthesises a structured daily briefing
8. Agent emails briefing to your inbox automatically
9. Memory updated with todays topic for next run

## Setup
1. Clone the repository
2. Create virtual environment: python -m venv venv
3. Activate: venv\Scripts\activate (Windows)
4. Install dependencies: pip install -r requirements.txt
5. Create .env file with your credentials (see below)
6. Run: python agent.py

## Environment variables (.env file)
