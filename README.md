# Identity Checker

Applicazione Flask per un progetto universitario di computer vision: l'utente carica una singola foto selfie in cui tiene il documento in mano. Il sistema rileva i volti presenti nell'immagine, considera il volto piu grande come volto della persona e confronta gli altri volti rilevati come possibili volti sul documento.

## Come avviare

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_models.py
python -m app
```

Poi apri `http://127.0.0.1:5000`.

Setup Windows rapido:

```powershell
.\scripts\windows\setup.ps1
```

## API

Oltre alla pagina web, il progetto espone un endpoint JSON:

```powershell
curl -X POST http://127.0.0.1:5000/api/verify -F "identity_image=@dataset/sample.jpg" -F "threshold=0.36"
```

La risposta contiene match, score, metodo usato, numero di volti rilevati e candidati documento.

Health check:

```powershell
curl http://127.0.0.1:5000/health
```

## Metodo usato

Il progetto usa una pipeline primaria deep learning con modelli OpenCV Zoo:

- YuNet per face detection;
- SFace per face recognition tramite embedding neurali;
- similarita coseno e soglia decisionale.

Al primo avvio l'app prova a scaricare automaticamente i file ONNX nella cartella `models/`. Se i modelli non sono disponibili, usa un fallback classico con OpenCV Haar Cascade.

Puoi prepararli esplicitamente con:

```powershell
python scripts/download_models.py
```

La logica della singola immagine e:

- rilevare tutti i volti nella scena;
- ordinare i volti per area;
- usare il volto piu grande come selfie/live face;
- confrontarlo con tutti i volti piu piccoli, cioe i candidati documento;
- usare lo score migliore come risultato finale.

Dopo il crop del volto principale, le immagini vengono normalizzate e trasformate in feature classiche:

- pixel grayscale ridimensionati;
- istogramma LBP per la texture locale;
- istogramma dei gradienti per la struttura del volto.

La verifica usa similarita coseno tra i due vettori. La soglia predefinita e `0.36`, modificabile dall'interfaccia.

## Valutazione

Prepara un CSV con colonne `image,label`, dove `image` e il path della foto singola e `label` vale `match`/`same`/`1` per esempi positivi e `0`/`false` per esempi negativi.
I path relativi in `image` vengono risolti rispetto alla cartella del CSV.

Se hai una cartella dataset con sottocartelle `match/` e `no_match/`, puoi generare il CSV automaticamente:

```powershell
python scripts/build_dataset_csv.py dataset --output samples.csv
```

Controlla prima che il CSV punti a file esistenti:

```powershell
python scripts/validate_dataset.py samples.csv
```

```powershell
python evaluate.py samples.csv --threshold 0.36 --output evaluation_results.json --report docs/evaluation_report.md --plots-dir docs/figures
```

Lo script calcola accuracy, precision, recall, F1-score e confusion matrix. Per inserire automaticamente le metriche nel documento tecnico:

```powershell
python evaluate.py samples.csv --threshold 0.36 --output evaluation_results.json --report docs/evaluation_report.md --plots-dir docs/figures --update-technical-analysis
python scripts/export_technical_pdf.py
```

La valutazione genera anche `docs/figures/confusion_matrix.png` e `docs/figures/score_distribution.png`.
Quando rigeneri il PDF tecnico, le figure PNG presenti in `docs/figures/` vengono incluse automaticamente.

Per cercare una soglia migliore sul dataset:

```powershell
python scripts/tune_threshold.py samples.csv --output threshold_tuning.json
```

Workflow finale cross-platform:

```powershell
python scripts/finalize_submission.py --csv samples.csv --tune-threshold
```

Se hai il dataset organizzato in `dataset/match/` e `dataset/no_match/`:

```powershell
python scripts/finalize_submission.py --dataset-dir dataset --csv samples.csv --tune-threshold
```

## Test

```powershell
pytest
```

Per un controllo complessivo degli artefatti di consegna:

```powershell
python scripts/project_audit.py
```

Oppure su Windows:

```powershell
.\scripts\windows\check.ps1
```

La checklist finale per pubblicazione/consegna e in `docs/submission_checklist.md`.

Per creare uno zip pulito da consegnare:

```powershell
python scripts/package_submission.py
```

Documenti utili per la consegna:

- `docs/architecture.md`: schema architettura e data flow.
- `docs/api.md`: documentazione endpoint JSON.
- `docs/requirements_coverage.md`: mappa requisiti della traccia -> artefatti.
- `docs/privacy_and_ethics.md`: privacy, sicurezza, bias e limiti etici.
- `docs/model_card.md`: uso dei modelli pre-addestrati e limiti.
- `docs/references.md`: riferimenti tecnici.
- `docs/deployment.md`: avvio locale e Docker.
- `docs/oral_presentation_outline.md`: scaletta per l'orale.
- `openapi.json`: specifica OpenAPI minimale.
- `.github/workflows/tests.yml`: CI GitHub con pytest.

## Documentazione tecnica

Il documento richiesto dalla traccia si trova in `docs/technical_analysis.md`. Per esportarlo in PDF:

```powershell
python scripts/export_technical_pdf.py
```

Il PDF viene salvato in `docs/technical_analysis.pdf`.

## Copertura requisiti

- Applicazione completa di Computer Vision: Flask app single-image.
- Problema reale: verifica identita da selfie con documento in mano.
- Data acquisition: upload immagine via browser.
- Preprocessing: decoding OpenCV, normalizzazione, crop/allineamento volti.
- Feature representation: embedding deep SFace e fallback LBP/gradienti.
- Core logic: face detection, candidate selection, cosine similarity, threshold.
- Post-processing: scelta best candidate, decisione match/no-match, anteprima annotata.
- Performance evaluation: `evaluate.py` con accuracy, precision, recall, F1 e confusion matrix.
- Dataset validation: `scripts/validate_dataset.py`.
- Dataset CSV builder: `scripts/build_dataset_csv.py`.
- Threshold tuning: `scripts/tune_threshold.py`.
- Model setup: `scripts/download_models.py`.
- Report risultati: `docs/evaluation_report.md` generabile da `evaluate.py`.
- Plot risultati: `docs/figures/` generabile da `evaluate.py`.
- Documentazione tecnica: `docs/technical_analysis.md` e PDF esportabile.
- Requisiti ambiente: `requirements.txt`.
- Test automatici: `tests/`.
- Audit consegna: `scripts/project_audit.py`.
- Finalizzazione consegna: `scripts/finalize_submission.py`.
- Packaging consegna: `scripts/package_submission.py`.
- Script Windows: `scripts/windows/setup.ps1`, `scripts/windows/check.ps1`, `scripts/windows/evaluate_dataset.ps1`.
- Checklist submission/GitHub: `docs/submission_checklist.md`.
- CI GitHub: `.github/workflows/tests.yml`.
- Deployment: `Dockerfile`, `.dockerignore`, `docs/deployment.md`.
- Documentazione API: `docs/api.md` e `openapi.json`.
- Documentazione architettura: `docs/architecture.md`.
- Privacy/ethics: `docs/privacy_and_ethics.md`.
- Model card: `docs/model_card.md`.
- References: `docs/references.md`.
- Scaletta orale: `docs/oral_presentation_outline.md`.

## Nota importante

Questo e un prototipo didattico per computer vision, utile per spiegare pipeline, preprocessing, feature extraction e decisione con soglia. Non deve essere usato come sistema reale di identificazione o controllo documentale.
