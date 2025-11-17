import ast
import random
from CodebaseAnalyzer import CodebaseAnalyzer
from DataClassesDefiner import Question, Answer
from typing import Set, Dict, Tuple

class _NameCollector(ast.NodeVisitor):
    """
    Un NodeVisitor che raccoglie tutti i nomi unici
    da Classi, Funzioni, Argomenti e Variabili in un singolo file.
    """
    def __init__(self):
        self.names: Set[str] = set()

    def add_name(self, name: str):
        if name:
            self.names.add(name)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.add_name(node.name)
        self.generic_visit(node) 

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.add_name(node.name)
        self.generic_visit(node) 

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.add_name(node.name)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg):
        self.add_name(node.arg)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.add_name(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        self.generic_visit(node)


class NamingAnalyzer(CodebaseAnalyzer):
    """Analizza la codebase su aspetti di naming, trova la risposta corretta per le domande"""

    def __init__(self, codebase_path: str):
        super().__init__(codebase_path)
        self._file_naming_cache: Dict[str, Dict[str, int]] = {}
                
    def _is_pascal_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        
        return (
            "_" not in name and
            name[0].isupper() and
            any(c.islower() for c in name)
        )

    def _is_camel_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        
        return (
            "_" not in name and
            name[0].islower() and
            any(c.isupper() for c in name)
        )

    def _is_snake_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        return (
            name.islower() and
            "_" in name
        )

    def _get_naming_counts_for_file(self, file_path: str) -> Dict[str, Dict]:
        """
        Esegue l'analisi AST su un SINGOLO file e classifica ogni nome.
        Utilizza una cache per evitare di ri-analizzare.
        
        RESTITUISCE: 
        Un dizionario strutturato:
        { "snake_case": {"count": 5, "names": ["var1", ...]}, ... }
        """
        if file_path in self._file_naming_cache:
            return self._file_naming_cache[file_path]
        
        counts = {
            "PascalCase": {"count": 0, "names": []},
            "camelCase":  {"count": 0, "names": []},
            "snake_case":  {"count": 0, "names": []},
            "constants":   {"count": 0, "names": []},
            "special":     {"count": 0, "names": []},
            "other":       {"count": 0, "names": []}
        }
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            collector = _NameCollector()
            collector.visit(tree)
            all_names_in_file = collector.names
            
        except Exception as e:
            self.parse_error_count += 1 
            self._file_naming_cache[file_path] = counts
            return counts
        
        for original_name in all_names_in_file:
            
            # Se è TUTTO MAIUSCOLO, è una costante.
            if original_name.isupper():
                counts["constants"]["count"] += 1
                counts["constants"]["names"].append(original_name)
                continue # Classificazione terminata

            # Se è un metodo "dunder", è speciale.
            if original_name.startswith('__') and original_name.endswith('__'):
                counts["special"]["count"] += 1
                counts["special"]["names"].append(original_name)
                continue # Classificazione terminata

            name_to_classify = original_name.lstrip('_')

            # --- 3. Classificazione (usa il nome "pulito") ---
            # Le funzioni _is_... vengono chiamate sul nome pulito.
            
            if self._is_pascal_case(name_to_classify):
                counts["PascalCase"]["count"] += 1
                counts["PascalCase"]["names"].append(original_name)

            elif self._is_camel_case(name_to_classify):
                counts["camelCase"]["count"] += 1
                counts["camelCase"]["names"].append(original_name)

            elif self._is_snake_case(name_to_classify):
                counts["snake_case"]["count"] += 1
                counts["snake_case"]["names"].append(original_name)

            else:
                counts["other"]["count"] += 1
                counts["other"]["names"].append(original_name)
        
        self._file_naming_cache[file_path] = counts
        return counts

    def _find_random_file_for_convention(self, convention: str):
        """
        Trova un file *casuale* nella codebase che contenga almeno un
        esempio di una specifica convenzione (es. "snake_case") E
        che non superi le 1000 righe di codice.
        
        Restituisce: (percorso_file_relativo, conteggio, lista_di_nomi)
        """
        candidate_files = []
        max_lines = 1000

        for file_path in self.python_files:
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                if len(lines) > max_lines:
                    continue
            
            except Exception as e:
                print(f"[!] Errore leggendo {file_path} per contare le righe: {e}")
                continue

            counts = self._get_naming_counts_for_file(str(file_path))
            
            default_data = {"count": 0, "names": []} 
            
            convention_data = counts.get(convention, default_data)
            current_count = convention_data["count"]
            current_names = convention_data["names"]
            
            # Se questo file ha almeno un esempio, è un candidato
            if current_count > 0:
                relative_path = file_path.relative_to(self.codebase_path)
                candidate_files.append((str(relative_path), float(current_count), current_names))

        if not candidate_files:
            print(f"[ATTENZIONE] NamingAnalyzer non ha trovato file per '{convention}' (con < {max_lines} righe)")
            return None 

        return random.choice(candidate_files)

    def question_N01(self):
        """Trova un file casuale con nomi snake_case e il loro numero."""
        return self._find_random_file_for_convention("snake_case")

    def question_N02(self):
        """Trova un file casuale con nomi camelCase e il loro numero."""
        return self._find_random_file_for_convention("camelCase")

    def question_N03(self):
        """Trova un file casuale con nomi PascalCase e il loro numero."""
        return self._find_random_file_for_convention("PascalCase")
    
    def question_N04(self):
        """
        Trova il file (< 1000 righe) con il maggior numero
        totale di nomi classificabili (snake, camel, pascal) e
        restituisce la convenzione dominante di QUEL file.
        
        Restituisce: (percorso_file_relativo, "convenzione_dominante")
        """
        best_file_path = None
        dominant_convention = "other"
        max_total_names = 0 
        max_lines = 1000

        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if len(f.readlines()) > max_lines:
                        continue
            except Exception as e:
                print(f"[!] Errore leggendo {file_path} per contare le righe: {e}")
                continue
            
            # Ottiene i dati del file (dalla cache o analizzandolo)
            counts_data = self._get_naming_counts_for_file(str(file_path))
            
            # Estrae i conteggi
            snake_count = counts_data["snake_case"]["count"]
            camel_count = counts_data["camelCase"]["count"]
            pascal_count = counts_data["PascalCase"]["count"]
            
            total_classifiable_names = snake_count + camel_count + pascal_count

            # Troviamo il file con il maggior numero di nomi in totale
            # (ignoriamo file con meno di 10 nomi per evitare file banali)
            if total_classifiable_names > max_total_names and total_classifiable_names > 10:
                max_total_names = total_classifiable_names
                best_file_path = file_path
                
                # Ora determina la convenzione dominante PER QUESTO file
                convention_counts = {
                    "snake_case": snake_count,
                    "camelCase": camel_count,
                    "PascalCase": pascal_count
                }
                
                # Trova la chiave (il nome della convenzione) con il valore (conteggio) massimo
                dominant_convention = max(convention_counts, key=convention_counts.get)

        if best_file_path is None:
            print(f"[ATTENZIONE] NamingAnalyzer non ha trovato file con > 10 nomi per N04")
            return None # Restituisce None come le altre funzioni

        relative_path = best_file_path.relative_to(self.codebase_path)
        
        # Restituisce il file trovato e la sua convenzione vincente (es. "snake_case")
        return (str(relative_path), dominant_convention)
    
    def question_N05(self):
        random_convention = random.choice(["snake_case", "camelCase", "PascalCase"])
        random_file = self._find_random_file_for_convention(random_convention)
        random_element = random.choice(random_file[2]) if random_file else None
        random_tuple = (random_file[0], random_convention, random_element if random_element else None) if random_file else None
        return random_tuple
    
    def question_N06(self):
        """
        Prende un file a caso, un nome a caso da quel file, e determina
        se quel nome segue una delle 3 convenzioni principali.
        
        Restituisce: (percorso_file, nome_scelto, è_standard [True/False])
        """
        max_lines = 1000
        tentativi = 0
        
        # Prova a trovare un file valido per un massimo di 50 tentativi
        while tentativi < 50:
            try:
                # 1. Scegli un file a caso
                file_path = random.choice(self.python_files)
                
                # 2. Controlla la lunghezza
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if len(f.readlines()) > max_lines:
                        tentativi += 1
                        continue # File troppo lungo, riprova

                # 3. Analizza il file e prendi TUTTI i nomi
                counts_data = self._get_naming_counts_for_file(str(file_path))
                
                all_names_in_file = (
                    counts_data["PascalCase"]["names"] +
                    counts_data["camelCase"]["names"] +
                    counts_data["snake_case"]["names"] +
                    counts_data["constants"]["names"] +
                    counts_data["other"]["names"] +
                    counts_data["special"]["names"]
                )

                if not all_names_in_file:
                    tentativi += 1
                    continue # File vuoto o con soli dunder, riprova

                # 4. Scegli un nome a caso da questo file
                random_name = random.choice(all_names_in_file)
                
                # 5. Classificalo: è una delle 3 convenzioni?
                # Pulisci il nome (rimuovi _) prima di testarlo
                name_to_test = random_name.lstrip('_')
                
                is_standard = (
                    self._is_pascal_case(name_to_test) or
                    self._is_camel_case(name_to_test) or
                    self._is_snake_case(name_to_test)
                )
                
                # 6. Restituisci i dati
                relative_path = file_path.relative_to(self.codebase_path)
                return (str(relative_path), str(is_standard).lower(), random_name)

            except Exception as e:
                # Probabile errore di parsing AST su un file strano, riprova
                tentativi += 1
                continue
        
        # Se dopo 50 tentativi non abbiamo trovato nulla
        print("[ATTENZIONE] NamingAnalyzer.question_N06 non è riuscito a trovare un nome valido.")
        return None
    
    def question_N07(self):
        return self._find_random_file_for_convention("other")
    
    def question_N08(self):
        random_file = self._find_random_file_for_convention("constants")
        random_constant = random.choice(random_file[2])
        return (random_file[0], "true" , random_constant) if "_" in random_constant else (random_file[0], "false", random_constant)
    
    def question_N09(self):
        """
        Sceglie un file CASUALE (con < 1000 righe) e trova la lunghezza 
        del nome più lungo presente all'interno di QUEL file specifico.
        
        Restituisce: (percorso_file, lunghezza_massima_nel_file)
        """
        max_lines = 1000
        tentativi = 0
        
        while tentativi < 50:
            try:
                # 1. Scegli un file a caso
                file_path = random.choice(self.python_files)
                
                # 2. Controlla la lunghezza (per performance)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if len(f.readlines()) > max_lines:
                        tentativi += 1
                        continue 

                # 3. Analizza il file e prendi TUTTI i nomi
                #    (Usa la cache se il file è già stato analizzato)
                counts_data = self._get_naming_counts_for_file(str(file_path))
                
                # Uniamo tutte le liste per avere tutti gli identificatori del file
                all_names_in_file = (
                    counts_data["PascalCase"]["names"] +
                    counts_data["camelCase"]["names"] +
                    counts_data["snake_case"]["names"] +
                    counts_data["constants"]["names"] +
                    counts_data["other"]["names"] +
                    counts_data["special"]["names"]
                )

                if not all_names_in_file:
                    tentativi += 1
                    continue # File vuoto, riprova

                # 4. Trova il nome più lungo IN QUESTO FILE
                longest_name = max(all_names_in_file, key=len)
                max_length = len(longest_name)
                
                # 5. Restituisci i dati
                relative_path = file_path.relative_to(self.codebase_path)
                
                return (str(relative_path), float(max_length), longest_name)

            except Exception as e:
                # Errore di lettura o parsing, prova un altro file
                tentativi += 1
                continue
        
        print("[ATTENZIONE] NamingAnalyzer.question_N09 non è riuscito a trovare un file valido.")
        return None