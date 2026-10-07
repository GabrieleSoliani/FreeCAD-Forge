# FreeCAD Forge

Fork personale di [FreeCAD](https://www.freecad.org) con un flusso di lavoro e una dotazione di
funzioni ispirati a SolidWorks: un unico ambiente "Forge" per parti, lamiera, saldature, assiemi e
tavole, errori comprensibili, strumenti di valutazione e produttività.

Uso esclusivamente personale. Il README originale di FreeCAD è in [README.FreeCAD.md](README.FreeCAD.md).
Stato dettagliato del lavoro: [PROGRESS.md](PROGRESS.md); confronto con SolidWorks e lavoro residuo:
[GAP_ANALYSIS.md](GAP_ANALYSIS.md); misure: [BENCHMARK.md](BENCHMARK.md).

## Installazione (Windows, compilazione locale)

Requisiti: [pixi](https://pixi.sh), Visual Studio Build Tools 2022 con il carico di lavoro C++,
Git, circa 40 GB liberi.

```
git clone https://github.com/GabrieleSoliani/FreeCAD-Forge.git
cd FreeCAD-Forge
git checkout forge
pixi run configure-rel-with-deb-info "-DENABLE_DEVELOPER_TESTS=ON"   # ~4 minuti
pixi run build                                                      # ~50 minuti la prima volta
pixi run install                                                    # installa nell'ambiente pixi
pixi run freecad                                                    # avvia FreeCAD Forge
```

`pixi run install` installa FreeCAD nella cartella `.pixi\envs\default\Library`; l'eseguibile è
`.pixi\envs\default\Library\bin\FreeCAD.exe` (avviarlo con `pixi run freecad` perché trovi le librerie).
Le compilazioni successive sono incrementali (ccache): pochi minuti.

Al primo avvio scegliere il workbench **Forge** (icona a incudine): Forge propone di applicare le
impostazioni in stile SolidWorks (navigazione, scorciatoie, Forge come ambiente iniziale); si possono
annullare in qualsiasi momento dal menu Forge → "Ripristina impostazioni precedenti".

## L'ambiente Forge

Una riga di schede sopra la vista, come il CommandManager di SolidWorks. La scheda cambia da sola
con il contesto (schizzo in modifica, tavola aperta, assieme attivo) e torna indietro all'uscita.

| Scheda | Contenuto |
|---|---|
| Schizzo | Nuovo/modifica schizzo, schizzo 3D, diagnosi schizzo; in modifica: disegno (linee, archi, rettangoli, asole, testo, raccordi, taglia, offset…) e vincoli (quota intelligente, coincidente, orizzontale/verticale…), blocchi |
| Feature | Corpo, estrusioni, rivoluzioni, loft, sweep, eliche, fori, raccordi, smussi, sformo, guscio, nervatura, serie, booleane, riferimenti, configurazioni, equazioni, rollback |
| Superfici | Estrusione, rivoluzione, loft, sweep, rigata, riempimento, sezioni, estensione, offset, ispessimento |
| Lamiera | Addon SheetMetal integrato: flangia base, flange, orli, pieghe, scarichi, giunzioni, sviluppo; tabella di piega; esportazione DXF dello sviluppo |
| Saldature | Schizzo 3D, profilati strutturali EN con tagli a mitra, distinta di taglio |
| Valuta | Misura, proprietà di massa, verifica geometria, diagnostica feature, interferenze, analisi di sformo e di spessore, confronto tra versioni, sezioni |
| Assieme | Assiemi e giunti di FreeCAD, interferenze, viteria ISO, serie e specchiatura di componenti, distinta |
| Tavola | Tavola automatica (viste, cartiglio, distinta e palloncini) e tutti gli strumenti TechDraw |

Inoltre: barra **heads-up** in sovrimpressione nella vista 3D (adatta, zoom, orientamento, stile di
visualizzazione, sezione, nascondi/mostra, proiezione), **cursore di rollback** accanto alle schede per
il corpo attivo, **menu radiale** contestuale (tasto S).

## Novità rispetto a FreeCAD

**Interfaccia (M1)**
- Ambiente unico a schede contestuali; la modifica degli schizzi non cambia più workbench.
- Rollback bar del corpo attivo (cursore + comandi indietro/avanti/fine, annullabili).
- Barra heads-up nella vista, menu radiale contestuale.
- Impostazioni stile SolidWorks applicabili e annullabili con un clic.

**Schizzo (M2)**
- Diagnosi schizzo stile SketchXpert: vincoli in conflitto/ridondanti con correzioni verificate e applicabili.
- Blocchi di schizzo riutilizzabili (salva/inserisci con i vincoli interni).
- Schizzo 3D ridotto (polilinea/spline 3D con raccordi), utile come percorso.

**Robustezza (M3)**
- Raccordi, smussi e gusci che producevano in silenzio solidi non validi (anche a volume negativo) o
  che non facevano nulla ora vanno in errore con un messaggio chiaro; lo sformo non dà più errori vuoti.
- Diagnostica feature in italiano con suggerimenti calcolati (es. "Il raggio massimo applicabile è circa
  4,95 mm"), feature senza effetto, corpi divisi; avvisi automatici dopo ogni ricalcolo.

**Feature (M4)**
- Configurazioni con valori dei parametri e soppressione delle feature, tabella dati da foglio di calcolo.
- Nervatura da profilo aperto.
- Gestore unificato di equazioni e variabili globali.

**Lamiera e saldature (M5)**
- Addon SheetMetal integrato, tabella di piega coerente con lo sviluppo, DXF dello sviluppo.
- Profilati EN (IPE, HEA, HEB, tubi, angolari, piatti) lungo schizzi 2D/3D con mitra; distinta di taglio con massa.

**Assiemi (M6)**
- Viteria ISO 4762/4017/4032/7089 M3–M20 posizionata sul foro selezionato con il diametro giusto.
- Serie lineari/circolari e specchiatura di componenti.

**Tavole (M7)**
- Tavola automatica A3 ISO: viste in primo diedro + assonometria a scala unificata, cartiglio compilato,
  distinta raggruppata con palloncini per gli assiemi.

**Valutazione e produttività (M8)**
- Interferenze e giochi, analisi di sformo e di spessore, confronto tra versioni.
- Pack and Go, libreria personale di componenti.

## Scorciatoie (dopo "Impostazioni stile SolidWorks")

| Tasti | Azione |
|---|---|
| F | Adatta la vista |
| Ctrl+1 … Ctrl+6 | Vista frontale, posteriore, sinistra, destra, superiore, inferiore |
| Ctrl+7 | Isometrica |
| Ctrl+8 | Normale a (faccia selezionata) |
| Ctrl+B | Ricostruisci |
| S | Menu radiale contestuale |
| Spazio | Nascondi/mostra la selezione (FreeCAD) |
| Rotella / tasto centrale | Zoom sul cursore / rotazione (stile di navigazione SolidWorks) |

## Parametri utili

Strumenti → Modifica parametri → `BaseApp/Preferences/Mod/Forge`:
`AutoSwitchTabs` (cambio scheda automatico), `ShowHeadsUp` (barra heads-up), `Clearance` (gioco minimo
per le interferenze, mm), `MinDraftAngle` (gradi), `MinThickness` (mm).

## Esempi

La cartella [forge_examples](forge_examples) contiene modelli di riferimento (flangia, staffa, albero,
scatola con guscio, molla, telaio saldato, staffa in lamiera) generati e verificati dai test.

## Test

```
pixi run build/relWithDebInfo/bin/FreeCADCmd.exe -t ForgeTests.TestForgeApp      # e gli altri ForgeTests.*
pixi run build/relWithDebInfo/bin/FreeCAD.exe -t ForgeTests.TestForgeGui         # test con interfaccia
pixi run build/relWithDebInfo/bin/FreeCADCmd.exe -t 0                            # tutta la suite (FreeCAD + Forge)
```

## Struttura

- `src/Mod/Forge`: tutto il codice Forge (Python): `forgelib/` (logica e comandi), `ForgeTests/` (test).
- `src/Mod/SheetMetal`: addon SheetMetal (LGPL 2.1) incluso senza modifiche, vedi [THIRD_PARTY.md](THIRD_PARTY.md).
- Modifiche al codice di FreeCAD: poche e documentate in [CORE_PATCHES.md](CORE_PATCHES.md).
- Decisioni di progetto: [DECISIONS.md](DECISIONS.md).

## Licenza

Come FreeCAD: LGPL 2.1 o successiva. Nessun asset di Dassault Systèmes: icone e nomi di Forge sono originali.
