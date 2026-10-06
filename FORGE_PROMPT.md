# Progetto: "FreeCAD Forge" — fork personale di FreeCAD con flusso di lavoro e completezza in stile SolidWorks

## Il tuo ruolo e l'obiettivo
Sei un ingegnere software senior esperto di CAD, OpenCASCADE, Qt e della base di codice di FreeCAD. Il tuo obiettivo è trasformare un fork di FreeCAD in un CAD parametrico per uso personale che sia, nell'uso quotidiano, più completo, più robusto e più coerente di FreeCAD standard, avvicinandosi il più possibile al flusso di lavoro e alle funzionalità di SolidWorks. Lavori in autonomia attraverso le milestone. Ti fermi a chiedermi qualcosa solo per blocchi esterni (dipendenze, risorse della macchina) o per decisioni irreversibili.

## Contesto e vincoli
- Uso esclusivamente personale, nessuna distribuzione: puoi integrare liberamente codice GPL/LGPL (addon FreeCAD, SolveSpace, ecc.). Registra comunque ogni fonte in THIRD_PARTY.md.
- Niente asset di Dassault Systèmes (icone, loghi, nome): riproduci i concetti di interazione con grafica originale. Niente reverse engineering dei formati .SLDPRT/.SLDASM: l'interoperabilità passa da STEP/IGES/STL/3MF/DXF.
- Mantieni il fork aggiornabile rispetto a upstream: preferisci implementare il nuovo codice come workbench o modulo separato ("ForgeWorkbench") e limita le patch al core a quanto strettamente necessario. Ogni patch al core va documentata in CORE_PATCHES.md con il motivo.

## Fase 0 — Setup
1. Clona https://github.com/FreeCAD/FreeCAD, crea il branch "forge" e compila seguendo la documentazione ufficiale di build presente nel repository per il mio sistema operativo (rilevalo tu).
2. Verifica che la build si avvii e che la suite di test esistente giri. Annota in PROGRESS.md i tempi di build e i test che falliscono già in partenza (baseline).
3. Studia l'architettura (App/Gui, PartDesign, Sketcher, Assembly, TechDraw, Part, Spreadsheet, FEM) e scrivi ARCHITECTURE_NOTES.md con i punti di intervento.

## Fase 1 — Analisi del divario (prima di scrivere codice)
Scrivi GAP_ANALYSIS.md: confronta, funzione per funzione, FreeCAD attuale con SolidWorks in queste aree: schizzo, feature di parte, multi-corpo, superfici, lamiera, saldature/profilati, assiemi, messa in tavola, configurazioni/equazioni, valutazione (misure, masse, interferenze, sformo, spessore), libreria di parti standard, rendering/aspetti, simulazione base, interoperabilità, interfaccia ed ergonomia. Per ogni voce indica: presente / parziale / assente / presente solo come addon; gravità del divario; stima di sforzo. Ordina poi le milestone qui sotto in base a questa analisi, privilegiando ciò che ha il maggior impatto sull'uso quotidiano.

## Milestone (ordine indicativo, da rivedere dopo GAP_ANALYSIS)
M1 — Interfaccia unificata in stile SolidWorks: un unico ambiente "Forge" senza cambio di workbench per parte, assieme e tavola. Command manager a schede contestuali (Schizzo, Feature, Superfici, Lamiera, Valuta, Assieme, Tavola). Albero delle feature con rollback bar trascinabile, cartelle, riordino con controllo delle dipendenze. Pannello proprietà contestuale con anteprima live e conferma/annulla. Navigazione mouse e scorciatoie configurabili sul modello SolidWorks. Mouse gestures e menu radiale contestuale. Barra "heads-up" nella vista.
M2 — Schizzo di livello professionale: quota intelligente unica (lineare/angolare/radiale in base alla selezione), inferenze più ricche durante il disegno, colori di stato chiari con diagnosi dei vincoli in conflitto e proposta di soluzioni, trascinamento fluido delle geometrie sottovincolate, blocchi di schizzo, schizzi 3D, testo nello schizzo.
M3 — Robustezza delle feature: individua e correggi i casi di fallimento più frequenti di raccordi, smussi, svuotamenti e booleane (crea una suite di modelli di prova "difficili"). Messaggi d'errore comprensibili sulla feature, con indicazione della geometria problematica e suggerimenti. Rigenerazione più veloce e incrementale dove possibile.
M4 — Feature mancanti o incomplete: foro guidato completo (ISO/UNI, filettature cosmetiche, svasature), drag handles in stile Instant3D per modificare le quote nella vista, configurazioni vere con tabella dati (soppressioni + parametri), gestore di equazioni e variabili globali unificato, pattern avanzati (guidati da curva, da schizzo, da tabella, con varianti), deforma/flessione, scritte in rilievo e incise.
M5 — Lamiera e saldature integrate: flangia base, flangia sul bordo, flangia a raccordo, piega, scarico, sviluppo in piano con export DXF e tabella di piega. Profilati strutturali con libreria UNI/EN, rifilatura e tabella dei tagli.
M6 — Assiemi in stile SolidWorks: accoppiamenti standard e avanzati (larghezza, limiti, ingranaggio, camma, vite, slot), "smart mates" con trascinamento e Alt, componenti flessibili, pattern di componenti, specchia componenti, viste esplose animate, rilevamento interferenze e giochi, modifica in contesto con riferimenti esterni gestibili, toolbox di viteria standard (integra l'addon Fasteners se conviene).
M7 — Messa in tavola più rapida: viste automatiche dal modello (palette delle viste), importazione delle quote di modello, quotatura automatica (ordinata/da riferimento), BOM collegata con palloncini automatici, fori con tabelle, cartiglio UNI/ISO con proprietà personalizzate, export PDF/DXF/DWG (se disponibile un convertitore utilizzabile).
M8 — Valutazione e produttività: proprietà di massa con libreria materiali, analisi di sformo, spessore e curvatura, sezioni dinamiche, confronto tra versioni di una parte, design library personale con trascinamento, autosalvataggio con ripristino, gestione dei riferimenti esterni e "Pack and Go".

## Metodo di lavoro
- Mantieni PROGRESS.md (stato attuale, prossimo passo, problemi noti) in modo che una nuova sessione possa riprendere leggendolo. Registra le decisioni in DECISIONS.md.
- Un commit per ogni task, un tag a fine milestone.
- Test: aggiungi test Python/C++ nel framework di test di FreeCAD per ogni funzione nuova o corretta, verificando proprietà geometriche oggettive (volume, area, numero di facce, validità del solido). Per ogni milestone crea in /forge_examples modelli di riferimento che riproducono esercizi tipici dei tutorial SolidWorks e verificano che si costruiscano senza errori.
- Metrica di successo: per ogni scenario di modellazione annota in BENCHMARK.md il numero di passaggi e i fallimenti in FreeCAD standard e nel fork. Il fork deve migliorare su entrambi.
- Niente funzioni finte né TODO silenziosi: se qualcosa non è realizzabile in modo affidabile, implementane una versione ridotta ma corretta e documenta il limite.
- Ogni 2 milestone esegui un rebase o merge da upstream e risolvi i conflitti, così da non perdere i miglioramenti ufficiali.

## Esecuzione non presidiata (cloud/server)
- Lavori su una macchina headless senza di me presente. Non attendere mie risposte: se una decisione non è bloccante, scegli l'opzione più ragionevole, documentala in DECISIONS.md e prosegui.
- Lancia le compilazioni lunghe in background con output su file di log (es. build.log) e controllane l'avanzamento, invece di attendere comandi bloccanti che possono andare in timeout. Usa ccache e build incrementali.
- Esegui i test in modalità console (FreeCADCmd) e, per i test che richiedono la GUI, usa xvfb-run.
- Fai commit e push sul branch "forge" almeno a ogni task completato: la macchina può essere riciclata in qualsiasi momento e ciò che non è pushato va perso.
- A ogni ripresa, la prima azione è leggere PROGRESS.md e verificare lo stato della build.
- Le modifiche all'interfaccia grafica non sono verificabili visivamente da te: per ognuna aggiungi in PROGRESS.md una voce "DA VERIFICARE A VIDEO" con i passi esatti che dovrò eseguire io.

## Consegna
Build funzionante e installabile sulla mia macchina, README.md in italiano con installazione, novità rispetto a FreeCAD e scorciatoie, GAP_ANALYSIS.md aggiornato con ciò che resta da fare.

Inizia dalla Fase 0.
