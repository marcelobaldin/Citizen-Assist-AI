# Citizen Assist AI — Assistente Digital de Orientacao ao Cidadao

**Global Solution 2o Semestre — FIAP Ciencias da Computacao**

## Integrantes

| Nome | RM |
|------|-----|
| Marcelo Bastianello Baldin | RM568746 |

**Grupo 4**

---

## Descricao do Problema

Muitos cidadaos brasileiros enfrentam dificuldades para acessar informacoes sobre servicos publicos, documentacao e direitos. A linguagem burocratica dos sites oficiais, a dispersao das informacoes em diversos orgaos e a falta de familiaridade com ferramentas digitais criam barreiras significativas.

O **Citizen Assist AI** e um assistente digital que orienta o cidadao de forma clara e acessivel sobre como acessar servicos, tirar documentos e exercer seus direitos — sempre citando fontes oficiais e alertando sobre suas limitacoes.

## Publico-Alvo

- Cidadaos brasileiros que precisam de orientacao sobre servicos publicos
- Pessoas com dificuldade de navegar sites governamentais
- Estudantes e profissionais que precisam de informacoes rapidas sobre documentacao

## Temas Cobertos

1. **Documentacao** — CPF, RG/CIN, CNH, passaporte, certidao de nascimento, titulo de eleitor
2. **Servicos Publicos** — SUS, INSS, Bolsa Familia, CadUnico, Farmacia Popular, Tarifa Social
3. **Orientacoes Comunitarias** — Procon, direitos do inquilino, MEI, seguro-desemprego, Defensoria Publica

---

## Organizacao da Base de Conhecimento

A base de conhecimento esta em `data/base_conhecimento.json` com 17 registros verificados. Cada registro contem:

```json
{
  "id": 1,
  "tema": "Documentacao",
  "palavras_chave": ["CPF", "cadastro pessoa fisica", ...],
  "pergunta": "Como tirar o CPF?",
  "orientacao": "Texto completo da orientacao...",
  "referencia": "Receita Federal — https://www.gov.br/...",
  "data_verificacao": "2026-10-01",
  "topicos_relacionados": [2, 3]
}
```

Todas as informacoes foram verificadas em fontes oficiais (.gov.br) e cada registro inclui a data da ultima verificacao.

## Estruturas de Dados Utilizadas

| Estrutura | Uso no Sistema |
|-----------|---------------|
| **Dicionario (hash)** | Indice de temas para acesso O(1) por categoria |
| **Lista** | Armazenamento ordenado de registros e resultados de busca |
| **Grafo (lista de adjacencia)** | Relacionamentos entre topicos para navegacao contextual |
| **Pilha (lista)** | Historico de consultas com operacao de desfazer (LIFO) |
| **Fila (deque)** | Fila de atendimento de consultas (FIFO) |

## Estrategia de Busca

O algoritmo de busca utiliza **scoring por palavras-chave** com pesos diferenciados:

1. **Palavras-chave do registro** (peso 3.0) — correspondencia com termos catalogados
2. **Titulo/pergunta** (peso 2.0) — correspondencia com o enunciado da pergunta
3. **Texto da orientacao** (peso 0.5) — correspondencia com o corpo da resposta

O score final e normalizado entre 0 e 1. Resultados com score abaixo de 15% sao descartados. O sistema inclui normalizacao de texto (remocao de acentos, case insensitive).

## Estrategias de Resposta (Prompt Strategies)

O sistema implementa **dois modelos de resposta** que o usuario pode alternar:

### Modelo 1 — Conciso
- Resposta direta em ate 300 caracteres
- Foco nos pontos essenciais
- Inclui fonte oficial
- Ideal para consultas rapidas

### Modelo 2 — Detalhado (padrao)
- Resposta completa com cabecalho informativo
- Tema e palavras-chave visiveis
- Texto integral da orientacao
- Fonte oficial e data de verificacao
- Ideal para quem precisa do passo a passo completo

**Comparacao:** O modo conciso e mais rapido de ler mas pode omitir detalhes importantes. O modo detalhado garante que nenhuma informacao se perca, porem exige mais leitura. A escolha fica com o usuario conforme sua necessidade.

## Tratamento de Limitacoes

- **Consulta sem resultado:** Mensagem clara + sugestoes de termos + indicacao dos temas cobertos
- **Consulta ambigua:** Lista de opcoes para o usuario escolher a mais adequada
- **Entrada vazia:** Mensagem de erro amigavel, sem travamento
- **Entrada sem sentido:** Tratamento identico a consulta sem resultado
- **Tema fora do escopo:** Aviso explicito de que o assunto nao esta na base

---

## Plano de Testes

O arquivo `data/perguntas_teste.json` contem 15 perguntas de teste organizadas em 4 categorias:

| Categoria | Quantidade | Descricao |
|-----------|-----------|-----------|
| Direta | 4 | Perguntas que correspondem exatamente a base |
| Reformulada | 5 | Mesma intencao com palavras diferentes |
| Fora do escopo | 2 | Temas nao cobertos pela base |
| Caso limite | 4 | Entrada vazia, sem sentido, ambigua |

### Metricas Calculadas

- **Taxa de acerto:** Percentual de perguntas que retornaram o ID esperado
- **Tempo medio de resposta:** Media do tempo de processamento de cada busca
- **Tempo maximo:** Pior caso de tempo de resposta

### Resultados

Os resultados completos sao salvos em `tests/resultados_testes.json` ao executar a opcao 5 do menu. O relatorio inclui:
- Resultado individual de cada teste
- Metricas agregadas
- Interpretacao dos resultados
- Sugestoes de melhorias
- Limitacoes da avaliacao
- Roteiro de teste de usabilidade

---

## Como Executar

### Requisitos
- Python 3.8 ou superior (testado com Python 3.13)
- Nenhuma dependencia externa necessaria (usa apenas bibliotecas padrao)

### Execucao

```bash
cd GLOBAL_SOLUTION_2o_SEMESTRE
python src/sistema.py
```

### Menu Principal

```
===== MENU PRINCIPAL =====
  [1] Navegar por temas
  [2] Buscar por texto
  [3] Modo de resposta (atual: detalhado)
  [4] Historico de consultas (0)
  [5] Executar testes automatizados
  [0] Sair
```

---

## Exemplos de Uso

### Exemplo 1 — Busca direta (modo detalhado)

**Entrada:** "Como tirar o CPF?"

**Saida:**
```
============================================================
ORIENTACAO: Como tirar o CPF?
============================================================
Tema: Documentacao
Palavras-chave: CPF, cadastro pessoa fisica, receita federal, documento, numero CPF
------------------------------------------------------------

INFORMACAO COMPLETA:
O CPF pode ser emitido gratuitamente pela internet no site da Receita
Federal (servicos.receita.fazenda.gov.br), em agencias do Banco do Brasil,
Caixa Economica Federal ou Correios. [...]

------------------------------------------------------------
Fonte oficial: Receita Federal — https://www.gov.br/receitafederal/pt-br/assuntos/meu-cpf
Data de verificacao: 2026-10-01
============================================================
```

### Exemplo 2 — Busca reformulada

**Entrada:** "Preciso de remedio de graca, onde consigo?"

**Saida:** Retorna informacoes sobre o programa Farmacia Popular com fonte do Ministerio da Saude.

### Exemplo 3 — Entrada invalida

**Entrada:** "" (vazia)

**Saida:**
```
Entrada vazia. Retornando ao menu.
```

### Exemplo 4 — Tema fora do escopo

**Entrada:** "Como declarar o imposto de renda?"

**Saida:**
```
Nenhum resultado encontrado para: 'Como declarar o imposto de renda?'
Sugestoes:
  - Tente usar palavras-chave mais especificas (ex: 'CPF', 'SUS', 'MEI')
  - Navegue pelos temas no menu principal
  - Lembre-se: cobrimos Documentacao, Servicos Publicos e Orientacoes Comunitarias

AVISO: Este sistema e apenas um prototipo educacional [...]
```

---

## Privacidade e Acessibilidade

- **Nenhum dado pessoal e coletado.** O sistema nao pede nome, CPF, endereco ou qualquer informacao do usuario.
- **Nenhuma informacao e armazenada** alem da sessao atual (historico apenas em memoria).
- **Interface em texto** acessivel a leitores de tela e terminais simples.
- **Linguagem clara** sem jargao tecnico nas orientacoes.

## Aviso Legal

Este sistema e um **prototipo educacional** desenvolvido como projeto academico da FIAP. **NAO e um canal oficial do governo** e nao substitui a consulta direta aos orgaos competentes. As informacoes podem estar desatualizadas. Sempre verifique nos sites oficiais (.gov.br).

---

## Video de Apresentacao

Link do video: *(a ser adicionado apos gravacao)*

---

## Conclusoes

O Citizen Assist AI demonstra que e possivel construir um assistente funcional de orientacao ao cidadao usando apenas Python e estruturas de dados fundamentais, sem dependencia de APIs pagas ou frameworks complexos. O sistema prioriza a confiabilidade das informacoes (fontes verificadas) e a transparencia (citacao de fontes em toda resposta).

### Limitacoes

- Base de conhecimento limitada a 17 registros em 3 temas
- Busca por palavras-chave sem processamento de linguagem natural avancado
- Nao lida com contexto conversacional (cada busca e independente)
- Informacoes podem ficar desatualizadas com mudancas em politicas publicas

### Melhorias Futuras

- Expansao da base de conhecimento com mais temas (educacao, transporte, habitacao)
- Implementacao de NLP com stemming/lematizacao para melhor correspondencia
- Interface web para maior acessibilidade
- Sistema de atualizacao automatica da base via scraping de sites oficiais
- Suporte a multiplos idiomas para imigrantes

---

## Estrutura do Repositorio

```
GLOBAL_SOLUTION_2o_SEMESTRE/
├── README.md                        # Este arquivo
├── src/
│   └── sistema.py                   # Codigo principal do sistema
├── data/
│   ├── base_conhecimento.json       # Base de conhecimento (17 registros)
│   └── perguntas_teste.json         # Conjunto de testes (15 perguntas)
├── tests/
│   └── resultados_testes.json       # Resultados dos testes (gerado automaticamente)
└── docs/
    └── uso_ia.md                    # Documentacao do uso de IA no desenvolvimento
```
