# 📖 Benchmark-Szenarien: Was wird eigentlich getestet?

Dieses Dokument erklärt die Benchmarks von CrucibleMark anhand von realen Szenarien. Es soll verständlich machen, welche Fähigkeiten der KI-Modelle geprüft werden, ohne tief in den Programmcode einzusteigen.

Für technische Details und Implementierungen siehe die jeweiligen Modul-Dokumentationen:
- [Code Quality Module](../benchmark_modules/code_quality/README.md)
- [UX Writing Module](../benchmark_modules/ux_writing/README.md)

---

## 🛠️ Modul: Code Quality Audit

In diesem Modul schlüpft das KI-Modell in die Rolle eines **Senior Developers**, der den Code von Junior-Kollegen überprüft (Code Review). Es geht nicht nur darum, Fehler zu finden, sondern diese auch korrekt zu erklären und bessere Lösungen vorzuschlagen.

### Szenario 1: Der Accessibility-Check (WCAG Audit)
**Die Situation:** Ein Junior-Entwickler hat eine Produktkarte für einen Online-Shop gebaut. Sie sieht optisch gut aus, ist aber für blinde Menschen (Screenreader-Nutzer) oder Tastatur-Nutzer kaum bedienbar.
**Die Aufgabe:** Das Modell muss erkennen, dass z.B. Bilder keine Beschreibungen haben, Buttons mit der Tastatur nicht erreichbar sind oder Farben zu wenig Kontrast haben. Es muss den Code so korrigieren, dass er den strengen WCAG 2.2 Richtlinien entspricht.
**Was wird geprüft:** Kenntnis von Barrierefreiheit, HTML-Semantik und Empathie für eingeschränkte Nutzergruppen.

### Szenario 2: Die Sicherheitslücke (Security Audit)
**Die Situation:** Ein Entwickler hat eine Funktion geschrieben, um Benutzerdaten zu speichern. Dabei hat er aus Unwissenheit eine Hintertür offen gelassen, durch die Hacker Datenbankbefehle einschleusen könnten (SQL Injection).
**Die Aufgabe:** Das Modell muss diese kritische Sicherheitslücke sofort erkennen, erklären *warum* sie gefährlich ist, und den Code so umschreiben, dass er sicher ist.
**Was wird geprüft:** Erkennung von Sicherheitsrisiken (OWASP Top 10), Secure Coding Practices.

### Szenario 3: Die langsame Webseite (Performance Audit)
**Die Situation:** Eine Webseite lädt extrem langsam, weil eine Funktion ineffizient programmiert wurde (z.B. wird eine Liste tausendfach unnötig neu berechnet).
**Die Aufgabe:** Das Modell muss den "Flaschenhals" im Code finden und eine optimierte Version schreiben, die deutlich schneller läuft, ohne die Funktion zu verändern.
**Was wird geprüft:** Algorithmisches Verständnis, Effizienz, Big-O-Notation.

### Szenario 4: Das schlechte API-Design
**Die Situation:** Ein Backend-Entwickler hat eine Schnittstelle (API) entworfen, die chaotisch ist. URLs sind unlogisch benannt, Fehlercodes werden falsch verwendet (z.B. "200 OK" obwohl ein Fehler passierte).
**Die Aufgabe:** Das Modell muss das Design kritisieren und eine saubere, standardkonforme REST-API-Struktur vorschlagen.
**Was wird geprüft:** Architektur-Verständnis, API-Standards (REST), Konsistenz.

### Szenario 5: Der "Spaghetti-Code" (Code Smells)
**Die Situation:** Ein Stück Code ist über Jahre gewachsen, extrem verschachtelt, Variablen haben Namen wie `x` und `temp`, und niemand versteht mehr, was passiert.
**Die Aufgabe:** Das Modell muss den Code aufräumen ("Refactoring"), sprechende Namen vergeben und die Struktur vereinfachen, damit er wieder wartbar ist.
**Was wird geprüft:** Clean Code Prinzipien, Lesbarkeit, Wartbarkeit.

---

## ✍️ Modul: UX Writing & Microcopy

Hier agiert das KI-Modell als **UX Writer**. Es geht darum, technische oder unklare Texte in eine Sprache zu übersetzen, die Nutzer verstehen, motiviert und führt.

### Szenario 1: Die kryptische Fehlermeldung
**Die Situation:** Ein Nutzer will bezahlen, aber es klappt nicht. Das System spuckt aus: `Error 503: Transaction failed due to timeout in payment gateway backend.` Der Nutzer ist verwirrt und frustriert.
**Die Aufgabe:** Das Modell muss diesen technischen Kauderwelsch in eine hilfreiche Nachricht übersetzen, z.B.: "Hoppla, da hat etwas nicht geklappt. Deine Zahlung wurde nicht abgebucht. Bitte versuche es in ein paar Minuten noch einmal."
**Was wird geprüft:** Empathie, Übersetzung von "Tech" zu "Mensch", Lösungsfokussierung.

### Szenario 2: Der Button ohne Kontext
**Die Situation:** In einem Dialogfenster steht die Frage "Möchten Sie den Vorgang wirklich abbrechen?" und die Buttons heißen nur "Ja" und "Nein". Der Nutzer muss die Frage genau lesen, um nicht das Falsche zu klicken.
**Die Aufgabe:** Das Modell soll die Buttons so beschriften, dass sie für sich selbst sprechen, z.B. "Vorgang abbrechen" und "Bearbeitung fortsetzen".
**Was wird geprüft:** Klarheit, kognitive Entlastung des Nutzers.

### Szenario 3: Das erste Mal (Onboarding Flow)
**Die Situation:** Ein neuer Nutzer öffnet eine komplexe App zum ersten Mal. Er weiß nicht, wo er anfangen soll.
**Die Aufgabe:** Das Modell muss eine kurze, dreiteilige Tour schreiben, die den Nutzer freundlich begrüßt und ihm die wichtigsten Funktionen erklärt, ohne ihn mit Text zu erschlagen.
**Was wird geprüft:** Didaktik, Motivation, Kürze ("Microcopy").

### Szenario 4: Texte für die Ohren (Accessibility Labels)
**Die Situation:** Ein blinder Nutzer navigiert mit einem Screenreader durch eine App. Er kommt auf einen Button, der nur ein Icon (einen Mülleimer) zeigt. Der Screenreader liest vor: "Button 43". Der Nutzer weiß nicht, was passiert, wenn er klickt.
**Die Aufgabe:** Das Modell muss unsichtbare Beschriftungen (ARIA-Labels) schreiben, die dem Screenreader sagen: "Eintrag löschen".
**Was wird geprüft:** Technisches Verständnis von Barrierefreiheit, präzise Beschreibung.

### Szenario 5: Der Ton macht die Musik (Microcopy Audit)
**Die Situation:** Eine Gesundheits-App, die eigentlich vertrauenswürdig wirken soll, nutzt eine viel zu lockere oder aggressive Sprache ("Hey Kumpel, hast du heute schon Sport gemacht?!").
**Die Aufgabe:** Das Modell muss erkennen, dass dieser Tonfall im Kontext "Gesundheit" unpassend ist und die Texte seriöser und einfühlsamer umschreiben.
**Was wird geprüft:** Tonalität (Tone of Voice), Kontextverständnis.
