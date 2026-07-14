# Ein Zufall, ein Vogel und die Frage, wer die Gutachter bewertet

*Entwurf für cruciblemark.com/magazine — Mai 2026*

---

Es begann, wie so vieles in diesem Projekt, mit einem Fehler.

In meiner lokalen Rechnerumgebung laufen seit einiger Zeit mehrere KI-Modelle gleichzeitig. Einige davon für den Benchmark. Andere für alltägliche Aufgaben. Eines davon ist **qwen2.5vl**, ein Modell von Alibaba, das ich ursprünglich für die Bilderkennung in SwarmUI eingerichtet hatte. SwarmUI ist eine Benutzeroberfläche zur Bildgenerierung — und qwen2.5vl ist dort sehr gut darin, generierte Bilder zu analysieren und zu beschreiben. Es ist ein sogenanntes Vision-Language-Modell: ein Modell, das Text und Bilder gleichzeitig versteht.

Das Problem entstand, als das Modell bei einem automatischen Benchmark-Lauf auftauchte, der ausschließlich Textaufgaben enthielt. Nicht wegen einer falschen Konfiguration im Benchmark-Framework. Sondern weil Ollama — das Programm, über das lokale KI-Modelle verwaltet werden — das Modell einfach als verfügbar meldete. Der Benchmark fragte, welche Modelle laufen. Ollama antwortete. qwen2.5vl stand auf der Liste. Also wurde es getestet.

Das Ergebnis war erwartungsgemäß durchwachsen. Das Modell erreichte 51,46 Prozent — ein Wert im untersten Drittel. Aber nicht weil es schlecht ist. Sondern weil es für eine völlig andere Aufgabe entwickelt wurde. Ein Fisch, der an einem Klettergerüst bewertet wird, wirkt ungeschickt. Das sagt nichts über seine Fähigkeiten im Wasser.

Dieser Zufallsbenchmark legte eine Schwachstelle offen, die ich schon länger ahnte, aber bequem ignoriert hatte.

---

## Das Problem mit den Karteikarten

Jedes Modell, das CrucibleMark testet, hat eine sogenannte **Model Card** — eine strukturierte Karteikarte mit allen relevanten Informationen zum Modell. Wer hat es entwickelt? Wie groß ist es? Für welchen Zweck ist es optimiert? Welche Lizenz hat es?

Klingt überschaubar. Ist es in der Theorie auch. In der Praxis hatte sich über Monate hinweg ein Problem aufgebaut, das ich am besten als "viele Zettel, keine Ordnung" beschreiben würde.

Die Informationen zu den Modellen waren verstreut. Manche standen in der zentralen Konfigurationsdatei. Manche im Leaderboard-CSV, der Rangliste aller getesteten Modelle. Manche nirgendwo explizit — sie wurden im Code stillschweigend vorausgesetzt. Das funktioniert, solange alles ruhig bleibt. Es bricht zusammen, sobald ein Modell auftaucht, das nicht in das erwartete Schema passt.

qwen2.5vl war genau ein solches Modell. Der automatisch generierte Review-Text für das Modell enthielt keine Einordnung, dass es ein Bildverständnis-Modell ist, das in einem reinen Textbenchmark antritt. Der Reviewer — ein anderes KI-Modell, das die Testergebnisse in einen lesbaren Bericht umwandelt — wusste das schlicht nicht. Niemand hatte es ihm gesagt.

Das ist der Kern des Problems, und er hat einen Namen: **fehlende Single Source of Truth**.

Single Source of Truth ist ein Konzept aus der Softwareentwicklung. Es bedeutet: Es gibt genau eine Stelle, an der eine Information gespeichert ist. Alle anderen Teile des Systems lesen von dieser einen Stelle. Kein Kopieren, kein Verteilen, kein "ich glaube, das stand irgendwo". Wenn sich etwas ändert, ändert man es an einer Stelle — und alle anderen Teile reagieren automatisch.

Das klingt simpel. Es konsequent umzusetzen ist es nicht. Aber der Zufallsbenchmark von qwen2.5vl hatte mir gerade sehr deutlich gezeigt, was passiert, wenn man es nicht tut.

---

## Die Überarbeitung: Was eine Karteikarte wirklich wissen muss

Die Reaktion war eine vollständige Überarbeitung aller Model Cards. Nicht nur die Felder hinzufügen, die offensichtlich fehlten. Sondern grundsätzlich durchdenken: Was muss ein System, das einen fairen und nachvollziehbaren Review-Text generiert, über ein Modell wissen?

Die Antwort gliedert sich in drei Säulen, die ich für jedes der über 70 Modelle im Benchmark nachgezogen habe.

Die **erste Säule** ist der Einsatzzweck. Ist das Modell ein Generalist ohne besondere Spezialisierung? Oder ist es auf Code-Generierung optimiert? Auf tiefes logisches Denken? Auf die Verarbeitung von Bildern? Auf die Steuerung anderer KI-Systeme? Diese Information klingt selbstverständlich. Sie war es in der Praxis für viele Modelle nicht. Das Feld heißt jetzt `use_case_primary` und hat fünf mögliche Werte: Generalist, Coding, Reasoning, Vision-Language und Agentic. Letzteres beschreibt Modelle, die dafür trainiert wurden, andere KI-Modelle zu koordinieren — so wie ein Projektleiter, der selbst nicht die ganze Arbeit erledigt, aber die richtigen Leute damit beauftragt.

Die **zweite Säule** ist das Hardware-Tier. Für welche Art von Rechner ist das Modell gedacht? Ein Nano-Modell mit unter vier Milliarden Parametern läuft auf einem Smartphone. Ein Frontier-Modell ist nur über eine Cloud-Schnittstelle erreichbar, weil es schlicht zu groß ist für jede lokale Hardware. Dazwischen gibt es Edge-Modelle für leistungsfähige Laptops, Desktop-Modelle für Gaming-PCs und Workstation-Modelle für professionelle Hardwarestationen. Diese Einordnung bestimmt, an welchem Maßstab ein Modell fair gemessen werden kann.

Die **dritte Säule** ist die Parameterarchitektur. Die meisten Modelle sind sogenannte Dense-Modelle: Alle ihre Parameter — das sind die erlernten Gewichte, die das Denken des Modells ausmachen — sind bei jeder Anfrage aktiv. Neuere Modelle nutzen eine andere Technik, MoE genannt, was für Mixture of Experts steht. Das Prinzip: Das Modell besteht aus vielen spezialisierten Teilnetzwerken. Bei einer Anfrage werden nur die Teile aktiviert, die gerade gebraucht werden. Das macht MoE-Modelle effizienter — sie haben viele Parameter auf dem Papier, nutzen aber immer nur einen Bruchteil davon. Wer ein MoE-Modell an seiner Gesamtparameterzahl misst, vergleicht Äpfel mit Birnen.

Parallel dazu wurden alle 77 Modelle mit zwei weiteren Feldern aktualisiert: dem maximalen Kontextfenster (also wie viel Text ein Modell auf einmal lesen und verarbeiten kann) und dem Wissensstand (bis wann sein Trainingsmaterial datiert). Ein Modell, das nur bis Ende 2024 trainiert wurde, weiß schlicht nicht, was danach passiert ist. Das ist keine Schwäche — es ist eine Eigenschaft, die ein Reviewer kennen muss.

---

## Die Reviews: Wenn 30.000 Wörter auf eine Seite müssen

Der Benchmark erzeugt für jedes Modell detaillierte Protokolle. Pro Test-Durchlauf. Pro Modul. Mit den Bewertungen des LLM-Judges, den Rohscores, den Auffälligkeiten. Für ein vollständig getestetes Modell summieren sich diese Protokolle schnell auf 25.000 bis 35.000 Wörter reinen Rohtextes. Das entspricht einem kurzen Roman.

Aus diesem Rohtext soll automatisch ein lesbarer, journalistischer Review-Artikel entstehen. Ein Text wie die anderen Beiträge auf dieser Seite: mit Haltung, mit konkreten Befunden, mit einer klaren Empfehlung am Ende.

Das ist eine Aufgabe, für die ein gutes Sprachmodell genau das tun muss, was Sprachmodelle laut Werbung können: große Mengen Text zusammenfassen, Muster erkennen, Urteile formulieren.

Ich hatte bisher Claude als Reviewer eingesetzt — Anthropics KI-Assistenten, der auch diese Plattform mit aufgebaut hat. Die Ergebnisse waren gut. Aber mit der neuen Klassifikationsstruktur, dem erweiterten Reviewer-Prompt und dem Wunsch, die Kosten pro Review zu verstehen, stellte sich eine naheliegende Frage: Macht es wirklich Unterschiede, welches Modell die Reviews schreibt?

---

## Der Wettbewerb: Vier Kandidaten, ein Test, ein Sieger

Die Antwort auf diese Frage wollte ich nicht raten. Also habe ich es getestet.

Drei Frontier-Modelle — das sind die leistungsstärksten, ausschließlich über Cloud-Schnittstellen verfügbaren Modelle der jeweiligen Anbieter — erhielten denselben Auftrag: Schreib einen Review-Artikel über Grok 3, das Flaggschiff-Modell von xAI. Jedes Modell bekam dieselben Rohdaten, denselben Prompt, dieselben Rahmenbedingungen.

Die Kandidaten waren **Claude Sonnet 4.6** von Anthropic, **Gemini 3.1 Pro** von Google und **GPT-5.4** von OpenAI. Grok 3 als Testobjekt war kein Zufall. Es ist ein Generalist ohne besondere Spezialisierung, hat solide Stärken und klare Schwächen — und gehört nicht zur gleichen Anbieterfamilie wie einer der drei Reviewer. Das vermeidet den unangenehmen Verdacht, ein Modell würde einen Konkurrenten absichtlich schlechter bewerten.

Das Ergebnis war überraschend klar.

**Claude Sonnet 4.6** schrieb den analytisch tiefsten Text. Die Sicherheitsanalyse war besonders präzise. Der Ton war sachlich kompetent, aber mit einem leicht akademischen Zug — eher Fachzeitschrift als Magazin.

**Gemini 3.1 Pro** enttäuschte. Der Text war zu kurz, zu strukturlos und ohne erkennbare Autorenstimme. Manche Pflichtabschnitte fehlten. Der Schluss klang wie eine Zusammenfassung, kein Urteil. Lesbar als Notiz. Unbrauchbar als Artikel.

**GPT-5.4** überraschte am meisten — und gewann. Nicht weil der Text technisch vollständiger war. Sondern weil er am besten traf, was ein guter Review-Artikel können muss: Einen Befund so formulieren, dass ihn jemand ohne Vorerfahrung versteht und trotzdem das Wichtige mitnimmt.

Ein Beispiel aus dem GPT-Text über Grok 3: *„Wer Risiken falsch priorisiert, sortiert den Löschzug nach Lackfarbe."* Das braucht keine Erklärung. Ein anderes Beispiel, zur Frage warum das Modell im Werkszustand getestet wurde und nicht mit aktiviertem Denkmodus: *„Man sieht das Serienauto, nicht die Rennstrecken-Konfiguration."* Auch hier: sofort verständlich, trotzdem präzise.

Dazu kam: GPT-5.4 verwendete in seinem gesamten Artikel exakt einen Gedankenstrich. Das war kein Zufall, sondern das Ergebnis einer expliziten Anweisung im Reviewer-Prompt, die ich im Laufe dieser Überarbeitungsrunde eingebaut hatte.

---

## Was dabei gelernt wurde

Dieser Prozess hat drei Dinge sichtbar gemacht, die vorher im Verborgenen lagen.

Erstens: Die Qualität eines automatisch generierten Textes hängt massiv davon ab, wie gut das System über das Objekt informiert ist, über das es schreiben soll. Das klingt banal. Es ist es nicht. Die neuen Model Cards sind nicht nur bessere Datenblätter. Sie sind der Unterschied zwischen einem Reviewer, der ein Modell versteht, und einem, der blind in Protokolldaten tippt.

Zweitens: Nicht alle Frontier-Modelle sind gleich gut in der Textproduktion für spezifische Aufgaben — selbst wenn sie in allgemeinen Benchmarks ähnlich abschneiden. GPT-5.4 ist für das, was CrucibleMark braucht, schlicht besser geeignet. Das ist kein Urteil über generelle Intelligenz. Es ist ein Befund für eine konkrete Aufgabe: strukturierte Rohdaten in zugänglichen Journalismus zu übersetzen.

Drittens: Ein versehentlicher Benchmark kann der produktivste Benchmark sein. qwen2.5vl hat nichts in diesem Test zu suchen gehabt. Dass es trotzdem aufgetaucht ist, hat eine überfällige Systemüberarbeitung ausgelöst, die das Framework deutlich robuster gemacht hat.

Das Modell selbst? Es arbeitet weiterhin zuverlässig in SwarmUI. Es analysiert Bilder, beschreibt Bildkompositionen und hilft beim Verfeinern von Bildgenerierungs-Prompts. Genau das, wofür es gebaut wurde.

Manchmal muss ein Fisch ins falsche Wasser geraten, damit man versteht, warum das Aquarium so aussieht, wie es aussieht.

---

*CrucibleMark ist ein unabhängiges Benchmark-Framework für Sprachmodelle. Alle Testergebnisse und Modell-Reviews sind öffentlich einsehbar unter cruciblemark.com.*
