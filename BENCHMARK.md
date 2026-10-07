# BENCHMARK — FreeCAD standard vs FreeCAD Forge

Per ogni scenario: passaggi necessari (azioni dell'utente) e fallimenti/esiti sbagliati.
"Standard" = upstream @ 82d3fa0; "Forge" = branch `forge`. I casi di M3 sono verificati da
`ForgeTests.TestForgeRobustness` (eseguibile con `FreeCADCmd -t ForgeTests.TestForgeRobustness`).

## M1 — Interfaccia

| Scenario | Standard: passaggi | Forge: passaggi | Note |
|---|---|---|---|
| Parte con schizzo, estrusione, raccordo e messa in tavola | ≥ 3 cambi di workbench (Part Design → Sketcher automatico → TechDraw) | 0 cambi di workbench | Schede contestuali + modifica schizzo in Forge |
| Tornare indietro nella storia del corpo di 2 feature | Selezionare la feature + "Imposta punta" (2 azioni) | Trascinare il cursore Rollback (1 azione) o 2 clic su "indietro" | |
| Viste standard / adatta | Tasti 0–6, "V, F" (diversi da SolidWorks) | Ctrl+1…Ctrl+8, F (come SolidWorks) | Dopo "Impostazioni stile SolidWorks" |

## M3 — Robustezza (blocco 20×10×10)

| Scenario | Standard | Forge |
|---|---|---|
| Raccordo r=6 su tutti gli spigoli | Feature "valida", solido **non valido, volume −2718** | Errore: "radius is probably too large…" |
| Raccordo r=2 su tutti gli spigoli | Valido | Valido (invariato) |
| Smusso 6 su tutti gli spigoli | Errore criptico "BRep_API: command not done" | Errore (invariato in C++; spiegazione in italiano: vedi M3.2) |
| Guscio con parete 5 | Feature "valida", solido **non valido** | Errore: "not a valid solid…" |
| Guscio con parete 6 o 9 | Feature "valida" che **non fa nulla** | Errore: "had no effect…" |
| Guscio con parete 1, 4, 4,9 | Valido, volume corretto | Valido, volume corretto (invariato) |
| Sformo 60° sui lati | Errore con **messaggio vuoto** | Errore con spiegazione |

Fallimenti silenziosi (risultato sbagliato senza errore) su questa suite: **standard 3, Forge 0**.
