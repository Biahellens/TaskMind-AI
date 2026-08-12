# TaskMind AI

> Agente de IA com **tool use real** (function calling): não só responde perguntas — consulta clima, busca informação atualizada na web, cria eventos na agenda e envia e-mails de verdade.

![status](https://img.shields.io/badge/status-em%20desenvolvimento-blue) ![python](https://img.shields.io/badge/backend-FastAPI-009688) ![react](https://img.shields.io/badge/frontend-React%20%2B%20TS-61DAFB)

## Demo

<!--
  Cole aqui um screenshot ou gif da conversa em ação (recomendo gravar com o
  QuickTime/Kap e converter pra gif com gifski). Salve em docs/demo.gif e
  troque a linha abaixo por: ![demo](docs/demo.gif)
-->
`[ screenshot / gif aqui ]`

## O que é isso

A maioria dos "agentes de IA" por aí é um chatbot com prompt bonito — ele só conversa. O TaskMind é diferente: quando você pergunta algo, o modelo **decide sozinho** quais ferramentas usar, chama uma API real, espera o resultado, e só então responde — podendo encadear várias ferramentas no mesmo turno.

Exemplo real de uma única pergunta:

> "Confere se dá pra gravar externa em São Paulo sexta, e se der bom, agenda pra 15h e me manda um resumo por e-mail"

O agente: consulta o clima → decide se está bom → cria o evento na agenda → envia o e-mail. Três ferramentas, uma pergunta, zero código extra escrito por mim pra orquestrar isso — quem decide a sequência é o próprio modelo.

## Como funciona (arquitetura)

```
Frontend (React)  ──POST /api/chat──►  FastAPI backend
      ▲                                      │
      │           eventos SSE                ▼
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
                                              (calendário = mock local)
```

O loop ([backend/app/agent.py](backend/app/agent.py)) segue o padrão de tool use da API da Anthropic:

1. Backend manda a conversa pro Claude junto com a lista de tools disponíveis
2. Se o Claude responder pedindo uma ou mais tools (`stop_reason == "tool_use"`), o backend executa a função real correspondente
3. O resultado (ou erro) volta pro Claude como `tool_result`
4. Repete até o Claude decidir que já tem o suficiente pra responder em texto
5. Cada passo é emitido como evento SSE em tempo real — é o que alimenta o "🔧 Buscando na web..." na interface

Limite de 6 rounds por turno pra evitar loop infinito, e cada tool trata seus próprios erros (timeout, API fora do ar, input inválido) devolvendo `{error: true, message}` em vez de derrubar a request — o Claude vê o erro e decide como reagir, em vez do usuário tomar um 500.

## Ferramentas disponíveis

| Ferramenta | Tipo | O que faz |
|---|---|---|
| `get_weather` | leitura externa | Clima atual de qualquer cidade (OpenWeather) |
| `web_search` | leitura externa / RAG | Busca informação atualizada na web (Tavily) |
| `create_calendar_event` | escrita de estado | Cria evento numa agenda local |
| `list_calendar_events` | leitura de estado | Consulta a agenda |
| `send_email_summary` | ação com efeito real | Envia e-mail de verdade (Resend) |

O calendário é um mock local (JSON) de propósito — dá pra rodar o projeto inteiro sem configurar OAuth do Google, mantendo o foco na parte que importa (a decisão do agente e a execução da tool). Trocar por Google Calendar real é só implementar um novo executor com a mesma assinatura, sem tocar no loop.

## Stack

- **Backend**: Python + FastAPI, SDK oficial da Anthropic, streaming via Server-Sent Events
- **LLM**: Claude (Anthropic) com tool use nativo
- **Frontend**: React + TypeScript + Tailwind CSS (Vite)
- **APIs externas**: OpenWeather, Tavily, Resend

## Como rodar localmente

### Pré-requisitos

- Python 3.11+
- Node 18+
- Uma `ANTHROPIC_API_KEY` ([console.anthropic.com](https://console.anthropic.com/))
- Opcional: chaves de [OpenWeather](https://openweathermap.org/api), [Tavily](https://tavily.com/) e [Resend](https://resend.com/) — sem elas, as tools correspondentes retornam erro tratado, mas o resto do agente continua funcionando

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha as chaves
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # aponta pro backend, padrão http://localhost:8000
npm run dev
```

Abra `http://localhost:5173`.

## Estrutura do projeto

```
backend/
  app/
    main.py       # endpoint FastAPI, streaming SSE
    agent.py       # loop de tool use
    config.py      # variáveis de ambiente
    tools/         # cada tool = schema + executor isolado
frontend/
  src/
    hooks/useChat.ts       # estado do chat, parse dos eventos SSE
    lib/api.ts              # cliente SSE sobre fetch
    components/             # bolhas de chat, chip de tool call, input
```

## Decisões de design

- **Erro nunca derruba o loop**: cada tool captura sua própria exceção e devolve o erro como `tool_result` — o Claude decide como reagir, em vez de o usuário ver uma tela quebrada.
- **Histórico 100% serializável**: os content blocks da Anthropic são convertidos pra dict puro a cada turno, então o histórico pode ser devolvido ao frontend e reenviado no próximo request sem estado no servidor (mais simples de deployar, sem sessão/Redis).
- **SSE em vez de WebSocket**: a comunicação é unidirecional (backend → frontend), então SSE é mais simples de implementar e debugar que WebSocket, sem perder o streaming em tempo real.

## Roadmap

- [ ] Google Calendar real como alternativa ao mock local
- [ ] Persistir conversas (hoje o histórico vive só no state do frontend)
- [ ] Deploy: backend no Railway/Render, frontend na Vercel
- [ ] Streaming token a token do texto final (hoje cada bloco de texto chega inteiro)

## Licença

MIT
