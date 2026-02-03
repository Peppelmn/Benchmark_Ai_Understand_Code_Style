import json
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
    It also preserves repository metadata (URL, commit hash) for traceability.
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
        saves repository metadata (URL, commit hash) to 'repo_info.json', and removes version control 
        metadata (.git) to treat the download as a static codebase.

        Args:
            query (str): The GitHub search query string (e.g., 'language:python stars:>1000').
            limit (int, optional): The maximum number of repositories to download. Defaults to 5.
            max_size_mb (int, optional): The maximum size limit in MB for a repository to be eligible. Defaults to 100.

        Returns:
            List[Path]: A list of Path objects pointing to the successfully downloaded (or existing) repository directories.
        """
        if any(self.download_dir.iterdir()):
            print(f"\n[INFO] La cartella '{self.download_dir}' non è vuota.")
            print("\tDownload da GitHub saltato. Verranno usati i repository esistenti.\n")
            return [p for p in self.download_dir.iterdir() if p.is_dir()]

        print(f"\nRicerca GitHub: '{query}' (Limit: {limit})...")

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

            print(f"  [Download] Clonando {repo.full_name} ({repo.stargazers_count} stelle)...")
            try:
                # 1. Clone the repository
                cloned_repo = Repo.clone_from(repo.clone_url, target_path, depth=1)
                
                # 2. Extract Metadata (URL and Commit Hash)
                head_commit = cloned_repo.head.commit.hexsha
                repo_info = {
                    "url": repo.html_url,  # e.g., https://github.com/psf/requests
                    "commit": head_commit, # e.g., a1b2c3d4...
                    "full_name": repo.full_name
                }
                
                # 3. Save repo_info.json in the downloaded project root
                with open(target_path / "repo_info.json", "w", encoding="utf-8") as f:
                    json.dump(repo_info, f, indent=2)

                # 4. Cleanup .git folder to save space
                shutil.rmtree(target_path / ".git", ignore_errors=True)
                
                downloaded_paths.append(target_path)
                count += 1
            except Exception as e:
                print(f"  [Errore] Impossibile clonare {repo.name}: {e}")

        return downloaded_paths