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

def scape_instagram(username, mode):
    log.info(f"[*] Verificando perfil Instagram: {username}")
    L = instaloader.Instaloader(quiet=True)
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except Exception as e:
        log.error(f"Erro ao buscar '{username}' no Instagram: {e}")
        return None

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
    url = f"https://www.google.com/search?q=site:linkedin.com/in/+%22{username}%22"
    
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
        ig_user = input("[>] Alvo no Instagram (ex: neymarjr): ").replace("@", "").strip()
        in_user = input("[>] Alvo no LinkedIn (nome ou slug): ").strip()

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
