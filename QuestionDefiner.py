from DataClassesDefiner import Question
from Spacing.SpacingAnalyzer import SpacingAnalyzer 
from Naming.NamingAnalyzer import NamingAnalyzer
from typing import List, Dict, Any

def get_all_questions(spacingAnalyzer: SpacingAnalyzer = None, namingAnalyzer: NamingAnalyzer = None) -> List[Question]:
    """
    Genera la lista di tutte le domande di spacing e naming,
    eseguendo il pre-calcolo dei dati necessari.
    """
    if spacingAnalyzer is None and namingAnalyzer is None:
        raise ValueError("spacingAnalyzer o namingAnalyzer devono essere forniti.")
    
    print("Pre-calcolo dati del benchmark (da 'get_all_questions')...")

    data_map: Dict[str, Any] = {}
    try:
        data_map["S01"] = spacingAnalyzer.question_S01()
        data_map["S02"] = spacingAnalyzer.question_S02()
        data_map["S03"] = spacingAnalyzer.question_S03_S04("before")
        data_map["S04"] = spacingAnalyzer.question_S03_S04("after")
        data_map["S05"] = spacingAnalyzer.question_S05()
        data_map["S06"] = spacingAnalyzer.question_S06()
        data_map["S07"] = spacingAnalyzer.question_S07()
        data_map["S08"] = spacingAnalyzer.question_S08_S09("above")
        data_map["S09"] = spacingAnalyzer.question_S08_S09("below")
        data_map["S10"] = spacingAnalyzer.question_S10()
        data_map["S11"] = spacingAnalyzer.question_S11()
        data_map["S12"] = spacingAnalyzer.question_S12()
        data_map["N01"] = namingAnalyzer.question_N01()
        data_map["N02"] = namingAnalyzer.question_N02()
        data_map["N03"] = namingAnalyzer.question_N03()
        data_map["N04"] = namingAnalyzer.question_N04()
        data_map["N05"] = namingAnalyzer.question_N05()

        if any(data is None for data in data_map.values()):
            raise ValueError("Uno o più analyzer non hanno prodotto risultati validi.")
            
    except Exception as e:
        print(f"Errore fatale durante la pre-analisi (in get_all_questions): {e}")
        raise e 
    
    print("Dati pre-calcolati con successo.")
    
    return [
        Question(
            id="S01",
            category="spacing",
            text=f"Nella definizione di una variabile quanti spazi vengono utilizzati per separare i token?",
            target_file=data_map['S01'][0]
        ),
        Question(
            id="S02",
            category="spacing",
            text=f"Nella definizione della condizione in una struttura di controllo, quanti spazi vengono usati per separare i token?",
            target_file=data_map['S02'][0]
        ),
        Question(
            id="S03",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati prima della virgola?",
            target_file=data_map['S03'][0]
        ),
        Question(
            id="S04",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati dopo la virgola?",
            target_file=data_map['S04'][0]
        ),
        Question(
            id="S05",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una funzione?",
            target_file=data_map['S05'][0]
        ),
        Question(
            id="S06",
            category="spacing",
            text=f"Qual è la lunghezza massima di una riga di codice (esclusi i commenti e le docstring)?",
            target_file=data_map['S06'][0]
        ),
        Question(
            id="S07",
            category="spacing",
            text=f"Quanti spazi vengono utilizzati per l'indentazione del codice?",
            target_file=data_map['S07'][0]
        ),
        Question(
            id="S08",
            category="spacing",
            text=f"Quante righe vuote ci sono sopra un commento?",
            target_file=data_map['S08'][0]
        ),
        Question(
            id="S09",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo un commento?",
            target_file=data_map['S09'][0]
        ),
        Question(
            id="S10",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo ogni import o blocco di import?",
            target_file=data_map['S10'][0]
        ),
        Question(
            id="S11",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una classe?",
            target_file=data_map['S11'][0]
        ),
        Question(
            id="S12",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una costante o di un blocco di costanti?",
            target_file=data_map['S12'][0]
        ),
        Question(
            id="N01",
            category="naming",
            text=f"Quanti elementi sono nominati con metodologia snake_case?",
            target_file=data_map['N01'][0]
        ),
        Question(
            id="N02",
            category="naming",
            text=f"Quanti elementi sono nominati con metodologia camelCase?",
            target_file=data_map['N02'][0]
        ),
        Question(
            id="N03",
            category="naming",
            text=f"Quanti elementi sono nominati con metodologia PascalCase?",
            target_file=data_map['N03'][0]
        ),
        Question(
            id="N04",
            category="naming",
            text=f"Qual è la metodologia più utilizzata per nominare gli elementi di questo script?",
            target_file=data_map['N04'][0]
        ),
        Question(
            id="N05",
            category="naming",
            text=f"Quale metodologia di denominazione è stata utilizzata in questo caso: {data_map['N05'][2]}?",
            target_file=data_map['N05'][0]
        ),
        # Question(
        #     id="N06",
        #     category="naming",
        #     text=f"Nel caso della denominazione di una costante, vengono utilizzati underscore per separare le parole (es. MY_CONSTANT)?",
        #     target_file=None
        # )
    ]