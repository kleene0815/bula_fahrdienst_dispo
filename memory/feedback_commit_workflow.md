---
name: feedback_commit_workflow
description: Wann und wie Commits erstellt werden sollen
metadata:
  type: feedback
---

Immer erst testen lassen, bevor committet wird. Nie proaktiv nach dem Fertigstellen einer Änderung committen oder pushen — der Nutzer gibt explizit Bescheid, wenn er bereit ist.

**Why:** Der Nutzer möchte Änderungen selbst im laufenden System prüfen, bevor sie ins Repository wandern.

**How to apply:** Nach Abschluss einer Implementierung fragen, ob getestet werden soll / Hinweis geben dass man testen kann — aber nicht von sich aus `git commit` oder `git push` ausführen.
