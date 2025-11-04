from pathlib import Path

class CodebaseAnalyzer:
    """Classe base per analizzatori di codebase"""
    
    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.python_files = []

        # Usa glob non ricorsivo e manualmente controlla le directory
        for path in self.codebase_path.rglob("*.py"):
            # Evita directory inutili o pericolose
            if any(part in {".git", "__pycache__", ".venv", "venv", "node_modules"} for part in path.parts):
                continue
            # Evita link simbolici
            if path.is_symlink():
                continue
            self.python_files.append(path)
