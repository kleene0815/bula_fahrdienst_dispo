---
name: feedback_development_workflow
description: "Verbindlicher Entwicklungsprozess für dieses Projekt — Reihenfolge von Doku, Planung, Umsetzung und Commit"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1f1015a8-625a-4a8b-b1bf-7a511393b358
---

Neues Feature oder Erweiterung immer in dieser Reihenfolge angehen:

1. **Erweiterungswünsche sammeln** und verständlich in `README.md` dokumentieren.
2. **Gemeinsam priorisieren**: Mit dem User besprechen, in welcher Reihenfolge die Wünsche am besten angegangen werden. Danach die TODO-Liste in Arbeitspakete gruppieren.
3. **Paket für Paket abarbeiten** — nie alles auf einmal.
4. **Vor dem Commit**:
   - Erledigte Todos abhaken.
   - Wenn ein komplettes Arbeitspaket abgeschlossen ist, dieses in den Abschnitt „Abgeschlossen" der TODO-Liste verschieben.
   - Erst danach committen.

**Why:** Der User möchte klare Struktur und Nachvollziehbarkeit — jeder Commit spiegelt einen abgeschlossenen, dokumentierten Schritt wider.

**How to apply:** Bei jeder Anfrage zu neuen Features oder Änderungen diesen Ablauf einhalten. Nie direkt mit der Implementierung starten, ohne Doku und Planung abgestimmt zu haben. Nie committen, ohne die TODO-Liste aktualisiert zu haben.
