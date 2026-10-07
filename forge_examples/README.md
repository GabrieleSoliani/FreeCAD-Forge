# forge_examples — modelli di riferimento

Modelli che riproducono esercizi tipici dei tutorial SolidWorks, costruiti da script
(`src/Mod/Forge/ForgeTests/examples.py`) e verificati da `ForgeTests.TestForgeExamples`
(validità, solido unico, volume uguale al valore calcolato a mano, nessuna diagnostica).

| File | Esercizio | Feature usate |
|---|---|---|
| `flangia.FCStd` | Flangia con mozzo e 6 fori in serie polare | Estrusione, tasca passante, serie polare |
| `staffa_a_L.FCStd` | Staffa a L con fori e raccordo interno | Estrusione da profilo, tasca, raccordo concavo |
| `albero_a_gradini.FCStd` | Albero a gradini con smussi | Rivoluzione, smusso su spigoli circolari |
| `scatola_con_guscio.FCStd` | Scatola raccordata svuotata | Estrusione, raccordo, guscio |
| `molla.FCStd` | Molla elicoidale | Elica additiva |

Per rigenerarli: `pixi run build/relWithDebInfo/bin/FreeCADCmd.exe forge_examples/genera_esempi.py`
