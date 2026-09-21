import csv
import platform
from datetime import datetime
from pathlib import Path
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from extracao import extrair_links, extrair_vaga

PORTAL = "https://programathor.com.br"
PAGINAS = 3
INTERVALO = 5
PASTA = Path(__file__).resolve().parent
CAMPOS = ["titulo", "empresa", "local", "faixa_salarial", "link", "descricao",
          "requisitos", "situacao", "pagina", "coletado_em"]


def salvar(vagas):
    pasta = PASTA / "dados"
    pasta.mkdir(exist_ok=True)
    # UTF-8 com BOM permite abrir os acentos corretamente no Excel.
    with (pasta / "vagas.csv").open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(vagas)


def criar_driver():
    """Cria o WebDriver adequado ao sistema operacional."""
    if platform.system() == "Darwin":
        opcoes = webdriver.SafariOptions()
        opcoes.page_load_strategy = "none"
        return webdriver.Safari(options=opcoes)
    # Linux e Windows usam o Chrome.
    opcoes = webdriver.ChromeOptions()
    opcoes.page_load_strategy = "none"
    opcoes.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=opcoes)


def main():
    driver = None
    vagas = []
    paginas_lidas = 0
    duplicatas = 0
    erros = 0
    try:
        driver = criar_driver()
        driver.set_page_load_timeout(30)
        espera = WebDriverWait(driver, 20)

        print("Abrindo o portal e pesquisando Python pelo link de tecnologia...", flush=True)
        driver.get(f"{PORTAL}/jobs")
        filtro = espera.until(EC.element_to_be_clickable((By.LINK_TEXT, "Vagas programador PYTHON")))
        filtro.click()
        espera.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "Vagas Python"))

        links = []
        vistos = set()
        for numero in range(1, PAGINAS + 1):
            espera.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".pagination .active"), str(numero)
            ))
            espera.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cell-list > a[href]")))
            html = driver.page_source
            encontrados = extrair_links(html, driver.current_url, numero)
            if not encontrados:
                raise ValueError(f"A página {numero} não retornou vagas reconhecíveis.")
            paginas_lidas += 1
            for vaga in encontrados:
                if vaga["link"] in vistos:
                    duplicatas += 1
                else:
                    vistos.add(vaga["link"])
                    links.append(vaga)
            print(f"Página {numero}: {len(encontrados)} anúncios; {len(links)} links únicos acumulados.", flush=True)

            if numero < PAGINAS:
                proxima = espera.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.pagination a[rel="Próx"]')
                ))
                sleep(INTERVALO)
                proxima.click()

        # Guardamos todos os links antes de sair da lista de resultados.
        for numero, resumo in enumerate(links, start=1):
            link = resumo["link"]
            print(f"Coletando {numero}/{len(links)}: {resumo['titulo']}", flush=True)
            try:
                sleep(INTERVALO)
                driver.get(link)
                # A URL canônica do HTML confirma que a página anterior foi substituída.
                espera.until(lambda navegador: any(
                    elemento.get_attribute("href") == link
                    for elemento in navegador.find_elements(By.CSS_SELECTOR, 'link[rel="canonical"]')
                ))
                espera.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".wrapper-content-job-show .line-height-2-4")
                ))
                html = driver.page_source
                vaga = extrair_vaga(html, link)
                if vaga["titulo"] == "Não informado":
                    raise ValueError("O título da vaga não foi encontrado.")
                vaga.update({"situacao": resumo["situacao"], "pagina": resumo["pagina"],
                             "coletado_em": datetime.now().astimezone().isoformat(timespec="seconds")})
                vagas.append(vaga)
                salvar(vagas)
            except (TimeoutException, WebDriverException, ValueError) as erro:
                if isinstance(erro, TimeoutException):
                    mensagem = "O conteúdo da vaga não apareceu em 20 segundos."
                else:
                    mensagem = str(erro).strip() or "A página da vaga não carregou."
                erros += 1
                print(f"  Não coletada: {link} — {mensagem.splitlines()[0]}", flush=True)
                html = driver.page_source
                if any(aviso in html.lower() for aviso in (
                    "sua solicitação foi bloqueada", "sorry, you have been blocked", "verify you are human"
                )):
                    print("O portal bloqueou o acesso. Encerrando sem novas tentativas.", flush=True)
                    break

    except (WebDriverException, ValueError, OSError) as erro:
        erros += 1
        print(f"Não foi possível concluir: {erro}", flush=True)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário. Salvando o que já foi coletado.", flush=True)
    finally:
        try:
            salvar(vagas)
        except OSError as erro:
            print(f"Não foi possível salvar os arquivos: {erro}")
        if driver is not None:
            try:
                driver.quit()
            except WebDriverException as erro:
                print(f"Não foi possível fechar o navegador: {erro.msg}")

    print(f"\nResultado: {len(vagas)} vagas; {paginas_lidas} páginas; "
          f"{duplicatas} duplicatas removidas; {erros} erros.")
    print(f"Arquivo: {PASTA / 'dados' / 'vagas.csv'}")


if __name__ == "__main__":
    main()
