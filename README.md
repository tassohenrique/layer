# Layer 🌸

![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-DATABASE__URL-4169E1?logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-fallback%20local-003B57?logo=sqlite&logoColor=white)
![No ads](https://img.shields.io/badge/sem%20an%C3%BAncios-por%20princ%C3%ADpio-success)

Plataforma de reviews de perfumes — pirâmide olfativa, accords, ficha
técnica e nota média da comunidade em cada página de perfume, com
usuários logados escrevendo reviews. Nos moldes do Fragrantica, mas com
um compromisso explícito: **sem anúncios e sem bloqueio de navegação**.

> Até a versão anterior, o Layer era um app pessoal (Streamlit) pra
> catalogar sua própria coleção e sugerir combinações de layering. Esse
> código foi preservado em [`legacy/`](./legacy) e pode virar a base do
> recomendador de perfumes semelhantes mais adiante — ver
> [CLAUDE.md](./CLAUDE.md) pro histórico completo do pivot.

## Stack

- Django 6.x + Postgres (via `DATABASE_URL`; cai pra SQLite local se a
  variável não estiver definida — não precisa instalar Postgres pra
  rodar localmente)
- Pillow (upload de avatar de perfil)
- `pytest-django` para testes

## Rodando localmente

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows; no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # ajuste se for usar Postgres (DATABASE_URL)

python manage.py migrate
python manage.py seed_perfumes    # popula o catálogo com 35 perfumes reais (nicho + designer)
python manage.py createsuperuser  # acesso ao /admin/, pra cadastrar/editar perfumes

python manage.py runserver
```

Abra `http://localhost:8000`. Cadastro de perfumes (marca, notas,
accords, imagem do frasco) é feito pelo `/admin/` no MVP — ainda não tem
uma tela própria de CRUD de catálogo. A imagem é opcional e sempre
upload manual (sem scraping de nenhum site); sem ela, aparece um
placeholder.

## Rodando os testes

```bash
pytest
```

Cobre models (`catalog`), a view da página de perfume, criação/edição de
review e o comando `seed_perfumes` (idempotente — pode rodar de novo sem
duplicar). Os testes do app antigo ficaram em `legacy/tests/` e são
ignorados pelo `pytest.ini` atual.

## Telas (Fase 1)

- `/` — lista de perfumes cadastrados
- `/perfumes/<slug>/` — pirâmide olfativa, accords, ficha técnica, nota
  média + reviews, formulário de review pra quem está logado
- `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/`
- `/accounts/profile/` — editar nome de exibição e avatar
- `/admin/` — cadastro de perfumes/marcas/accords/notas

## Roadmap

Fases 2 (busca, favoritos, curtidas em review, edição com histórico) e 3
(recomendador, "em alta", comparador, diretório de marcas, editorial)
estão detalhadas em [CLAUDE.md](./CLAUDE.md).
