from urllib.parse import urljoin

from bs4 import BeautifulSoup


def texto(elemento):
    if elemento is None:
        return "Não informado"
    return " ".join(elemento.get_text(" ", strip=True).split()) or "Não informado"


def extrair_links(html, url_pagina, numero_pagina):
    pagina = BeautifulSoup(html, "html.parser")
    vagas = []
    for card in pagina.select(".cell-list > a[href]"):
        titulo = card.select_one("h3")
        if titulo is None:
            continue

        # O selo de vaga vencida não faz parte do título.
        situacao = "Sem selo de vencida"
        for selo in titulo.select("span"):
            if texto(selo) == "Vencida":
                situacao = "Vencida"
                selo.decompose()

        vagas.append({
            "titulo": texto(titulo),
            "link": urljoin(url_pagina, card["href"]),
            "pagina": numero_pagina,
            "situacao": situacao,
        })
    return vagas


def extrair_vaga(html, link):
    pagina = BeautifulSoup(html, "html.parser")
    conteudo = pagina.select_one(".wrapper-content-job-show")
    if conteudo is None:
        raise ValueError("A página não contém os detalhes de uma vaga.")

    local = "Não informado"
    salario = "Não informado"
    for paragrafo in conteudo.select(".wrapper-details-job-show p"):
        valor = texto(paragrafo)
        if valor.startswith("Localização:"):
            local = valor.removeprefix("Localização:").strip() or "Não informado"
        elif valor.startswith("Salário:"):
            salario = valor.removeprefix("Salário:").strip() or "Não informado"

    # Cada h3 inicia uma seção; seus irmãos seguintes contêm o texto da seção.
    secoes = {}
    for cabecalho in conteudo.select(".line-height-2-4 h3"):
        trechos = []
        for elemento in cabecalho.find_next_siblings():
            if elemento.name == "h3":
                break
            trecho = texto(elemento)
            if trecho != "Não informado":
                trechos.append(trecho)
        secoes[texto(cabecalho)] = "\n".join(trechos) or "Não informado"

    return {
        "titulo": texto(pagina.select_one(".wrapper-header-job-show h1")),
        "empresa": texto(conteudo.select_one("h2")),
        "local": local,
        "faixa_salarial": salario,
        "link": link,
        "descricao": secoes.get("Atividades e Responsabilidades", "Não informado"),
        "requisitos": secoes.get("Requisitos", "Não informado"),
    }
