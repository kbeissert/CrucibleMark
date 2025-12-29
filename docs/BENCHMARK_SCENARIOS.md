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

---

## 📚 Modul: Documentation Quality

In diesem Modul übernimmt das KI-Modell die Rolle eines **Technical Writers**. Es muss unvollständige, veraltete oder schlecht strukturierte Dokumentation analysieren und in hilfreiche, präzise und nutzerfreundliche Anleitungen verwandeln.

### Szenario 1: Die unbrauchbare README (README Quality)
**Die Situation:** Ein Open-Source-Projekt hat eine README-Datei, die nur aus einem Satz und einem Installationsbefehl besteht. Nutzer wissen nicht, was das Tool macht, welche Voraussetzungen nötig sind oder wie man es konfiguriert.
**Die Aufgabe:** Das Modell muss die fehlenden Sektionen (Installation, Usage, Configuration, Contributing) identifizieren und eine vollständige, professionelle README schreiben.
**Was wird geprüft:** Strukturierung, Vollständigkeit, Best Practices für Open Source.

### Szenario 2: Die lückenhafte API-Doku (REST API Documentation)
**Die Situation:** Ein Backend-Entwickler hat einen API-Endpunkt dokumentiert, aber wichtige Details vergessen: Welche Authentifizierung wird benötigt? Welche Fehlercodes können auftreten? Wie sieht ein Beispiel-Request aus?
**Die Aufgabe:** Das Modell muss die Dokumentation vervollständigen, Sicherheitslücken in der Beschreibung finden und klare Beispiele für Request und Response liefern.
**Was wird geprüft:** Technisches Verständnis von REST-APIs, Genauigkeit, Developer Experience (DX).

### Szenario 3: Die Komponente ohne Anleitung (Component Props)
**Die Situation:** Eine React-Komponente in einer Design-System-Bibliothek hat viele Einstellungsmöglichkeiten (Props), aber niemand weiß, was sie tun oder welche Datentypen erwartet werden.
**Die Aufgabe:** Das Modell muss eine klare Tabelle aller Props erstellen, Typen (TypeScript) definieren und erklären, wann man welche Einstellung verwendet.
**Was wird geprüft:** Verständnis von Frontend-Code, Präzision, Dokumentation von Schnittstellen.

### Szenario 4: Das frustrierende Setup (Setup Guide & Troubleshooting)
**Die Situation:** Neue Entwickler brauchen Stunden, um das Projekt lokal zum Laufen zu bringen, weil die Anleitung Schritte überspringt oder bekannte Fehler verschweigt ("Works on my machine").
**Die Aufgabe:** Das Modell muss eine schrittweise Anleitung erstellen, die auch Voraussetzungen prüft und Lösungen für häufige Probleme (Troubleshooting) direkt mitliefert.
**Was wird geprüft:** Empathie für Einsteiger, Antizipation von Fehlern, Didaktik.

### Szenario 5: Der kryptische Changelog (Release Notes)
**Die Situation:** Ein neues Software-Update wird veröffentlicht, aber die "Release Notes" sind nur eine Liste von technischen Git-Commit-Nachrichten ("fix: bug in regex"), die kein normaler Nutzer versteht.
**Die Aufgabe:** Das Modell muss diese technischen Details in verständliche "User Benefits" übersetzen und klar zwischen neuen Features, Fehlerbehebungen und kritischen Änderungen (Breaking Changes) unterscheiden.
**Was wird geprüft:** Übersetzung von Tech zu Business, Priorisierung von Informationen, Semantic Versioning.
