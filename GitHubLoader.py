import os
import shutil
from pathlib import Path
from github import Github
from git import Repo
from dotenv import load_dotenv

class GitHubLoader:
    def __init__(self, download_dir: str = "Codebase/downloads"):
        load_dotenv("keys.env")
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN non trovato nel file .env")
        
        self.g = Github(token)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_repositories(self, query: str, limit: int = 5, max_size_mb: int = 100):
        """
        Scarica repository che corrispondono alla query.
        
        Args:
            query: Query di ricerca GitHub (es. 'language:python stars:>1000')
            limit: Numero massimo di repo da scaricare
            max_size_mb: Dimensione massima in MB per evitare repo giganti
        """
        print(f"\n🔎 Ricerca GitHub: '{query}' (Limit: {limit})...")
        repositories = self.g.search_repositories(query=query, sort="stars", order="desc")
        
        count = 0
        downloaded_paths = []

        for repo in repositories:
            if count >= limit:
                break
            
            # Filtro dimensione (approssimativo, size è in KB)
            if repo.size > (max_size_mb * 1024):
                print(f"Skipped {repo.full_name}: troppo grande ({repo.size // 1024} MB)")
                continue

            target_path = self.download_dir / repo.name
            
            if target_path.exists():
                print(f"  [Esistente] {repo.name}")
                downloaded_paths.append(target_path)
                count += 1
                continue

            print(f"  [Download] Clonando {repo.full_name} ({repo.stargazers_count} ⭐)...")
            try:
                Repo.clone_from(repo.clone_url, target_path, depth=1) # Depth 1 = solo l'ultimo commit (veloce)
                
                # Rimuovi la cartella .git per risparmiare spazio e non confondere il tuo git
                shutil.rmtree(target_path / ".git", ignore_errors=True)
                
                downloaded_paths.append(target_path)
                count += 1
            except Exception as e:
                print(f"  [Errore] Impossibile clonare {repo.name}: {e}")

        return downloaded_paths

if __name__ == "__main__":
    # Esempio di utilizzo standalone
    loader = GitHubLoader()
    
    # Criteri rigorosi: Python, >5000 stelle, creati dopo il 2020 (codice moderno)
    query = "language:python stars:>5000 created:>2020-01-01"
    
    loader.download_repositories(query, limit=5)