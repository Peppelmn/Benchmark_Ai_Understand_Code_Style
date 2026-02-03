import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from CodebaseAnalyzer import CodebaseAnalyzer
from Spacing.SpacingAnalyzer import SpacingAnalyzer
from Naming.NamingAnalyzer import NamingAnalyzer

class DatasetGenerator:
    """
    Scans the entire codebase, calculates token counts, and determines the correct answers (Ground Truth)
    for each file using specific analyzers (Spacing and Naming). It aggregates this information,
    along with GitHub permalinks, to generate a static 'Master Dataset' in JSON format.
    """

    def __init__(self, codebase_path: str):
        """
        Initializes the DatasetGenerator with the target codebase directory.

        Args:
            codebase_path (str): The root directory path containing the downloaded repositories to be analyzed.
        """
        self.codebase_path = Path(codebase_path)
        # Cache to avoid re-reading repo_info.json for every file in the same repo
        self._repo_info_cache = {} 
        
    def _get_github_url(self, file_path: Path) -> Optional[str]:
        """
        Constructs the GitHub permalink for the specified file.
        It assumes the directory structure is: Codebase/downloads/RepoName/path/to/file.py
        It reads 'repo_info.json' from the repository root to get the base URL and commit hash.

        Args:
            file_path (Path): The absolute path to the file.

        Returns:
            Optional[str]: The full GitHub URL (e.g., '.../blob/commit_hash/src/main.py'), or None if metadata is missing.
        """
        try:
            # Calculate the path relative to the codebase root (downloads folder)
            # e.g., Requests/src/models.py
            rel_to_base = file_path.relative_to(self.codebase_path)
            
            # The first part of the relative path is the repository directory name (e.g., "Requests")
            repo_dir_name = rel_to_base.parts[0]
            repo_root = self.codebase_path / repo_dir_name
            
            # Check cache for repository info
            if repo_dir_name not in self._repo_info_cache:
                info_path = repo_root / "repo_info.json"
                if info_path.exists():
                    with open(info_path, 'r') as f:
                        self._repo_info_cache[repo_dir_name] = json.load(f)
                else:
                    self._repo_info_cache[repo_dir_name] = None # Marker to avoid retrying

            info = self._repo_info_cache[repo_dir_name]
            if not info:
                return None

            # Construct URL
            # Format: {html_url}/blob/{commit}/{path_inside_repo}
            base_url = info["url"]
            commit = info["commit"]
            
            # Path inside the repo (excluding the repo folder name)
            # e.g., src/models.py
            path_inside_repo = "/".join(rel_to_base.parts[1:])
            
            return f"{base_url}/blob/{commit}/{path_inside_repo}"

        except Exception:
            return None

    def generate_dataset(self, output_path: str):
        """
        Executes the complete analysis pipeline and saves the resulting ground truth dataset to a JSON file.

        This method performs the following steps:
        1. Checks if the output file already exists (skips generation if so).
        2. Initializes the base, spacing, and naming analyzers.
        3. Retrieves all Python files from the codebase.
        4. Iterates through each file to:
           - Calculate the token count.
           - Generate the GitHub permalink using stored metadata.
           - Analyze spacing and naming conventions.
        5. Aggregates valid results and metadata.
        6. Serializes the collected data into a JSON file.

        Args:
            output_path (str): The file path where the generated JSON dataset will be saved.

        Returns:
            None: The method writes directly to the file system and prints progress to the console.

        Raises:
            IOError: If there are issues writing the final JSON file (though caught internally, the error is printed).
        """

        if os.path.exists(output_path):
            print(f"[INFO] Esiste già un dataset in {output_path}. Salto la generazione.\n")
            return

        # Initialize analyzers
        self.base_analyzer = CodebaseAnalyzer(codebase_path=self.codebase_path)
        self.spacing_analyzer = SpacingAnalyzer(self.codebase_path)
        self.naming_analyzer = NamingAnalyzer(self.codebase_path)

        print(f"\n{'='*60}")
        print(f"GENERAZIONE DATASET STATICO")
        print(f"Path: {self.codebase_path}")
        print(f"{'='*60}\n")
        
        # 1. File scanning
        all_files = self.base_analyzer.get_python_files()
        
        if not all_files:
            print("[ERRORE] Nessun file Python trovato nella codebase.")
            return

        dataset = []
        total_files = len(all_files)
        
        print(f"Inizio analisi su {total_files} file...")

        for i, file_path in enumerate(all_files):
            # Visual progress feedback
            print(f"[{i+1}/{total_files}] Processing: {file_path.name}...", end="\r")
            
            str_path = str(file_path)
            
            # Calculate relative path
            try:
                relative_path = str(file_path.relative_to(self.codebase_path))
            except ValueError:
                relative_path = str_path

            # 2. GitHub URL Generation (NEW)
            github_url = self._get_github_url(file_path)

            # 3. Read content and count tokens
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Fallback token counting: ~4 chars per token
                token_count = len(content) // 4 

            except Exception as e:
                print(f"\n[SKIP] Errore lettura {file_path.name}: {e}")
                continue

            # 4. Spacing Analysis
            try:
                spacing_data = self.spacing_analyzer.analyze_file(str_path)
            except Exception as e:
                print(f"\n[ERR] SpacingAnalyzer fallito su {file_path.name}: {e}")
                spacing_data = {}

            # 5. Naming Analysis
            try:
                naming_data = self.naming_analyzer.analyze_file(str_path)
            except Exception as e:
                print(f"\n[ERR] NamingAnalyzer fallito su {file_path.name}: {e}")
                naming_data = {}

            # 6. Merge results
            all_answers = {**spacing_data, **naming_data}
            
            # Filter out None keys
            clean_answers = {k: v for k, v in all_answers.items() if v is not None}

            if not clean_answers:
                continue

            file_entry = {
                "file_path": relative_path,
                "github_url": github_url, # <--- Added Field
                "token_count": token_count,
                "answers": clean_answers
            }
            
            dataset.append(file_entry)

        print(f"\n\nAnalisi completata.")
        print(f"Salvataggio di {len(dataset)} entry nel file '{output_path}'...")

        # 7. Save to JSON
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2)
            print(f"✅ Dataset salvato con successo!")
        except Exception as e:
            print(f"❌ Errore durante il salvataggio del JSON: {e}")