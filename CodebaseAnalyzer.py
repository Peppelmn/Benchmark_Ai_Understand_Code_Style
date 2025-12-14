from ast import List
from pathlib import Path

class CodebaseAnalyzer:
    """Classe base per analizzatori di codebase"""
    
    def __init__(self, codebase_path: str, max_token_limit, num_target_files_per_question=10):
        """
        Inizializza l'analyzer filtrando i file non validi o troppo grandi.
        
        Args:
            codebase_path: Percorso della cartella da analizzare
            max_char_limit: Limite caratteri (~120k chars = ~30k tokens)
        """
        self.codebase_path = Path(codebase_path)
        self.python_files = []
        self.parse_error_count = 0
        self.num_target_files_per_question = num_target_files_per_question
        self.max_char_limit = max_token_limit * 4
        
        print(f"Inizializzazione Analyzer: scansione file in {self.codebase_path}...")
        skipped_count = 0

        for path in self.codebase_path.rglob("*.py"):
            
            # 1. Filtro Cartelle (Standard)
            if any(part in {".git", "__pycache__", ".venv", "venv", "node_modules", "build", "dist"} for part in path.parts):
                continue
            
            # 2. Filtro Link Simbolici
            if path.is_symlink():
                continue

            # 3. Filtro DIMENSIONE (Il controllo centralizzato)
            try:
                # Leggiamo il file per vedere quanto è grosso
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if len(content) > self.max_char_limit:
                    skipped_count += 1
                    # (Opzionale) Debug print per vedere cosa scarta
                    # print(f"  -> Skipped {path.name}: troppo grande ({len(content)} chars)")
                    continue
                    
                # Se il file è vuoto, inutile analizzarlo
                if not content.strip():
                    continue

            except Exception:
                # Se non riusciamo nemmeno a leggerlo (es. permessi), lo saltiamo
                continue

            # Se passa tutti i controlli, è un file valido per il benchmark
            self.python_files.append(path)
            
        print(f"Analyzer pronto. File validi caricati: {len(self.python_files)} (Scartati per dimensione: {skipped_count})")

    def get_files(self):
        """Restituisce la lista dei file Python validi trovati nella codebase."""
        return self.python_files