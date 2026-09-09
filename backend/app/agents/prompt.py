from __future__ import annotations

from typing import Any, Dict, Iterable, List

SYSTEM_PROMPT = """Voce e o assistente tecnico helpMec.
Use SOMENTE as fontes do manual fornecidas no contexto para responder.
Nao invente torques, especificacoes, procedimentos, codigos DTC ou referencias.
Cite as fontes no formato [Fonte N] ao fazer afirmacoes tecnicas.
Separe fatos confirmados pelo manual de hipoteses diagnosticas.
Se o contexto nao trouxer evidencia suficiente, diga explicitamente que nao e possivel confirmar a resposta nos manuais.
Nao use conhecimento externo como se fosse uma informacao do fabricante.
Responda no mesmo idioma da pergunta do usuario, mesmo quando as fontes estiverem em ingles.
Quando traduzir uma fonte, preserve fielmente o significado tecnico e mantenha a referencia ao trecho original.
"""


def build_grounded_messages(
    question: str,
    results: Iterable[Any],
    history: Iterable[Dict[str, str]] = (),
) -> List[Dict[str, str]]:
    sources = []
    for index, result in enumerate(results, start=1):
        payload = getattr(result, "payload", {}) or {}
        text = str(payload.get("text", "")).strip()
        if not text:
            continue
        sources.append(
            "[Fonte {index}] {title} | secao: {section} | pagina: {page} | sistema: {system}\n{text}".format(
                index=index,
                title=payload.get("document_title", "Manual tecnico"),
                section=payload.get("section_title", "Nao informado"),
                page=payload.get("page_number", "Nao informado"),
                system=payload.get("system", "general"),
                text=text,
            )
        )

    context = "\n\n---\n\n".join(sources)
    user_content = (
        "CONTEXTO DOS MANUAIS (unica fonte autorizada):\n"
        f"{context}\n\n"
        "PERGUNTA DO USUARIO:\n"
        f"{question}"
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(list(history)[-6:])
    messages.append({"role": "user", "content": user_content})
    return messages
