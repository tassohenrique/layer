MAX_COMPARE = 4


def parse_compare_slugs(get_params) -> list[str]:
    """Lê os slugs de perfumes a comparar da querystring (`?p=slug&p=slug2`),
    removendo duplicatas e limitando a MAX_COMPARE, preservando a ordem em
    que foram adicionados."""
    seen: list[str] = []
    for slug in get_params.getlist("p"):
        slug = slug.strip()
        if slug and slug not in seen:
            seen.append(slug)
    return seen[:MAX_COMPARE]
