"""
Citizen Assist AI — Assistente Digital de Orientacao ao Cidadao
Global Solution 2o Semestre — FIAP Ciencias da Computacao
Autor: Marcelo Bastianello Baldin — RM568746
"""

import json
import os
import time
from collections import deque

# ---------- constantes ----------

CAMINHO_BASE = os.path.join(os.path.dirname(__file__), "..", "data", "base_conhecimento.json")
CAMINHO_TESTES = os.path.join(os.path.dirname(__file__), "..", "data", "perguntas_teste.json")
CAMINHO_RESULTADOS = os.path.join(os.path.dirname(__file__), "..", "tests", "resultados_testes.json")

AVISO_NAO_OFICIAL = (
    "AVISO: Este sistema e apenas um prototipo educacional e NAO substitui "
    "canais oficiais do governo. Consulte sempre os sites oficiais (.gov.br) "
    "para informacoes atualizadas."
)

LIMIAR_RELEVANCIA = 0.15

STOPWORDS = {
    "a", "o", "e", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "para", "por", "com", "sem", "como", "que", "qual",
    "quais", "se", "ou", "ao", "aos", "me", "te", "nos", "eu", "ele", "ela", "meu",
    "minha", "seu", "sua", "esse", "essa", "este", "esta", "isso", "isto", "ter",
    "ser", "foi", "sao", "tem", "nao", "mais", "muito", "ja", "ate", "tambem",
    "onde", "quando", "fui", "faco", "quero", "preciso", "posso", "tenho", "algum",
}

# ---------- carregamento e validacao ----------

def carregar_base(caminho):
    """Carrega e valida a base de conhecimento JSON."""
    if not os.path.exists(caminho):
        print(f"[ERRO] Arquivo nao encontrado: {caminho}")
        return []

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERRO] JSON invalido: {e}")
        return []

    if not isinstance(dados, list) or len(dados) == 0:
        print("[ERRO] Base de conhecimento vazia ou formato invalido.")
        return []

    campos_obrigatorios = {"id", "tema", "palavras_chave", "pergunta", "orientacao", "referencia"}
    validos = []
    for registro in dados:
        if campos_obrigatorios.issubset(registro.keys()):
            validos.append(registro)
        else:
            faltando = campos_obrigatorios - set(registro.keys())
            print(f"[AVISO] Registro id={registro.get('id', '?')} ignorado — campos faltando: {faltando}")

    print(f"Base carregada: {len(validos)} registros validos de {len(dados)} total.")
    return validos


# ---------- estruturas de dados ----------

def construir_indice_temas(base):
    """Organiza registros por tema usando dicionario (tabela hash)."""
    indice = {}
    for registro in base:
        tema = registro["tema"]
        if tema not in indice:
            indice[tema] = []
        indice[tema].append(registro)
    return indice


def construir_grafo(base):
    """Constroi grafo de relacionamentos entre topicos (lista de adjacencia)."""
    grafo = {}
    for registro in base:
        rid = registro["id"]
        relacionados = registro.get("topicos_relacionados", [])
        if rid not in grafo:
            grafo[rid] = set()
        for rel in relacionados:
            grafo[rid].add(rel)
            if rel not in grafo:
                grafo[rel] = set()
            grafo[rel].add(rid)
    return grafo


def obter_registro_por_id(base, rid):
    """Busca registro por ID usando dicionario para acesso O(1)."""
    indice_id = {r["id"]: r for r in base}
    return indice_id.get(rid)


# ---------- algoritmo de busca ----------

def normalizar(texto):
    """Remove acentos simplificados e converte para minusculas."""
    texto = texto.lower().strip()
    substituicoes = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u", "ü": "u",
        "ç": "c",
    }
    for original, substituto in substituicoes.items():
        texto = texto.replace(original, substituto)
    return texto


def calcular_relevancia(consulta, registro):
    """Calcula pontuacao de relevancia entre consulta e registro."""
    consulta_norm = normalizar(consulta)
    todas_palavras = consulta_norm.split()
    # filtra stopwords para scoring, mas mantem para contexto
    palavras_consulta = {p for p in todas_palavras if p not in STOPWORDS and len(p) > 1}

    if len(palavras_consulta) == 0:
        return 0.0

    pontuacao = 0.0

    # palavras-chave do registro (peso maior — termos catalogados especificamente)
    for palavra_chave in registro["palavras_chave"]:
        pc_norm = normalizar(palavra_chave)
        pc_palavras = set(pc_norm.split())
        for palavra in palavras_consulta:
            # correspondencia exata com termo da palavra-chave
            if palavra in pc_palavras:
                pontuacao += 5.0
            # correspondencia parcial (substring)
            elif len(palavra) > 3 and palavra in pc_norm:
                pontuacao += 2.0

    # titulo/pergunta do registro
    pergunta_norm = normalizar(registro["pergunta"])
    for palavra in palavras_consulta:
        if len(palavra) > 2 and palavra in pergunta_norm:
            pontuacao += 1.5

    # orientacao do registro (peso menor — texto longo tem muitos falsos positivos)
    orientacao_norm = normalizar(registro["orientacao"])
    for palavra in palavras_consulta:
        if len(palavra) > 4 and palavra in orientacao_norm:
            pontuacao += 0.3

    # normaliza pela quantidade de palavras significativas
    pontuacao_final = pontuacao / (len(palavras_consulta) * 5.0)
    return min(pontuacao_final, 1.0)


def buscar(consulta, base, limite=5):
    """Busca registros relevantes ordenados por pontuacao."""
    if not consulta or not consulta.strip():
        return []

    resultados = []
    for registro in base:
        score = calcular_relevancia(consulta, registro)
        if score >= LIMIAR_RELEVANCIA:
            resultados.append((score, registro))

    resultados.sort(key=lambda x: x[0], reverse=True)
    return resultados[:limite]


# ---------- modelos de resposta (prompt strategies) ----------

def resposta_concisa(registro):
    """Modelo 1 — resposta direta e curta com os pontos essenciais."""
    linhas = [
        f">> {registro['pergunta']}",
        "",
        registro["orientacao"][:300] + ("..." if len(registro["orientacao"]) > 300 else ""),
        "",
        f"Fonte: {registro['referencia']}",
    ]
    return "\n".join(linhas)


def resposta_detalhada(registro):
    """Modelo 2 — resposta completa com contexto, passos e fonte."""
    linhas = [
        "=" * 60,
        f"ORIENTACAO: {registro['pergunta']}",
        "=" * 60,
        f"Tema: {registro['tema']}",
        f"Palavras-chave: {', '.join(registro['palavras_chave'])}",
        "-" * 60,
        "",
        "INFORMACAO COMPLETA:",
        registro["orientacao"],
        "",
        "-" * 60,
        f"Fonte oficial: {registro['referencia']}",
        f"Data de verificacao: {registro.get('data_verificacao', 'nao informada')}",
        "=" * 60,
    ]
    return "\n".join(linhas)


# modo de resposta ativo (pode ser trocado pelo usuario)
modo_resposta_atual = "detalhado"


def formatar_resposta(registro):
    """Aplica o modo de resposta selecionado."""
    if modo_resposta_atual == "conciso":
        return resposta_concisa(registro)
    else:
        return resposta_detalhada(registro)


# ---------- historico de consultas (pilha) ----------

historico_consultas = []


def registrar_consulta(consulta, resultado_id):
    """Empilha consulta no historico (LIFO)."""
    historico_consultas.append({
        "consulta": consulta,
        "resultado_id": resultado_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


def desfazer_ultima_consulta():
    """Remove a ultima consulta do historico (pop da pilha)."""
    if historico_consultas:
        return historico_consultas.pop()
    return None


# ---------- fila de atendimento ----------

fila_atendimento = deque()


def adicionar_fila(consulta):
    """Adiciona consulta a fila de atendimento (FIFO)."""
    fila_atendimento.append(consulta)


def processar_fila():
    """Processa a proxima consulta da fila."""
    if fila_atendimento:
        return fila_atendimento.popleft()
    return None


# ---------- navegacao por grafo ----------

def mostrar_relacionados(registro, base, grafo):
    """Exibe topicos relacionados ao registro atual usando o grafo."""
    rid = registro["id"]
    vizinhos = grafo.get(rid, set())

    if not vizinhos:
        print("\nNenhum topico relacionado encontrado.")
        return

    print("\n--- Topicos Relacionados ---")
    registros_rel = []
    for viz_id in vizinhos:
        reg_viz = obter_registro_por_id(base, viz_id)
        if reg_viz:
            registros_rel.append(reg_viz)
            print(f"  [{reg_viz['id']}] {reg_viz['pergunta']} ({reg_viz['tema']})")

    if registros_rel:
        print("\nDigite o numero do topico para ver, ou 0 para voltar:")
        escolha = input("> ").strip()
        if escolha.isdigit() and int(escolha) > 0:
            escolha_id = int(escolha)
            for reg in registros_rel:
                if reg["id"] == escolha_id:
                    print()
                    print(formatar_resposta(reg))
                    registrar_consulta(reg["pergunta"], reg["id"])
                    mostrar_relacionados(reg, base, grafo)
                    return
            print("Topico nao encontrado entre os relacionados.")


# ---------- menus ----------

def menu_temas(indice_temas, base, grafo):
    """Menu de navegacao hierarquica por temas."""
    temas = list(indice_temas.keys())

    while True:
        print("\n===== TEMAS DISPONIVEIS =====")
        for i, tema in enumerate(temas, 1):
            qtd = len(indice_temas[tema])
            print(f"  [{i}] {tema} ({qtd} topicos)")
        print(f"  [0] Voltar ao menu principal")

        escolha = input("\nEscolha o tema: ").strip()
        if escolha == "0":
            return

        if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(temas):
            print("Opcao invalida. Tente novamente.")
            continue

        tema_selecionado = temas[int(escolha) - 1]
        registros_tema = indice_temas[tema_selecionado]

        while True:
            print(f"\n--- {tema_selecionado} ---")
            for i, reg in enumerate(registros_tema, 1):
                print(f"  [{i}] {reg['pergunta']}")
            print(f"  [0] Voltar aos temas")

            escolha_topico = input("\nEscolha o topico: ").strip()
            if escolha_topico == "0":
                break

            if not escolha_topico.isdigit() or int(escolha_topico) < 1 or int(escolha_topico) > len(registros_tema):
                print("Opcao invalida. Tente novamente.")
                continue

            registro = registros_tema[int(escolha_topico) - 1]
            print()
            print(formatar_resposta(registro))
            registrar_consulta(registro["pergunta"], registro["id"])
            mostrar_relacionados(registro, base, grafo)


def menu_busca(base, grafo):
    """Menu de busca por texto livre."""
    print("\n===== BUSCA POR TEXTO =====")
    print("Digite sua duvida (ou 'voltar' para retornar):")
    consulta = input("> ").strip()

    if consulta.lower() == "voltar" or not consulta:
        if not consulta:
            print("Entrada vazia. Retornando ao menu.")
        return

    inicio = time.time()
    resultados = buscar(consulta, base)
    tempo = time.time() - inicio

    if not resultados:
        print(f"\nNenhum resultado encontrado para: '{consulta}'")
        print("Sugestoes:")
        print("  - Tente usar palavras-chave mais especificas (ex: 'CPF', 'SUS', 'MEI')")
        print("  - Navegue pelos temas no menu principal")
        print("  - Lembre-se: cobrimos Documentacao, Servicos Publicos e Orientacoes Comunitarias")
        print(f"\n{AVISO_NAO_OFICIAL}")
        registrar_consulta(consulta, None)
        return

    if len(resultados) > 1 and resultados[0][0] - resultados[1][0] < 0.1:
        print(f"\nEncontrei {len(resultados)} resultados possiveis (busca em {tempo:.3f}s):")
        print("Sua consulta e um pouco generica. Veja as opcoes:\n")
        for i, (score, reg) in enumerate(resultados, 1):
            print(f"  [{i}] {reg['pergunta']} ({reg['tema']}) — relevancia: {score:.0%}")
        print(f"  [0] Voltar")

        escolha = input("\nEscolha uma opcao: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(resultados):
            _, registro = resultados[int(escolha) - 1]
            print()
            print(formatar_resposta(registro))
            registrar_consulta(consulta, registro["id"])
            mostrar_relacionados(registro, base, grafo)
        return

    # melhor resultado
    score, registro = resultados[0]
    print(f"\nMelhor resultado (relevancia: {score:.0%}, tempo: {tempo:.3f}s):\n")
    print(formatar_resposta(registro))
    registrar_consulta(consulta, registro["id"])

    if len(resultados) > 1:
        print("\nOutros resultados possiveis:")
        for score_r, reg_r in resultados[1:]:
            print(f"  - {reg_r['pergunta']} ({reg_r['tema']}) — {score_r:.0%}")

    mostrar_relacionados(registro, base, grafo)


def menu_modo_resposta():
    """Menu para alternar entre modos de resposta."""
    global modo_resposta_atual
    print(f"\n===== MODO DE RESPOSTA (atual: {modo_resposta_atual}) =====")
    print("  [1] Conciso — resposta curta e direta")
    print("  [2] Detalhado — resposta completa com contexto e passos")
    print("  [0] Voltar")

    escolha = input("\nEscolha: ").strip()
    if escolha == "1":
        modo_resposta_atual = "conciso"
        print("Modo alterado para: CONCISO")
    elif escolha == "2":
        modo_resposta_atual = "detalhado"
        print("Modo alterado para: DETALHADO")


def menu_historico():
    """Exibe historico de consultas (pilha)."""
    if not historico_consultas:
        print("\nNenhuma consulta realizada nesta sessao.")
        return

    print(f"\n===== HISTORICO ({len(historico_consultas)} consultas) =====")
    for i, entrada in enumerate(reversed(historico_consultas), 1):
        resultado = f"-> id {entrada['resultado_id']}" if entrada['resultado_id'] else "-> sem resultado"
        print(f"  {i}. [{entrada['timestamp']}] \"{entrada['consulta']}\" {resultado}")


# ---------- testes automatizados ----------

def executar_testes(base):
    """Executa suite de testes e gera metricas."""
    if not os.path.exists(CAMINHO_TESTES):
        print(f"[ERRO] Arquivo de testes nao encontrado: {CAMINHO_TESTES}")
        return None

    with open(CAMINHO_TESTES, "r", encoding="utf-8") as f:
        perguntas = json.load(f)

    print(f"\nExecutando {len(perguntas)} testes...")
    print("-" * 60)

    resultados = []
    acertos = 0
    tempos = []

    for teste in perguntas:
        pergunta = teste["pergunta"]
        id_esperado = teste["id_esperado"]
        tipo = teste["tipo"]

        inicio = time.time()
        resultado_busca = buscar(pergunta, base)
        tempo = time.time() - inicio
        tempos.append(tempo)

        if resultado_busca:
            id_obtido = resultado_busca[0][1]["id"]
            score = resultado_busca[0][0]
        else:
            id_obtido = None
            score = 0.0

        correto = (id_obtido == id_esperado)
        if correto:
            acertos += 1

        status = "OK" if correto else "FALHA"
        print(f"  [{status}] Teste {teste['id']:2d} ({tipo:16s}): \"{pergunta[:50]}\"")
        if not correto:
            print(f"         Esperado: {id_esperado} | Obtido: {id_obtido} (score: {score:.2f})")

        resultados.append({
            "id_teste": teste["id"],
            "tipo": tipo,
            "pergunta": pergunta,
            "id_esperado": id_esperado,
            "id_obtido": id_obtido,
            "score_relevancia": round(score, 4),
            "correto": correto,
            "tempo_segundos": round(tempo, 6),
            "descricao": teste["descricao"],
        })

    # metricas
    total = len(perguntas)
    taxa_acerto = (acertos / total) * 100 if total > 0 else 0
    tempo_medio = sum(tempos) / len(tempos) if tempos else 0
    tempo_max = max(tempos) if tempos else 0

    metricas = {
        "total_testes": total,
        "acertos": acertos,
        "erros": total - acertos,
        "taxa_acerto_pct": round(taxa_acerto, 2),
        "tempo_medio_seg": round(tempo_medio, 6),
        "tempo_maximo_seg": round(tempo_max, 6),
        "data_execucao": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    relatorio = {
        "metricas": metricas,
        "resultados": resultados,
        "interpretacao": {
            "analise": (
                f"O sistema obteve {taxa_acerto:.1f}% de acerto em {total} testes. "
                f"O tempo medio de resposta foi de {tempo_medio*1000:.2f}ms. "
                "Perguntas diretas tiveram as maiores taxas de acerto, enquanto "
                "reformulacoes e consultas ambiguas representam os principais desafios."
            ),
            "melhorias_sugeridas": [
                "Implementar sinonimos e expansao de consulta para melhorar a correspondencia com reformulacoes",
                "Adicionar processamento de linguagem natural (NLP) com stemming/lematizacao para capturar variacoes morfologicas",
                "Expandir a base de conhecimento com mais temas e perguntas frequentes reais",
            ],
            "limitacoes_avaliacao": (
                "Os testes sao baseados em correspondencia de ID, o que nao captura "
                "a qualidade da orientacao em si. Alem disso, a amostra de 15 perguntas "
                "e pequena para validacao estatistica robusta. Uma avaliacao mais completa "
                "exigiria testes com usuarios reais e metricas de satisfacao."
            ),
        },
        "teste_usabilidade": {
            "roteiro": [
                "Tarefa 1: Encontre informacoes sobre como tirar o CPF usando o menu de temas",
                "Tarefa 2: Use a busca por texto para descobrir como obter medicamentos gratuitos",
                "Tarefa 3: A partir de um resultado, navegue para um topico relacionado",
                "Tarefa 4: Altere o modo de resposta para conciso e faca uma nova consulta",
                "Tarefa 5: Consulte o historico de buscas realizadas na sessao",
            ],
            "criterios_avaliacao": [
                "Tempo para completar cada tarefa",
                "Numero de erros ou tentativas necessarias",
                "Satisfacao do usuario com a resposta obtida (escala 1-5)",
                "Clareza das instrucoes e mensagens do sistema",
            ],
            "observacoes": (
                "O teste de usabilidade deve ser conduzido com pelo menos 3 usuarios "
                "representativos do publico-alvo (cidadaos com diferentes niveis de "
                "familiaridade com tecnologia). Recomenda-se protocolo think-aloud."
            ),
        },
    }

    print("-" * 60)
    print(f"\nRESULTADOS:")
    print(f"  Acertos:      {acertos}/{total} ({taxa_acerto:.1f}%)")
    print(f"  Tempo medio:  {tempo_medio*1000:.2f}ms")
    print(f"  Tempo maximo: {tempo_max*1000:.2f}ms")

    # salva resultados
    os.makedirs(os.path.dirname(CAMINHO_RESULTADOS), exist_ok=True)
    with open(CAMINHO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    print(f"\nResultados salvos em: {CAMINHO_RESULTADOS}")

    return relatorio


# ---------- menu principal ----------

def menu_principal():
    """Loop principal do sistema."""
    print("=" * 60)
    print("  CITIZEN ASSIST AI")
    print("  Assistente Digital de Orientacao ao Cidadao")
    print("=" * 60)
    print()
    print(AVISO_NAO_OFICIAL)
    print()
    print("Este sistema NAO coleta dados pessoais.")
    print("Nenhuma informacao digitada e armazenada alem desta sessao.")
    print()

    # carrega base
    base = carregar_base(CAMINHO_BASE)
    if not base:
        print("Nao foi possivel iniciar o sistema sem a base de conhecimento.")
        return

    # constroi estruturas
    indice_temas = construir_indice_temas(base)
    grafo = construir_grafo(base)

    print(f"Temas disponiveis: {', '.join(indice_temas.keys())}")
    print(f"Relacionamentos no grafo: {sum(len(v) for v in grafo.values()) // 2} conexoes")
    print()

    while True:
        print("\n===== MENU PRINCIPAL =====")
        print("  [1] Navegar por temas")
        print("  [2] Buscar por texto")
        print(f"  [3] Modo de resposta (atual: {modo_resposta_atual})")
        print(f"  [4] Historico de consultas ({len(historico_consultas)})")
        print("  [5] Executar testes automatizados")
        print("  [0] Sair")

        escolha = input("\nEscolha uma opcao: ").strip()

        if escolha == "1":
            menu_temas(indice_temas, base, grafo)
        elif escolha == "2":
            menu_busca(base, grafo)
        elif escolha == "3":
            menu_modo_resposta()
        elif escolha == "4":
            menu_historico()
        elif escolha == "5":
            executar_testes(base)
        elif escolha == "0":
            print("\nObrigado por usar o Citizen Assist AI!")
            print(AVISO_NAO_OFICIAL)
            break
        else:
            print("Opcao invalida. Digite um numero de 0 a 5.")


# ---------- execucao ----------

if __name__ == "__main__":
    menu_principal()
