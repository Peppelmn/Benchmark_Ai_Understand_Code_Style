import os
import shutil
from pathlib import Path
from github import Github
from git import Repo
from dotenv import load_dotenv

class GitHubLoader:
    """
    Handles the discovery and downloading of repositories from GitHub to build a local codebase for analysis.
    It manages authentication via environment variables and ensures efficient cloning (shallow clones) to save space and bandwidth.
    """
    def __init__(self, download_dir: str = "Codebase/downloads"):
        """
        Initializes the loader, sets up the GitHub client using credentials from the environment file,
        and prepares the download directory.

        Args:
            download_dir (str, optional): The local path where repositories will be saved. Defaults to "Codebase/downloads".

        Raises:
            ValueError: If the 'GITHUB_TOKEN' is missing from the .env file.
        """
        load_dotenv("keys.env")
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN non trovato nel file .env")
        
        self.g = Github(token)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_repositories(self, query: str, limit: int = 5, max_size_mb: int = 100):
        """
        Searches for and downloads repositories matching a specific query.
        It applies filters for size and existence, performs a shallow clone (depth=1) for efficiency,
        and removes version control metadata (.git) to treat the download as a static codebase.

        Args:
            query (str): The GitHub search query string (e.g., 'language:python stars:>1000').
            limit (int, optional): The maximum number of repositories to download. Defaults to 5.
            max_size_mb (int, optional): The maximum size limit in MB for a repository to be eligible. Defaults to 100.

        Returns:
            List[Path]: A list of Path objects pointing to the successfully downloaded (or existing) repository directories.
        """
        print(f"\n🔎 Ricerca GitHub: '{query}' (Limit: {limit})...")
        repositories = self.g.search_repositories(query=query, sort="stars", order="desc")
        
        count = 0
        downloaded_paths = []

        for repo in repositories:
            if count >= limit:
                break
            
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
                Repo.clone_from(repo.clone_url, target_path, depth=1)
                
                shutil.rmtree(target_path / ".git", ignore_errors=True)
                
                downloaded_paths.append(target_path)
                count += 1
            except Exception as e:
                print(f"  [Errore] Impossibile clonare {repo.name}: {e}")

        return downloaded_paths

if __name__ == "__main__":
    loader = GitHubLoader()
    
    query = "language:python stars:>5000 created:>2020-01-01"
    
    loader.download_repositories(query, limit=5)