from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def chat_page(request: Request) -> HTMLResponse:
    """Serve the browser chat without a separate frontend build step."""
    return HTMLResponse(_CHAT_PAGE)


@router.post("/messages", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(payload: ChatRequest) -> ChatResponse:
    try:
        return await ChatService().answer(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O servico de busca dos manuais esta indisponivel no momento.",
        ) from exc


@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: str) -> ChatHistoryResponse:
    return ChatService().history(session_id)


_CHAT_PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TorqueAI — Assistente de Oficina</title>
  <style>
    :root {
      --bg: #0e1216;
      --bg-soft: #141a20;
      --panel: #1a2229;
      --panel-2: #202a33;
      --line: #2a3540;
      --ink: #e8edf1;
      --muted: #8fa1af;
      --accent: #f5a623;
      --accent-2: #e08914;
      --steel: #4a5f6b;
      --ok: #34c77b;
      --warn: #e0553d;
      --mono: "SFMono-Regular", "JetBrains Mono", "Fira Code", ui-monospace, Menlo, Consolas, monospace;
      --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Helvetica, Arial, sans-serif;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0; color: var(--ink);
      background: radial-gradient(1200px 600px at 80% -10%, #1b2730 0%, var(--bg) 55%);
      font-family: var(--sans); font-size: 15px; line-height: 1.5;
    }
    .app { display: grid; grid-template-columns: 280px 1fr; gap: 18px; max-width: 1180px; margin: 0 auto; padding: 20px; min-height: 100vh; }
    .brand { display: flex; align-items: center; gap: 12px; padding: 20px 22px; border-bottom: 1px solid var(--line); }
    .brand .mark { width: 34px; height: 34px; color: var(--accent); flex: none; }
    .brand h1 { margin: 0; font-size: 22px; letter-spacing: .4px; font-weight: 700; }
    .brand h1 span { color: var(--accent); }
    .brand p { margin: 2px 0 0; font-size: 12px; color: var(--muted); }

    .sidebar {
      background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
      box-shadow: 0 18px 44px rgba(0,0,0,.35); display: flex; flex-direction: column; overflow: hidden;
    }
    .sidebar .filters { padding: 20px 22px; display: flex; flex-direction: column; gap: 16px; }
    .field label { display: block; margin-bottom: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: .8px; color: var(--muted); font-weight: 600; }
    .field select { width: 100%; background: var(--bg-soft); border: 1px solid var(--line); color: var(--ink); border-radius: 8px; padding: 11px 13px; font: inherit; transition: border-color .15s; }
    .field select:focus { outline: none; border-color: var(--accent); }
    .hint { font-size: 12px; color: var(--muted); padding: 0 22px 22px; }
    .hint code { font-family: var(--mono); color: var(--accent); }

    .chat { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; box-shadow: 0 18px 44px rgba(0,0,0,.35); display: flex; flex-direction: column; min-height: 0; }
    .chat header { padding: 18px 22px; border-bottom: 1px solid var(--line); display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
    .chat header h2 { margin: 0; font-size: 18px; font-weight: 650; }
    .chat header .status { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--muted); }
    .chat header .status .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 0 3px rgba(52,199,123,.18); }

    #messages { flex: 1; overflow-y: auto; padding: 22px; display: flex; flex-direction: column; gap: 14px; }
    .empty { color: var(--muted); text-align: center; margin: auto; max-width: 360px; }
    .empty .glyph { font-size: 40px; display: block; margin-bottom: 10px; }

    .message { max-width: 82%; padding: 13px 16px; border-radius: 12px; white-space: pre-wrap; overflow-wrap: break-word; }
    .message.user { align-self: flex-end; background: var(--panel-2); border: 1px solid var(--line); }
    .message.assistant { align-self: flex-start; background: var(--bg-soft); border: 1px solid var(--line); border-left: 3px solid var(--accent); }
    .message .meta { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .6px; color: var(--steel); margin-bottom: 6px; font-weight: 700; }

    .sources { margin-top: 12px; padding-top: 10px; border-top: 1px dashed var(--line); display: flex; flex-direction: column; gap: 6px; }
    .badge { font-size: 12px; color: var(--accent-2); font-family: var(--mono); }
    .badge.no-evidence { color: var(--warn); }
    .badge.hypothesis { color: var(--accent); }
    .source-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
    .src-link { font-size: 12px; color: var(--accent); text-decoration: none; background: var(--panel-2); border: 1px solid var(--line); border-radius: 6px; padding: 4px 10px; cursor: pointer; transition: border-color .15s, background .15s; }
    .src-link:hover { border-color: var(--accent); background: var(--bg-soft); }

    .modal { display: none; position: fixed; inset: 0; background: rgba(6,9,12,.82); z-index: 50; align-items: center; justify-content: center; padding: 24px; }
    .modal.open { display: flex; }
    .modal .modal-body { position: relative; max-width: min(900px, 100%); max-height: 100%; }
    .modal img { display: block; max-width: 100%; max-height: 88vh; border-radius: 8px; border: 1px solid var(--line); box-shadow: 0 24px 64px rgba(0,0,0,.6); }
    .modal .modal-close { position: absolute; top: -38px; right: 0; background: none; border: 1px solid var(--line); color: var(--ink); width: 34px; height: 34px; border-radius: 8px; cursor: pointer; font-size: 18px; line-height: 1; }
    .modal .modal-close:hover { border-color: var(--accent); color: var(--accent); }
    .modal .modal-caption { color: var(--muted); font-size: 12px; margin-top: 8px; text-align: center; font-family: var(--mono); }

    .composer { display: flex; gap: 10px; padding: 16px; border-top: 1px solid var(--line); align-items: flex-end; }
    .composer textarea { flex: 1; min-height: 46px; max-height: 160px; resize: vertical; background: var(--bg-soft); border: 1px solid var(--line); color: var(--ink); border-radius: 10px; padding: 12px 14px; font: inherit; }
    .composer textarea:focus { outline: none; border-color: var(--accent); }
    .composer button { border: 0; cursor: pointer; background: var(--accent); color: #17120a; font-weight: 700; border-radius: 10px; padding: 0 20px; height: 46px; transition: background .15s, transform .05s; }
    .composer button:hover { background: var(--accent-2); }
    .composer button:disabled { background: var(--steel); color: #d7dde1; cursor: not-allowed; }
    .composer button:active { transform: translateY(1px); }

    .typing { color: var(--muted); font-style: italic; }

    @media (max-width: 760px) {
      .app { grid-template-columns: 1fr; padding: 12px; gap: 12px; }
      .chat { min-height: 70vh; }
      .message { max-width: 94%; }
    }
  </style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <svg class="mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M13 2 4.5 13.5a2 2 0 0 0 6 3L19 8"/>
        <path d="m15 8 3 3"/>
        <path d="M17 3l4 4"/>
        <path d="M4 20h4"/>
      </svg>
      <div><h1>Torque<span>AI</span></h1><p>Assistente de oficina</p></div>
    </div>
    <div class="filters">
      <div class="field">
        <label for="generation">Geração</label>
        <select id="generation"><option value="">Todos os veículos</option></select>
      </div>
      <div class="field">
        <label for="system">Sistema</label>
        <select id="system"><option value="">Todos os sistemas</option></select>
      </div>
    </div>
    <p class="hint">Escolha o veículo e o sistema para refinar a busca. Deixe em "Todos" para pesquisar em todos os manuais.</p>
  </aside>

  <section class="chat" aria-label="Bate-papo do assistente">
    <header>
      <h2>Consulta técnica</h2>
      <div class="status"><span class="dot"></span> Manuais indexados</div>
    </header>
    <div id="messages" aria-live="polite">
      <div class="empty"><span class="glyph">🔧</span>Sua primeira pergunta começa aqui.<br>Procedimentos, componentes, torques e DTCs.</div>
    </div>
    <form class="composer" id="form">
      <textarea id="question" required minlength="3" placeholder="Descreva sua dúvida..." aria-label="Pergunta"></textarea>
      <button type="submit">Enviar</button>
    </form>
  </section>
</div>
<script>
const form = document.querySelector('#form');
const messages = document.querySelector('#messages');
let sessionId;

function addMessage(role, content, citations = [], grounded = null) {
  const empty = document.querySelector('.empty');
  if (empty) empty.remove();
  const item = document.createElement('article');
  item.className = 'message ' + role;

  const meta = document.createElement('span');
  meta.className = 'meta';
  meta.textContent = role === 'user' ? 'Você' : 'TorqueAI';
  item.append(meta);

  const body = document.createElement('div');
  body.textContent = content;
  item.append(body);

  if (role === 'assistant') {
    const sources = document.createElement('div');
    sources.className = 'sources';
    let badge = document.createElement('span');
    badge.className = 'badge';
    if (grounded === false) {
      badge.textContent = '⚠ Sem evidência suficiente nos manuais indexados.';
      badge.classList.add('no-evidence');
    } else if (/hip[oó]tese/i.test(content)) {
      badge.textContent = '⚠ Hipótese diagnóstica — requer verificação.';
      badge.classList.add('hypothesis');
    } else {
      badge.textContent = '✓ Evidência do manual — ' + citations.map(c => `${c.document_title}, ${c.chapter}, p. ${c.page_number}`).join(' | ');
    }
    sources.append(badge);

    if (citations && citations.length) {
      const links = document.createElement('div');
      links.className = 'source-links';
      citations.forEach(c => {
        if (!c.document_id || !c.page_number) return;
        const a = document.createElement('a');
        a.className = 'src-link';
        a.href = '#';
        a.textContent = `${c.chapter} · p. ${c.page_number}`;
        a.title = `${c.document_title} — página ${c.page_number}`;
        a.addEventListener('click', ev => {
          ev.preventDefault();
          openModal(
            `/api/v1/documents/${c.document_id}/page/${c.page_number}/thumbnail`,
            `${c.document_title} — ${c.chapter} · p. ${c.page_number}`
          );
        });
        links.append(a);
      });
      sources.append(links);
    }
    item.append(sources);
  }
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
}

function openModal(src, caption) {
  const modal = document.querySelector('#modal');
  const img = modal.querySelector('img');
  const cap = modal.querySelector('.modal-caption');
  img.src = src;
  img.alt = caption;
  cap.textContent = caption;
  modal.classList.add('open');
}

function closeModal() {
  const modal = document.querySelector('#modal');
  modal.classList.remove('open');
  modal.querySelector('img').src = '';
}

async function loadPickerOptions() {
  const genSelect = document.querySelector('#generation');
  const sysSelect = document.querySelector('#system');
  try {
    const response = await fetch('/api/v1/vehicles/picker');
    if (!response.ok) return;
    const data = await response.json();
    (data.generations || []).forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.code;
      opt.textContent = `${g.brand} ${g.model} — ${g.code}`;
      genSelect.append(opt);
    });
    (data.systems || []).forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      sysSelect.append(opt);
    });
  } catch (e) {
    /* keep default "Todos" options if picker fails */
  }
}
loadPickerOptions();

form.addEventListener('submit', async event => {
  event.preventDefault();
  const input = document.querySelector('#question');
  const question = input.value.trim();
  if (!question) return;
  addMessage('user', question);
  input.value = '';
  const button = form.querySelector('button');
  button.disabled = true;
  button.textContent = 'Consultando…';
  try {
    const response = await fetch('/api/v1/chat/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        question,
        generation_code: document.querySelector('#generation').value || null,
        system: document.querySelector('#system').value || null
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Falha ao consultar os manuais');
    sessionId = data.session_id;
    addMessage('assistant', data.answer, data.citations, data.grounded);
  } catch (error) {
    input.value = question;
    addMessage('assistant', error.message, [], false);
  } finally {
    button.disabled = false;
    button.textContent = 'Enviar';
  }
});

const modal = document.querySelector('#modal');
modal.querySelector('.modal-close').addEventListener('click', closeModal);
modal.addEventListener('click', ev => { if (ev.target === modal) closeModal(); });
document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeModal(); });
</script>
<div class="modal" id="modal" role="dialog" aria-modal="true" aria-label="Fonte do manual">
  <div class="modal-body">
    <button class="modal-close" aria-label="Fechar">&times;</button>
    <img alt="Página do manual">
    <div class="modal-caption"></div>
  </div>
</div>
</body></html>"""