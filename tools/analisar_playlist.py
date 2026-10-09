"""Analisa os vídeos de uma playlist do YouTube com o Gemini e salva um .md por vídeo.

Uso:
    python tools/analisar_playlist.py            # processa os vídeos pendentes
    python tools/analisar_playlist.py --force    # reprocessa tudo

Requer a variável de ambiente GEMINI_API_KEY.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELOS = ["gemini-pro-latest", "gemini-3.8-flash"]  # ordem de preferência; o segundo é fallback em caso de limite

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "analise-bot-externo"

VIDEOS = [
    ("01", "RSdrUMdtPqw", "Configurações Iniciais"),
    ("02", "Vhu78S3iwB0", "Configurações de interface"),
    ("03", "k3lvhw4VARI", "Configuração Aba Áreas"),
    ("04", "VQGRU9IvWRc", "Configurações Aba Configs"),
    ("05", "f81OMjAQd8w", "Configuração Healing"),
    ("06", "_GZeRgii1Bg", "Configuração Target"),
    ("07", "mL7CHH-5fQo", "Funcionamento da aba cavebot"),
    ("08", "UC9nb21wyG0", "Configurando uma hunt"),
    ("09", "EzDTMEyMfDw", "Configurações Aba Catch (Cavebot)"),
    ("10", "GiITAqjwccI", "Funções do Sinapty2"),
    ("11", "jb5CWSavQus", "Configuração do Catch em Shinies"),
]

PROMPT = """Analise este vídeo, que faz parte da playlist "Tutorial Pokemon Aliiance V3" do canal "PokeTibia Bot".
Ele é um tutorial de um bot externo para o jogo OT Pokémon (Poketibia). Título deste vídeo: "{titulo}".

Quero um levantamento técnico e exaustivo, considerando o que é FALADO e o que APARECE NA TELA.

Para cada funcionalidade mostrada, informe:
1. Nome da funcionalidade/aba/módulo
2. O que ela faz e como o usuário configura (todos os campos, opções, checkboxes, sliders, valores padrão visíveis)
3. Como parece funcionar por baixo (leitura de tela/pixel, OCR, leitura de memória, hotkeys, cliques, scripts etc.), deixando claro se é algo DITO no vídeo ou uma INFERÊNCIA sua
4. Limitações, bugs, dicas ou reclamações mencionadas
5. Minutagem (mm:ss) onde aparece

Inclua também: estrutura geral da interface vista neste vídeo, sistema de scripts/waypoints (se houver), formato de arquivos de configuração, requisitos e qualquer detalhe que diferencie esse bot.

Formato da resposta (Markdown, em português):
- "## Resumo" (3 a 5 linhas)
- "## Funcionalidades" (uma subseção ### por funcionalidade, seguindo os itens 1 a 5)
- "## Detalhes de interface"
- "## Observações técnicas e inferências"
Não resuma demais; prefiro excesso de detalhe.
"""


def chamar_gemini(modelo: str, video_id: str, titulo: str, chave: str) -> str:
    corpo = {
        "contents": [{
            "parts": [
                {"file_data": {"file_uri": f"https://www.youtube.com/watch?v={video_id}"}},
                {"text": PROMPT.format(titulo=titulo)},
            ]
        }],
        "generationConfig": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        API_URL.format(model=modelo),
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": chave},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        dados = json.load(resp)

    candidatos = dados.get("candidates") or []
    if not candidatos:
        raise RuntimeError(f"Resposta sem candidatos: {json.dumps(dados)[:500]}")
    partes = candidatos[0].get("content", {}).get("parts", [])
    texto = "".join(p.get("text", "") for p in partes).strip()
    if not texto:
        raise RuntimeError(f"Resposta vazia (finishReason={candidatos[0].get('finishReason')})")
    return texto


def processar(numero: str, video_id: str, titulo: str, chave: str) -> bool:
    nome = re.sub(r"[^\w-]+", "-", titulo.lower()).strip("-")
    destino = SAIDA / f"{numero}-{nome}.md"

    for modelo in MODELOS:
        for tentativa in range(1, 4):
            print(f"[{numero}] {titulo} -> {modelo} (tentativa {tentativa})", flush=True)
            inicio = time.time()
            try:
                texto = chamar_gemini(modelo, video_id, titulo, chave)
            except urllib.error.HTTPError as e:
                detalhe = e.read().decode("utf-8", "replace")[:400]
                print(f"    HTTP {e.code}: {detalhe}", flush=True)
                if e.code >= 500:
                    time.sleep(30 * tentativa)
                    continue
                break  # limite (429) ou modelo indisponível (4xx): passa para o próximo
            except Exception as e:  # timeout, rede, resposta vazia
                print(f"    Erro: {e}", flush=True)
                time.sleep(30 * tentativa)
                continue

            cabecalho = (
                f"# {numero} - {titulo}\n\n"
                f"- Vídeo: https://www.youtube.com/watch?v={video_id}\n"
                f"- Modelo: {modelo}\n\n---\n\n"
            )
            destino.write_text(cabecalho + texto + "\n", encoding="utf-8")
            print(f"    OK em {time.time() - inicio:.0f}s -> {destino.name}", flush=True)
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="reprocessa vídeos já analisados")
    parser.add_argument("--modelo", action="append", help="modelo(s) a usar no lugar da lista padrão")
    args = parser.parse_args()
    if args.modelo:
        MODELOS[:] = args.modelo

    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        print("GEMINI_API_KEY não definida.", file=sys.stderr)
        return 1

    SAIDA.mkdir(parents=True, exist_ok=True)
    falhas = []
    for numero, video_id, titulo in VIDEOS:
        if not args.force and any(SAIDA.glob(f"{numero}-*.md")):
            print(f"[{numero}] já analisado, pulando")
            continue
        if not processar(numero, video_id, titulo, chave):
            falhas.append(f"{numero} - {titulo}")
        time.sleep(5)

    if falhas:
        print("\nFalharam:\n  " + "\n  ".join(falhas))
        return 2
    print("\nTodos os vídeos analisados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
