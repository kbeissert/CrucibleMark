**Deployment-Urteil**

> **Erstellt am:** 22.06.2026, 21:34:20


Bedingt deploy, weil das Modell zwar keine Halluzinationen zeigt, aber kein durchgängig valides Tool-Calling liefert und die Gesamteignung mit 68.83 nur moderat ausfällt.

**Tool-Execution-Profil**

Codestral 25.08 trifft die Werkzeugwahl oft richtig, ist aber in der Ausführung nicht stabil genug für hochdeterministische MCP-Pipelines. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, erkennt es den Bedarf für web_search zuverlässig. Das spricht gegen ein rein starres Muster und für brauchbare Tool-Intelligenz. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt, bleibt es brauchbar, aber nicht präzise genug für Pipelines, die auf reproduzierbare Fetch-Pfade angewiesen sind. Der Befund tool_call_valid=false ist hier der operative Kern: Das Modell ist nicht protokollunsicher im Sinn von chaotisch, aber es produziert nicht konsistent die Art von gültigen Calls, die man unbeaufsichtigt in kritische Automationen geben will. Retry war nicht nötig. Das spricht eher für ein Präzisionsproblem in der Tool-Nutzung als für ein grundlegendes Formatversagen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung von 56.67 zeigt ein wiederkehrendes Problem in der Verdichtung und im sauberen Zusammenführen von Rechercheergebnissen. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis: Es beschafft Informationen, verdichtet sie aber nicht mit der Klarheit und Trennschärfe, die Produktionsnutzer für belastbare Entscheidungsoutputs brauchen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt es vertrauenswürdig. P2=40 ist schwach, aber Halluzinationen wurden nicht erkannt. Das ist wichtig: Das Modell erfindet hier keine Compliance-Fakten. Es verdichtet schlecht, aber es bricht nicht die Quelle-zu-Antwort-Kette.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem fehlschlagenden Abruf misst, halluziniert Codestral 25.08 keinen Ersatzinhalt. Das ist der zentrale Produktionspunkt. Die Kommunikation des Fehlers ist jedoch nicht stark genug, um als robuste Incident-Ausgabe zu gelten. P2=40 heißt: akzeptabel für überwachte Pipelines, nicht ausreichend für autonome Fehlerpfade.

**Souveränitätsprofil**

Lokal betreibbar und damit souverän einsetzbar. Combined 68.83 liegt 0.90 Punkte über dem Fleet-Ø von 67.93. Kein Souveränitätsabschlag erkennbar.

**Fazit & Empfehlung**

Geeignet für lokale, MCP-gestützte Coding- und Recherchepipelines mit menschlicher Nachkontrolle, besonders wenn Quellentreue wichtiger ist als elegante Ergebnisverdichtung. Nicht geeignet für Compliance-nahe, vollautonome oder stark deterministische Tool-Ketten, in denen jeder Call formal gültig sein und jede Synthese direkt weiterverarbeitet werden muss. Als ausführendes Code-Modell mit Web-Zugriff ist es nutzbar. Als verlässlicher Endpunkt einer unbeaufsichtigten Tool-Infrastruktur noch nicht.