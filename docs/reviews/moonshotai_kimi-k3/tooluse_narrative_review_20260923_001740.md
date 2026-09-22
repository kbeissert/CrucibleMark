**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:17:40


Bedingt deploy, weil die Tool-Ausführung stark ist und keine Halluzination erkannt wurde, aber der invalide Tool-Call bei insgesamt gutem Ergebnis das Vertrauen in eine unbeaufsichtigte MCP-Pipeline begrenzt.

**Tool-Execution-Profil**

Kimi K3 zeigt klare Orchestrierungsstärke. Die Tool-Ausführung ist mit P1 88.33 belastbar, aber nicht sauber genug für eine Null-Aufsicht-Freigabe, weil mindestens ein Tool-Call nicht valide war. Entscheidend ist die Werkzeugwahl: Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis search statt fetch gewählt wird, trifft das Modell die richtige Entscheidung sehr sicher. Das spricht gegen starres Musterverhalten und für echte Tool-Selektion. Beim URL-Construction-and-Fetch-Test, der die eigenständige Ableitung einer Ziel-URL misst, bleibt es brauchbar, aber weniger deterministisch. Genau dort zeigt sich die Grenze: K3 plant gut, aber die letzte Meile der Call-Präzision ist nicht konstant genug für strikt schema- oder URL-sensitive Systeme. Positiv ist, dass kein Retry erforderlich war. Das wirkt eher wie ein punktuelles Protokoll- oder Präzisionsproblem als wie ein grundlegendes Verständnisdefizit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht stark genug für hochkritische Wissenspipelines. P2 73.33 zeigt brauchbare Zusammenfassung über alle Assets hinweg, mit sichtbar schwächerer Verdichtung bei EU License Research und Multilingual Search and Synthesis. K3 extrahiert und verbindet Informationen ordentlich, verliert aber bei Compliance-naher oder sprachübergreifender Verdichtung an Schärfe.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser als die Verdichtungsnote. Im EU-License-Research-Honeypot, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das Modell bleibt also grundsätzlich in der Tool-Spur. Die P2-60 zeigt eher ungenaue Verdichtung als unerlaubtes Ausweichen auf Vorwissen.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Ersatzinhalt verlangt, halluziniert K3 keinen Seiteninhalt. P2 80 ist hier das richtige Signal: Das Modell kommuniziert Fehlschläge ausreichend klar und beschädigt die Pipeline nicht durch fingierte Resultate.

**Betriebsprofil**

Total 140.95s pro Run. Call 1: 7.39s. MCP-Latenz: 1.19s. Call 2: 14.91s. Für die gezeigte Leistung eher langsam. Kosten/Run: local.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungspipelines mit menschlicher Abnahme oder nachgelagerter Validierung, besonders wenn Tool-Wahl wichtiger ist als perfekte Endverdichtung. Nicht die erste Wahl für vollautomatische Compliance-, Registry- oder URL-sensitive Workflows, in denen jeder Call protokolltreu und jeder Syntheseschritt exakt sein muss. Bei Cloud-Nutzung kommt ein erhebliches Jurisdiktionsrisiko hinzu; für sensible Daten ist nur ein streng kontrolliertes, selbst betriebenes Setup vertretbar.