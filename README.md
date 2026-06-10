# Personal Research Agent

An autonomous AI agent that searches the web, synthesises findings, 
and emails a daily research briefing.

## Stack
- LangChain — agent orchestration
- Claude Haiku (Anthropic API) — LLM reasoning
- DuckDuckGo Search — free web search
- Gmail SMTP — email delivery
- Windows Task Scheduler — daily automation

## How it works
1. Agent searches the web across 3 query angles
2. Claude Haiku synthesises findings using ReAct reasoning
3. Formatted briefing emailed to inbox automatically every morning

## Skills demonstrated
- Agentic AI and LLM orchestration
- Prompt engineering
- API integration (Anthropic, Gmail)
- Python automation
- Environment management

## Architecture
- Multi-angle search: 6 query dimensions per topic
- Resilient search: Tavily API with DuckDuckGo fallback
- Deep content: Full article scraping via BeautifulSoup
- LLM reasoning: Claude Haiku ReAct loop
- Output: Automated Gmail delivery
- Memory: JSON session persistence
- Schedule: Windows Task Scheduler daily automation

## Sample Output
See sample_output.txt for a real briefing example
