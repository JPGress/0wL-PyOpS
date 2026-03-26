import os
import json
import time
from core.logger import log

try:
    import instaloader
    import requests
    from bs4 import BeautifulSoup
    DEPENDENCIES_OK = True
except ImportError:
    DEPENDENCIES_OK = False

def scrape_instagram_fallback(username):
    log.warning(f"[!] Tentando coletar via visualizadores anônimos alternativos (ex: storiesig.info)...")
    
    # As an alternative, if we can't scrape Instaloader direct due to auth wall,
    # we provide the URLs to the anonymous viewers as viable OSINT pivoting points for the operator,
    # and attempt a basic scrape on an open anonymous viewer like picuki or dumpoir if possible.
    
    fallback_data = {
        "platform": "instagram_anonymous",
        "username": username,
        "status": "Instaloader Blocked. Falling back to Anonymous Scrapers.",
        "alternative_viewers_urls": [
            f"https://storiesig.info/pt/{username}/",
            f"https://dumpoir.com/v/{username}",
            f"https://www.picuki.com/profile/{username}"
        ]
    }
    
    # Attempting to fetch basic HTML from dumpoir to parse bio/name as a proof of concept fallback
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(f"https://dumpoir.com/v/{username}", headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            user_info = soup.find('div', class_='user')
            if user_info:
                name_tag = user_info.find('h1')
                bio_tag = user_info.find('div', class_='desc')
                if name_tag:
                    fallback_data["full_name"] = name_tag.text.strip()
                if bio_tag:
                    fallback_data["biography"] = bio_tag.text.strip()
                log.success("[+] Metadados parciais extraídos via Dumpoir (Anonymous Viewer).")
    except Exception as e:
        log.debug(f"Erro no fallback do Dumpoir: {e}")
        
    return fallback_data

def scape_instagram(username, mode):
    log.info(f"[*] Verificando perfil Instagram: {username}")
    L = instaloader.Instaloader(quiet=True, max_connection_attempts=1)
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        log.error(f"[-] Perfil '{username}' não existe ou Instagram bloqueou o IP (Ghost Ban).")
        return scrape_instagram_fallback(username)
    except instaloader.exceptions.ConnectionException:
        log.error(f"[-] Conexão recusada pelo Instagram (Rate Limit/Auth Wall) para '{username}'.")
        return scrape_instagram_fallback(username)
    except Exception as e:
        if "Expecting value: line 1 column 1" in str(e):
            log.error(f"[-] Instaloader bloqueado pelo Instagram (Anti-Bot Ativado) no perfil '{username}'.")
            return scrape_instagram_fallback(username)
        log.error(f"Erro ao buscar '{username}' no Instagram: {e}")
        return scrape_instagram_fallback(username)

    data = {
        "platform": "instagram",
        "username": profile.username,
        "full_name": profile.full_name,
        "biography": profile.biography,
        "is_private": profile.is_private,
        "followers_count": profile.followers,
        "following_count": profile.followees,
        "external_url": profile.external_url,
    }

    if profile.is_private:
        log.warning(f"[!] O perfil @{username} é PRIVADO.")
        log.warning("[!] OPSEC: Sugerimos o uso de um Avatar/Sock Puppet com acesso (seguindo o perfil) para continuidade do levantamento.")
        data["posts"] = "Ocultos (Privado)"
        return data

    if mode == "1" or mode == "2":
        log.success("[+] Perfil público! Extraindo fotos, bio e postagens (Rápida)...")
        posts_data = []
        try:
            for i, post in enumerate(profile.get_posts()):
                if i >= 10: # Limit for 'rápida'
                    break
                posts_data.append({
                    "shortcode": post.shortcode,
                    "date": str(post.date_utc),
                    "caption": post.caption[:200] + "..." if post.caption else "",
                    "url": f"https://instagram.com/p/{post.shortcode}/"
                })
            data["recent_posts"] = posts_data
        except Exception as e:
             log.error(f"Erro extraindo posts: {e}")

    if mode == "2":
        log.warning("[!] Iniciando Coleta Completa (Seguidores/Seguidos).")
        try:
            log.info("[+] Tentando extrair contatos...")
            # Puxamos apenas alguns para evitar rate limit (já que num cenário real demora)
            data["followers"] = [follower.username for idx, follower in enumerate(profile.get_followers()) if idx < 100]
            data["followees"] = [followee.username for idx, followee in enumerate(profile.get_followees()) if idx < 100]
            log.success("[+] Seguidores capturados com sucesso na visão permitida.")
        except instaloader.exceptions.LoginRequiredException:
            log.error("[-] Falha: Para baixar os seguidores, é necessário estar Autenticado no Instagram via Instaloader.")
            log.error("[-] OPSEC: Realize um login prévio com um Avatar confiável e tente novamente.")
            data["followers"] = "Falha: Login Required"
            data["followees"] = "Falha: Login Required"
        except Exception as e:
            log.error(f"[-] Erro ao baixar contatos: {e}")

    return data


def scrape_linkedin(username):
    log.info(f"[*] Buscando informações profissionais no LinkedIn para: {username}")
    # Scraping direto do LI é complexo sem auth. Fazemos Dork no Google para recuperar os snippets públicos dele!
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    # Removemos as aspas estritas do Dorking e limpamos os hifens comuns de slugs
    clean_query = username.replace("-", " ")
    url = f"https://www.google.com/search?q=site:linkedin.com/in/+{clean_query}"
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        search_results = soup.find_all('div', class_='g')
        results = []
        for g in search_results:
            title_el = g.find('h3')
            snippet_el = g.find('div', class_='VwiC3b')
            
            if title_el and snippet_el:
                results.append({
                    "professional_summary": title_el.text.replace(" - LinkedIn", ""),
                    "description_snippet": snippet_el.text
                })
        
        if not results:
            log.warning("[-] Nenhuma menção clara encontrada no Google para este perfil do LinkedIn.")
            return {"platform": "linkedin", "query": username, "status": "Not Found / Blocked"}
            
        log.success(f"[+] {len(results)} registros de atividades profissionais coletados.")
        return {
            "platform": "linkedin",
            "query": username,
            "osint_dork_results": results
        }
        
    except Exception as e:
        log.error(f"Erro na exploração do LinkedIn: {e}")
        return None


import urllib.parse

def extract_username(url_or_name, platform="ig"):
    if not url_or_name:
        return ""
    if platform == "ig":
        if "instagram.com" in url_or_name:
            path = urllib.parse.urlparse(url_or_name).path
            parts = [p for p in path.split('/') if p]
            return parts[0] if parts else ""
        return url_or_name.replace("@", "").strip()
    else:
        if "linkedin.com" in url_or_name:
            path = urllib.parse.urlparse(url_or_name).path
            parts = [p for p in path.split('/') if p]
            if "in" in parts:
                idx = parts.index("in")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            return ""
        return url_or_name.strip()

def run():
    print()
    log.info("--- Módulo 2: SOCMINT & Identity ---")
    if not DEPENDENCIES_OK:
        log.error("Dependências SOCMINT ausentes!")
        log.warning("Comando para o Host: pip install instaloader beautifulsoup4 requests --break-system-packages")
        print()
        input("Pressione Enter para voltar...")
        return
        
    log.info("Insira os alvos para OSINT (Deixe em branco se não quiser rastrear aquela rede)")
    
    try:
        ig_input = input("[>] Alvo no Instagram (Username ou URL do perfil): ").strip()
        in_input = input("[>] Alvo no LinkedIn (Slug ou URL do perfil): ").strip()
        
        ig_user = extract_username(ig_input, "ig")
        in_user = extract_username(in_input, "li")

        if not ig_user and not in_user:
            log.warning("Nenhum alvo definido. Operação cancelada.")
            return
            
        mode = "1"
        if ig_user:
             print("\nModos de coleta Instagram (se o perfil for público):")
             print(" [1] Rápida (Apenas postagens, fotos e bio)")
             print(" [2] Completa (Rápida + Extração em massa de Seguidores e Seguidos)")
             mode = input("Selecione o modo IG [1/2]: ").strip()
             if mode not in ["1", "2"]:
                 mode = "1"

        print("\n-------------------------------------------------")
        results = {}
        
        if ig_user:
            ig_data = scape_instagram(ig_user, mode)
            if ig_data:
                results["instagram"] = ig_data
                
        if in_user:
            in_data = scrape_linkedin(in_user)
            if in_data:
                results["linkedin"] = in_data

        if results:
            target_name = ig_user if ig_user else in_user.replace(" ", "_")
            ts = int(time.time())
            filename = f"target_{target_name}_{ts}_socmint.json"
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
                
            print()
            log.success(f"[✔] Dossiê exportado com sucesso para: {os.path.abspath(filename)}")
        else:
            log.warning("[-] Nenhuma informação crítica pôde ser extraída.")
            
        print()
        input("Pressione Enter para voltar...")
    except KeyboardInterrupt:
        print()
        log.info("Ação interrompida pelo Operador. Retornando...")
