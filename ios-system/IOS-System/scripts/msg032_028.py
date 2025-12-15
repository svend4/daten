"""
Prepare test dataset from real SGB-IX documents
"""

import os
import shutil
from pathlib import Path

# Create test data directory
TEST_DATA_DIR = Path("test_data/sgb_ix")
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Document categories
categories = {
    "gesetze": [],  # Laws
    "widersprueche": [],  # Objections
    "antraege": [],  # Applications
    "bescheide": [],  # Decisions
    "urteile": [],  # Court decisions
}

def create_sample_documents():
    """Create sample documents for testing"""
    
    # Sample 1: Widerspruch
    widerspruch = TEST_DATA_DIR / "widerspruch_001.txt"
    widerspruch.write_text("""
Widerspruch gegen Bescheid vom 15.11.2024

Sehr geehrte Damen und Herren,

hiermit widerspreche ich dem Bescheid des Sozialamts München vom 15.11.2024
über die Ablehnung des Persönlichen Budgets gemäß § 29 SGB IX.

Begründung:

Die Ablehnung ist rechtswidrig. Die Voraussetzungen für die Gewährung eines
Persönlichen Budgets nach § 29 Absatz 1 SGB IX sind erfüllt.

Ich habe Anspruch auf Leistungen zur Teilhabe gemäß § 99 SGB IX. Diese
Leistungen können und sollen als Persönliches Budget erbracht werden.

Die Zuständigkeit liegt beim Bezirk Oberbayern gemäß § 98 SGB IX.

Ich beantrage:
1. Aufhebung des Bescheids vom 15.11.2024
2. Bewilligung des Persönlichen Budgets in Höhe von 2.500 € monatlich
3. Erstattung der Kosten für dieses Widerspruchsverfahren

Mit freundlichen Grüßen
Max Mustermann
München, 20.11.2024
    """)
    
    # Sample 2: Antrag
    antrag = TEST_DATA_DIR / "antrag_001.txt"
    antrag.write_text("""
Antrag auf Gewährung eines Persönlichen Budgets

Antragsteller: Max Mustermann
Adresse: Musterstraße 1, 80333 München
Geburtsdatum: 01.01.1990

Sehr geehrte Damen und Herren,

hiermit beantrage ich gemäß § 29 SGB IX die Gewährung eines Persönlichen
Budgets für folgende Leistungen zur Teilhabe:

1. Assistenzleistungen im Haushalt: 1.200 € monatlich
2. Assistenz für Mobilität: 800 € monatlich
3. Teilhabe am Arbeitsleben: 500 € monatlich

Gesamtsumme: 2.500 € monatlich

Begründung:
Ich bin aufgrund meiner Behinderung auf umfassende Assistenzleistungen
angewiesen. Das Persönliche Budget ermöglicht mir eine selbstbestimmte
Lebensführung gemäß dem Wunsch- und Wahlrecht nach § 8 SGB IX.

Zuständigkeit:
Gemäß § 98 SGB IX ist der Bezirk Oberbayern zuständig.

Anlagen:
- Schwerbehindertenausweis
- Ärztliche Bescheinigungen
- Kostenaufstellung

Mit freundlichen Grüßen
Max Mustermann
München, 01.10.2024
    """)
    
    # Sample 3: Bescheid
    bescheid = TEST_DATA_DIR / "bescheid_001.txt"
    bescheid.write_text("""
BESCHEID

Bezirk Oberbayern
Sozialverwaltung
Maximilianstraße 1
80333 München

Bescheid über Bewilligung von Eingliederungshilfe

Aktenzeichen: EGH-2024-12345
Datum: 01.12.2024

Antragsteller: Max Mustermann
Geburtsdatum: 01.01.1990
Adresse: Musterstraße 1, 80333 München

Sehr geehrter Herr Mustermann,

Ihr Antrag auf Leistungen der Eingliederungshilfe nach dem SGB IX vom
01.10.2024 wird bewilligt.

Es werden folgende Leistungen gewährt:

1. Assistenzleistungen im Haushalt
   Bewilligungszeitraum: 01.01.2025 - 31.12.2025
   Umfang: 1.200 € monatlich

2. Assistenz für Mobilität
   Bewilligungszeitraum: 01.01.2025 - 31.12.2025
   Umfang: 800 € monatlich

Rechtsgrundlagen: § 99, § 78, § 113 SGB IX

Die Leistungen werden als Persönliches Budget gemäß § 29 SGB IX erbracht.
Die monatliche Auszahlung erfolgt im Voraus zum 1. eines jeden Monats.

Rechtsbehelfsbelehrung:
Gegen diesen Bescheid kann innerhalb eines Monats nach Bekanntgabe
Widerspruch eingelegt werden.

Mit freundlichen Grüßen
Im Auftrag

Dr. Schmidt
Bezirk Oberbayern
Sozialverwaltung
    """)
    
    print("✓ Sample documents created")
    print(f"  Location: {TEST_DATA_DIR}")
    print(f"  Files: {len(list(TEST_DATA_DIR.glob('*.txt')))}")

if __name__ == "__main__":
    create_sample_documents()