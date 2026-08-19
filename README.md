# TaskMind AI

> AI agent with **real tool use** (function calling): it doesn't just answer questions — it checks the weather, searches the web for up-to-date info, creates calendar events, and sends real emails.

![status](https://img.shields.io/badge/status-in%20development-blue) ![python](https://img.shields.io/badge/backend-FastAPI-009688) ![react](https://img.shields.io/badge/frontend-React%20%2B%20TS-61DAFB)

## Demo

![TaskMind](https://github.com/Biahellens/TaskMind-AI/blob/main/desktop-app.png)

## What this is

Most "AI agents" out there are just a chatbot with a nice prompt — they only talk. TaskMind is different: when you ask something, the model **decides on its own** which tools to use, calls a real API, waits for the result, and only then responds — chaining multiple tools in the same turn if needed.

Real example of a single prompt:

> "Check if the weather's good enough to film outdoors in São Paulo on Friday, and if it is, schedule it for 3pm and send me a summary by email"

The agent: checks the weather → decides if it's good → creates the calendar event → sends the email. Three tools, one question, zero extra code written by me to orchestrate it — the model itself decides the sequence.

## How it works (architecture)

```
Frontend (React)  ──POST /api/chat──►  FastAPI backend
      ▲                                      │
      │           SSE events                 ▼
      │   (tool_call, tool_result, text) ┌─────────────┐
      └───────────────────────────────── │ Agent Loop   │
                                          └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │Tool Registry │
                                          └──────┬───────┘
                                    ┌────────────┼────────────┐
                                    ▼            ▼            ▼
                              OpenWeather   Tavily API    Resend API
                                              (calendar = local mock)
```

The loop ([backend/app/agent.py](backend/app/agent.py)) follows the Anthropic API's tool use pattern:

1. The backend sends the conversation to Claude along with the list of available tools
2. If Claude responds asking for one or more tools (`stop_reason == "tool_use"`), the backend executes the matching real function
3. The result (or error) goes back to Claude as a `tool_result`
4. Repeat until Claude decides it has enough to answer in plain text
5. Every step is emitted as a real-time SSE event — that's what powers the "🔧 Searching the web..." indicator in the UI

Capped at 6 rounds per turn to prevent infinite loops, and each tool handles its own errors (timeout, API down, invalid input) by returning `{error: true, message}` instead of crashing the request — Claude sees the error and decides how to react, instead of the user getting a 500.

## Available tools

| Tool | Type | What it does |
|---|---|---|
| `get_weather` | external read | Current weather for any city (OpenWeather) |
| `web_search` | external read / RAG | Searches the web for up-to-date info (Tavily) |
| `create_calendar_event` | state write | Creates an event in a local calendar |
| `list_calendar_events` | state read | Lists calendar events |
| `send_email_summary` | real-world side effect | Sends a real email (Resend) |

The calendar is a local mock (JSON) on purpose — it lets you run the whole project without setting up Google OAuth, keeping the focus on what actually matters (the agent's decision-making and tool execution). Swapping in real Google Calendar just means implementing a new executor with the same signature, without touching the loop.

## Stack

- **Backend**: Python + FastAPI, official Anthropic SDK, streaming via Server-Sent Events
- **LLM**: Claude (Anthropic) with native tool use
- **Frontend**: React + TypeScript + Tailwind CSS (Vite)
- **External APIs**: OpenWeather, Tavily, Resend

## Running locally

### Prerequisites

- Python 3.11+
- Node 18+
- An `ANTHROPIC_API_KEY` ([console.anthropic.com](https://console.anthropic.com/))
- Optional: [OpenWeather](https://openweathermap.org/api), [Tavily](https://tavily.com/), and [Resend](https://resend.com/) keys — without them, the corresponding tools return a handled error, but the rest of the agent keeps working

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # points to the backend, defaults to http://localhost:8000
npm run dev
```

Open `http://localhost:5173`.

## Project structure

```
backend/
  app/
    main.py       # FastAPI endpoint, SSE streaming
    agent.py       # tool use loop
    config.py      # environment variables
    tools/         # each tool = schema + isolated executor
frontend/
  src/
    hooks/useChat.ts       # chat state, parses SSE events
    lib/api.ts              # SSE client over fetch
    components/             # chat bubbles, tool call chip, input
```

## Design decisions

- **Errors never break the loop**: each tool catches its own exception and returns the error as a `tool_result` — Claude decides how to react, instead of the user seeing a broken screen.
- **Fully serializable history**: Anthropic's content blocks are converted to plain dicts on every turn, so the history can be returned to the frontend and resent on the next request with no server-side state (simpler to deploy, no session/Redis needed).
- **SSE instead of WebSocket**: communication is one-directional (backend → frontend), so SSE is simpler to implement and debug than WebSocket, without losing real-time streaming.

## Roadmap

- [ ] Real Google Calendar as an alternative to the local mock
- [ ] Persist conversations (today the history only lives in frontend state)
- [ ] Deploy: backend on Railway/Render, frontend on Vercel
- [ ] Token-by-token streaming of the final text (currently each text block arrives whole)

## License

MIT
