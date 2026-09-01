# CLAUDE.md

Este arquivo dá contexto ao Claude Code sobre o projeto **Layer**. Leia por
completo antes de gerar qualquer código.

## Visão geral do projeto

App **local-first** (sem backend hospedado, sem nuvem, sem API paga) para
quem coleciona perfumes de nicho: cataloga a coleção, sugere combinações de
**layering** (aplicar duas fragrâncias juntas) com base em regras reais de
perfumaria, mantém um diário de uso e mostra visualizações da coleção.
Interface em Streamlit, banco SQLite local (`layer.db`).

**Fase atual:** MVP funcional (coleção, sugestor, diário, visualizações,
alertas de estoque, sugestão sazonal). Falta só a integração opcional com a
API da Anthropic — ver "Dívidas técnicas / fase 2" abaixo.

## Stack

- Python 3.11+, tipagem estrita (`from __future__ import annotations`,
  type hints em toda função pública)
- SQLite via SQLAlchemy 2.x (`layer.db`, arquivo local)
- Streamlit (UI, multi-page em `layer/ui/pages/`)
- Pydantic v2 (schemas de validação/serialização — `FragranceRead`,
  `FragranceCreate`, `FragranceUpdate`)
- Pandas (import/export CSV), Plotly (gráficos), Pytest (testes)

Tudo roda localmente. Sem dependência de rede em tempo de execução — isso é
uma decisão de produto, não só técnica (ver "O que não fazer" abaixo).

## Decisões de arquitetura já tomadas

- **Domínio puro** (`layer/domain/`): não importa SQLAlchemy nem Streamlit,
  opera só sobre schemas Pydantic (`FragranceRead`). É por isso que
  `compatibility.py` é testável sem banco nem UI — não quebre esse
  isolamento importando `layer.models` ou `layer.db` de dentro de
  `layer/domain/`.
- **Serviços fazem a ponte** (`layer/services/`): recebem uma `Session` do
  SQLAlchemy, leem/escrevem `layer.models.Fragrance`, convertem de/para os
  schemas Pydantic que o domínio entende. Toda regra de negócio fica no
  domínio, não nos serviços — serviço é CRUD + tradução, nada mais.
  Exemplo: `low_stock_fragrances()` só filtra por `ml_remaining`, não decide
  o que fazer com o resultado — quem decide é a UI.
- **UI só chama serviços** (`layer/ui/`): nunca acessa `layer.db` ou
  `layer.models` diretamente, nunca importa `layer/domain/` sem passar por
  um serviço primeiro.
- **O motor de compatibilidade nunca bloqueia uma combinação.** Mesmo pares
  "arriscados" (score baixo) são retornados, só sinalizados como
  experimentais (`is_experimental=True`). Isso é intencional — o app avisa,
  o usuário decide. Qualquer feature nova de scoring deve seguir esse
  princípio: penalizar no score, não impedir de sugerir.
- **Score é sempre um inteiro 0–100**, ajustado em camadas por
  `evaluate_pair()` (`_intensity_adjustment`, `_season_adjustment`,
  `_concentration_adjustment`, `_sweet_clash_adjustment`, e depois os vieses
  de intenção/ocasião em `suggest_from_scratch`). Cada ajuste é uma função
  isolada e documentada com a *regra de perfumaria* por trás dele — ao
  adicionar um novo ajuste, siga o padrão: função pequena, docstring
  explicando o porquê olfativo, e sempre `max(0, min(100, score))` no final.
- **Papel líder/modificador é determinístico** (`assign_roles()`): decidido
  por intensidade → concentração → notas de fundo → id (desempate estável).
  Não introduza aleatoriedade aqui — os testes dependem de resultado
  reproduzível.
- **Matriz de famílias olfativas é dado, não texto solto**
  (`layer/domain/families.py`) — é isso que permite testar
  `get_family_pair_rule()` sem parsing de string. Nova combinação de
  famílias entra como entrada na matriz, não como `if/elif`.

## Convenções de código

- Type hints em tudo; `from __future__ import annotations` no topo de cada
  módulo novo.
- Dataclasses de domínio usam `@dataclass(slots=True)`.
- Docstrings em português, focadas no **porquê** da regra de negócio (a
  lógica de perfumaria por trás do ajuste de score), não em repetir o que o
  código já deixa óbvio.
- Nomes de funções/variáveis em inglês; textos voltados ao usuário
  (`rationale`, mensagens de UI) em português.
- Funções privadas de ajuste de score prefixadas com `_` e vivem em
  `layer/domain/compatibility.py` perto de `evaluate_pair`.

## Dívidas técnicas / fase 2

- **Alertas de reposição de estoque** — implementado.
  `fragrance_service.low_stock_fragrances()` alimenta a seção "Estoque
  baixo" da home (`layer/ui/app.py`) e a coluna "Estoque" da tabela em
  `layer/ui/pages/1_colecao.py`. Threshold fixo em 15ml em ambos os
  lugares — se isso virar configurável, centralize o valor em vez de
  duplicar o número.
- **Sugestão sazonal automática** — implementado.
  `layer.domain.compatibility.suggest_for_season()` prioriza pares cuja
  `best_season` bate com `current_season()`, com fallback pro ranking geral
  se nada bater. Exposto via `combo_service.get_seasonal_suggestions()` na
  home, reusando `layer.ui.components.render_suggestion_card` (o mesmo
  componente da página Sugestor — não duplique a renderização de card de
  sugestão, estenda `components.py`).
- **Integração com API da Anthropic** para gerar descrições mais literárias
  no lugar do `rationale` baseado em regras: mencionada no README como
  possibilidade futura, sem código ainda. É a única pendência que rompe a
  promessa "local-first, sem API paga" — não implementar sem alinhar antes
  se isso ainda é o que o produto quer.

## O que não fazer

- Não fazer scraping de sites como Fragrantica (viola termos de uso deles)
  — cadastro de fragrância é manual ou via CSV/JSON.
- Não adicionar dependência de rede em tempo de execução sem decisão
  explícita — o app é local-first por design, não por acidente.
- Não deixar o motor de compatibilidade bloquear uma sugestão — penalizar
  no score, nunca omitir o par.
- Não importar SQLAlchemy/Streamlit dentro de `layer/domain/`.

## Onde mexer em quê

- Regras de layering (score, papel líder/modificador, textos de
  combinação): `layer/domain/compatibility.py` e `layer/domain/families.py`.
- Regras de estação: `layer/domain/seasons.py`.
- CRUD e queries: `layer/services/*.py` (um arquivo por entidade/fluxo:
  `fragrance_service`, `combo_service`, `journal_service`,
  `importexport_service`).
- Páginas e navegação: `layer/ui/app.py` (entrypoint) e `layer/ui/pages/`
  (uma página por número de ordem no menu lateral). Componentes Streamlit
  reusados por mais de uma página (ex.: card de sugestão) vivem em
  `layer/ui/components.py`.
- Schemas de validação/serialização: `layer/schemas.py`. Modelos de banco:
  `layer/models.py`.

## Comandos

```bash
pip install -r requirements.txt   # instalar dependências
python seed_data.py               # popular o banco com ~20 perfumes de nicho reais
streamlit run layer/ui/app.py     # subir o app (cria layer.db automaticamente)
pytest                            # rodar os testes (compatibility.py + services, com SQLite em memória)
```

Mais contexto de produto, instalação e estrutura completa de pastas em
[README.md](./README.md).
