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
  <title>helpMec | Assistente tecnico</title>
  <style>
    :root { --ink:#19242b; --muted:#65737b; --line:#d8e1df; --paper:#f6f8f5; --accent:#d85d32; --accent-dark:#a63d20; --panel:#fff; }
    * { box-sizing:border-box; } body { margin:0; color:var(--ink); background:linear-gradient(135deg,#eef4f0,#f8f3eb); font:16px Georgia,serif; }
    main { max-width:1100px; min-height:100vh; margin:auto; padding:30px 22px; display:grid; grid-template-columns:260px 1fr; gap:22px; }
    aside, .chat { background:var(--panel); border:1px solid var(--line); box-shadow:0 12px 32px #26352b12; } aside { padding:24px; } h1 { margin:0 0 8px; font-size:28px; } p { color:var(--muted); line-height:1.45; }
    label { display:block; margin:20px 0 7px; color:var(--muted); font:12px Arial,sans-serif; letter-spacing:0; text-transform:uppercase; } select, textarea, button { width:100%; border:1px solid var(--line); padding:12px; font:inherit; } select, textarea { background:var(--paper); } button { border:0; color:white; background:var(--accent); cursor:pointer; } button:hover { background:var(--accent-dark); }
    .chat { display:flex; min-height:650px; flex-direction:column; } header { padding:24px 28px; border-bottom:1px solid var(--line); } header h2 { margin:0; font-size:24px; } #messages { flex:1; overflow:auto; padding:28px; } .message { max-width:82%; margin:0 0 18px; padding:15px 17px; white-space:pre-wrap; line-height:1.5; } .assistant { background:var(--paper); border-left:4px solid var(--accent); } .user { margin-left:auto; color:white; background:var(--ink); } .sources { margin-top:12px; color:var(--muted); font:13px Arial,sans-serif; } .composer { display:flex; gap:10px; padding:18px; border-top:1px solid var(--line); } textarea { min-height:48px; resize:vertical; } .composer button { width:110px; align-self:flex-end; } .empty { color:var(--muted); text-align:center; margin-top:20%; }
    @media (max-width:720px) { main { display:block; padding:12px; } aside { margin-bottom:12px; } .chat { min-height:75vh; } .message { max-width:94%; } }
  </style>
</head>
<body>
<main>
  <aside><h1>helpMec</h1><p>Respostas tecnicas baseadas nos manuais indexados.</p>
    <label for="generation">Geracao</label><input id="generation" placeholder="Ex.: R56">
    <label for="system">Sistema</label><input id="system" placeholder="Ex.: steering">
  </aside>
  <section class="chat"><header><h2>Assistente de oficina</h2><p>Pergunte sobre procedimentos, componentes ou DTCs.</p></header>
    <div id="messages"><div class="empty">A sua primeira pergunta começa aqui.</div></div>
    <form class="composer" id="form"><textarea id="question" required minlength="3" placeholder="Descreva sua dúvida..."></textarea><button type="submit">Enviar</button></form>
  </section>
</main>
<script>
const form=document.querySelector('#form'), messages=document.querySelector('#messages'); let sessionId;
function addMessage(role, content, citations=[], grounded=null) { const empty=document.querySelector('.empty'); if(empty) empty.remove(); const item=document.createElement('article'); item.className='message '+role; item.textContent=content; if(role==='assistant'){ const sources=document.createElement('div'); sources.className='sources'; sources.textContent=grounded===false ? 'Sem evidencia suficiente nos manuais indexados.' : /hip[oó]tese/i.test(content) ? 'Hipotese diagnostica: requer verificacao.' : 'Evidencia do manual: '+citations.map(c=>`${c.document_title}, ${c.chapter}, p. ${c.page_number}`).join(' | '); item.append(sources); } messages.append(item); messages.scrollTop=messages.scrollHeight; }
form.addEventListener('submit', async event => { event.preventDefault(); const input=document.querySelector('#question'); const question=input.value.trim(); if(!question) return; addMessage('user',question); input.value=''; const button=form.querySelector('button'); button.disabled=true; button.textContent='Consultando...'; try { const response=await fetch('/api/v1/chat/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,question,generation_code:document.querySelector('#generation').value||null,system:document.querySelector('#system').value||null})}); const data=await response.json(); if(!response.ok) throw new Error(data.detail||'Falha ao consultar os manuais'); sessionId=data.session_id; addMessage('assistant',data.answer,data.citations,data.grounded); } catch(error) { input.value=question; addMessage('assistant',error.message,[],false); } finally { button.disabled=false; button.textContent='Enviar'; } });
</script>
</body></html>"""
