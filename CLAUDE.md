# CLAUDE.md

Este arquivo dá contexto ao Claude Code sobre o projeto **Layer**. Leia por
completo antes de gerar qualquer código.

## Visão geral do projeto

O Layer é uma plataforma pública de **reviews de perfumes**, nos moldes do
Fragrantica — página de perfume com pirâmide olfativa, accords, ficha
técnica e nota média da comunidade; usuários logados escrevem reviews.

**Princípio de design inegociável, válido em qualquer fase:** nenhum
anúncio e nenhum bloqueio de navegação (ex.: paywall por "muitas páginas
visitadas"). É a principal reclamação da comunidade sobre o concorrente, e
o Layer existe pra ser a alternativa sem isso — nunca adicionar anúncios
ou limites de navegação, mesmo que pareça uma forma óbvia de monetizar.

**Fase atual: MVP (Fase 1) do roteiro de evolução** — catálogo de
perfumes + reviews + autenticação. Fases 2 e 3 estão documentadas em
"Roadmap" abaixo, não implementadas ainda.

### Histórico: pivot de produto

Até este ponto, o Layer era um app **pessoal** (Streamlit + SQLite, um
usuário só, sem login) pra catalogar a própria coleção e sugerir
combinações de layering. Esse código foi preservado em `legacy/` — não
apagado, porque a lógica do motor de compatibilidade
(`legacy/layer/domain/compatibility.py`, `families.py`) é candidata a
virar a base do recomendador da Fase 3 ("se você gosta de X, também pode
gostar de Y"). `legacy/` não faz parte do app atual: não importar de lá
em `catalog/`, `reviews/` ou `accounts/`.

## Stack

- Django 6.x + Postgres (via `dj-database-url` lendo `DATABASE_URL`; sem
  a variável, cai pra SQLite local — não há Postgres instalado nesta
  máquina de dev, então o fallback evita travar em setup de banco)
- `psycopg[binary]` (driver Postgres)
- `python-decouple` pra `.env` (mesmo padrão de `.env.local` que
  finance-app e cstiltility usam)
- Pillow (avatar de perfil via `ImageField`)
- Autenticação: `django.contrib.auth` nativo — sem `django-allauth` no
  MVP, não há OAuth nem verificação de e-mail ainda
- Templates Django server-rendered, CSS mínimo inline (sem framework de
  UI ainda — a Fase 1 prioriza a estrutura de dados e as telas
  funcionando, não o visual)
- `pytest-django` para testes

## Schema (Fase 1)

```
Brand         — name, slug
Accord        — key, label_pt   (família olfativa: amadeirado, cítrico...)
Note          — name            (nota individual: bergamota, baunilha...)

Perfume       — brand (FK), name, slug, launch_year, perfumer,
                concentration (cologne/edt/edp/parfum/extrait), image,
                notes_top/notes_heart/notes_base (M2M Note),
                accords (M2M Accord)

Review        — perfume (FK), user (FK), rating (1-5), text,
                created_at, updated_at
                unique_together (perfume, user) — 1 review por pessoa

Profile       — user (OneToOne), display_name, avatar
                criado automaticamente via signal no post_save de User
```

## Decisões de arquitetura já tomadas

- **Nota média e contagem de votos são calculadas em tempo real**
  (`Perfume.rating_stats`, um `aggregate(Avg, Count)`), não um campo
  cacheado. Dataset pequeno no MVP — não vale a complexidade de manter
  cache sincronizado ainda. Se o ranking "em alta" da Fase 3 pedir mais
  performance, cacheia então (e só então).
- **Reenviar o formulário de review atualiza a review existente**, não
  duplica — o `unique_together (perfume, user)` é a fonte de verdade, e
  `reviews/views.py::create_review` faz `Review.objects.filter(...).first()`
  antes de decidir criar ou atualizar via `ModelForm(instance=...)`.
- **Cadastro de catálogo (Brand/Accord/Note/Perfume) fica pelo Django
  Admin no MVP** — não construir uma tela própria de CRUD de perfume
  ainda, o admin já resolve pra quem cadastra conteúdo.
- **Imagem de perfume é upload manual pelo admin** (`Perfume.image`,
  `null=True, blank=True`) — não existe scraping nem download automático
  de foto de nenhuma fonte externa (mesmo princípio de não fazer scraping
  do Fragrantica). Sem imagem, a lista e a página do perfume mostram um
  placeholder (🌸), nunca um espaço quebrado.
- **Accords reaproveitam as famílias olfativas do motor antigo**
  (rótulos em português de `legacy/layer/domain/families.py`), portados
  pra `catalog/management/commands/seed_perfumes.py::ACCORD_LABELS_PT` —
  evita reinventar a taxonomia de famílias que já existia e era testada.
- **`DATABASE_URL` opcional com fallback SQLite**: não force Postgres
  local. Se for adicionar algo que só funciona em Postgres (ex.: full
  text search nativo), documente isso — hoje o projeto roda 100% em
  SQLite pra dev.

## Convenções de código

- Um app Django por domínio: `catalog` (Brand/Accord/Note/Perfume),
  `reviews` (Review), `accounts` (Profile + auth). Não misturar — uma
  view de review vive em `reviews/views.py`, nunca em `catalog/`.
  `catalog/views.py::perfume_detail` importa `reviews.forms.ReviewForm`
  só pra montar o formulário na página; a criação em si é
  `reviews:create_review`.
- Templates de cada app ficam em `<app>/templates/<app>/*.html`
  (`APP_DIRS=True`), estendendo `templates/base.html`.
- Slugs são gerados automaticamente no `save()` do model
  (`Brand.slug`, `Perfume.slug`) — nunca pedir slug em formulário.
- Migrations sempre commitadas junto com a mudança de model que as gerou
  (não rodar `makemigrations` num commit separado).

## Já implementado além do MVP original

- **Busca e filtro** (`catalog/views.py::perfume_list`) — busca livre por
  nome/marca/nota (`?q=`) via `Q` OR + `icontains` nos três campos de
  notas, e filtro por accord (`?accord=<key>`). Os dois usam `.distinct()`
  porque filtrar por M2M pode duplicar linhas. Estado vazio diferencia
  "nada cadastrado" de "busca sem resultado".
- **Favoritar perfumes + coleção pessoal** (app `favorites`, model
  `Favorite`, `unique_together (user, perfume)`) — o mesmo registro guarda
  as duas coisas: existência da linha = "quero ter" (favorito), campo
  `owned=True` = "tenho" (coleção). Botão de favoritar (cria/apaga a
  linha) e botão separado "📦 Tenho esse perfume" (`toggle_owned`, cria a
  linha com `owned=True` se não existir, senão inverte o campo — nunca
  apaga por engano o "quero ter" de quem já tinha favoritado). Página
  `/favoritos/` ("Minha lista") tem abas Todos/Quero ter/Tenho via
  `?status=`. Decisão deliberada de **não** criar um app/model separado
  pra "coleção" — o roadmap pedia reconexão com o conceito do app antigo
  como feature social, não como produto isolado (sem ml_remaining, sem
  nota pessoal, sem diário — só o flag de posse).
- **Curtir reviews** (`reviews/models.py::ReviewLike`,
  `unique_together (review, user)`) — botão de curtir/descurtir (toggle
  via POST) em cada review na página do perfume, com contagem. O autor
  pode curtir a própria review (sem regra especial pra isso, igual ao
  Fragrantica). `catalog/views.py::perfume_detail` anota `like_count` via
  `Count("likes")` e monta um `set` dos ids de review que o usuário logado
  já curtiu, pra não fazer 1 query por review no template.
- **Atualização de review com histórico** (`reviews/models.py::ReviewUpdate`)
  — a review original (`Review.text`/`Review.rating` no momento da
  criação) nunca é sobrescrita: `reviews:create_review` só cria a
  primeira vez (reenviar não faz nada, é ignorado). Atualizações depois
  de mais tempo de uso passam por `reviews:add_review_update`, que cria
  um `ReviewUpdate` (nota + texto + data) SEM tocar na review original, e
  sincroniza `Review.rating` com a nota mais recente. Esse sync existe
  porque `Perfume.rating_stats` lê `Review.rating` direto num
  `aggregate()` — a média da comunidade deve refletir a opinião atual de
  cada pessoa (a mais recente), não a média das próprias notas de uma
  pessoa ao longo do tempo. Na página do perfume, a review mostra data +
  texto originais, seguidos de cada atualização com sua própria data e
  nota, mais recente por último.
- **Recomendador simples** (`catalog/recommendations.py::similar_perfumes`)
  — seção "Você também pode gostar de" na página do perfume, com até 5
  sugestões. Pontua por sobreposição de accords (peso 3) e notas (peso 1)
  com o perfume atual, sem ML. Calculado em Python sobre querysets
  pré-carregados, não com `annotate`+`Count` em várias relações M2M na
  mesma query (o Django infla contagem ao combinar mais de uma anotação
  M2M assim). **Não reaproveita**
  `legacy/layer/domain/compatibility.py` — aquele motor resolve layering
  (como duas fragrâncias combinam quando usadas juntas, com papel
  líder/modificador), um problema diferente de similaridade de catálogo.
  Escala em O(n) sobre todo o catálogo por view — aceitável com dezenas
  de perfumes; se o catálogo crescer muito, vira candidato a cache ou
  query mais esperta.
- **"Em alta"** (`catalog/trending.py::trending_perfumes`, página
  `/em-alta/`) — ranking dos perfumes com mais reviews + atualizações de
  review + favoritos nos últimos 30 dias (`DEFAULT_WINDOW_DAYS`).
  Mesma decisão de calcular em Python que `recommendations.py`: três
  relações reversas diferentes (`reviews`, `reviews__updates`,
  `favorited_by`) num só `annotate`+`Count` multiplicariam linhas entre
  os joins antes de contar. Três queries simples de `values_list` em vez
  disso, agregadas num dict em memória. Página pública, sem exigir
  login, com link "Em alta" sempre visível no nav.

## Roadmap (não implementado ainda)

### Fase 3 — diferenciais avançados
- Comparador de perfumes lado a lado
- Diretório de marcas (`Brand` já existe, falta a página de navegação)
- Conteúdo editorial (artigos/notícias de lançamento)

## Comandos

```bash
pip install -r requirements.txt        # instalar dependências
python manage.py migrate               # aplicar migrations (SQLite por padrão)
python manage.py seed_perfumes         # popular o catálogo com os ~20 perfumes do seed antigo
python manage.py createsuperuser       # criar acesso ao /admin/
python manage.py runserver             # subir o app em http://localhost:8000
pytest                                 # rodar os testes (exclui legacy/, ver pytest.ini)
```

Mais contexto de produto e telas em [README.md](./README.md).
