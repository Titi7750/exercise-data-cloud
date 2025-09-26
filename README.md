# README pour le LAB 9 - Mini-projet ELT — Prefect + GCS + BigQuery

## Objectif
Mettre en place un pipeline **ELT** orchestré par **Prefect** (exécuté en local) qui :
1. **Extract** : télécharge un CSV COVID (OWID)  
2. **Load (raw)** : dépose le fichier dans **Google Cloud Storage (GCS)**  
3. **Transform** : nettoie avec **pandas**  
4. **Load (clean)** : charge le résultat dans **BigQuery**

**Orchestration :** Prefect **Server** local (UI sur `http://127.0.0.1:4200`).  
**Stockage / Warehouse :** GCS + BigQuery (projet GCP).

---

## Prérequis

### Côté GCP
- **Project ID** (ex. `mon-projet-12345`) – pas le nom lisible ni le numéro.
- **Bucket GCS** existant : `gs://<YOUR_BUCKET>`
- **Dataset BigQuery** : `my_dataset`
- **Service account** + clé JSON (ex. `key.json`) avec rôles :
  - *Storage Object Admin* (sur le bucket)
  - *BigQuery Data Editor* (sur le dataset)
  - *BigQuery Job User* (sur le projet)

### Côté local
- Python 3.10+ (idéalement 3.11)
- `pip`
- Prefect 2.x

---

## Structure de dépôt (suggestion)

```
.
├─ flow.py
├─ requirements.txt
├─ .env.example
└─ jobvars.json            # (optionnel) variables d’env à embarquer dans la deployment
```

**requirements.txt** :
```
prefect==2.*
pandas
requests
google-cloud-storage
google-cloud-bigquery
python-dotenv
```

**.env.example** :
```
GOOGLE_APPLICATION_CREDENTIALS=C:\chemin\vers\key.json
GCP_PROJECT=mon-projet-12345
GCS_BUCKET=ton-bucket
BQ_DATASET=my_dataset
BQ_TABLE=covid_clean
```

> Le `flow.py` doit définir un flow nommé `covid_elt_prefect` et lire les variables via `os.getenv(...)`.

---

## Installation

**Windows PowerShell** :
```powershell
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

*(macOS/Linux : `python3 -m venv .venv && source .venv/bin/activate`)*

---

## Démarrer Prefect Server (local)
Dans une **première fenêtre** :
```powershell
prefect server start
```

Dans une **seconde fenêtre**, pointer la CLI sur le serveur local :
```powershell
prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect config view | findstr PREFECT_API_URL
```

Créer un **work pool** *pull* de type **process** :
```powershell
prefect work-pool create process-pull --type process
prefect work-pool ls
```

---

## Démarrer un worker (avec les variables GCP)
Dans la **fenêtre où tu lances le worker**, exporter les variables d’environnement :
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\chemin\vers\key.json"
$env:GCP_PROJECT="mon-projet-12345"
$env:GCS_BUCKET="ton-bucket"
$env:BQ_DATASET="my_dataset"
$env:BQ_TABLE="covid_clean"

prefect worker start --pool process-pull
```
> Laisse cette fenêtre **ouverte**. Dans l’UI, le pool doit apparaître actif (pastille verte).

---

## Créer & déployer la *deployment* du flow
Dans une **troisième fenêtre**, au **dossier du projet** :
```powershell
# Build + apply, rattaché au pool, avec un cron quotidien à 7h (Europe/Paris)
prefect deployment build flow.py:covid_elt -n covid-daily --pool process-pull --cron "0 7 * * *" --timezone "Europe/Paris" --apply
```

**(Optionnel)** : embarquer les variables d’env dans la deployment.  
Créer `jobvars.json` :
```json
{
  "env": {
    "GOOGLE_APPLICATION_CREDENTIALS": "C:\chemin\vers\key.json",
    "GCP_PROJECT": "mon-projet-12345",
    "GCS_BUCKET": "ton-bucket",
    "BQ_DATASET": "my_dataset",
    "BQ_TABLE": "covid_clean"
  }
}
```
Puis :
```powershell
prefect deployment build flow.py:covid_elt -n covid-daily --pool process-pull --cron "0 7 * * *" --timezone "Europe/Paris" --apply
```

---

## Lancer un run de test
```powershell
prefect deployment ls   # note le nom exact du flow et de la deployment
prefect deployment run "covid_elt_prefect/covid-daily"
```

Dans la fenêtre du **worker**, tu dois voir :  
`extract → ingest → transform → load`  
Vérifie dans l’UI Prefect que le run est **vert**.

---

## Vérifications

### GCS
- `gs://<YOUR_BUCKET>/raw/covid.csv`
- `gs://<YOUR_BUCKET>/processed/covid_clean.csv`

### BigQuery
```sql
SELECT location, SUM(CAST(new_cases AS FLOAT64)) AS total_cases
FROM `mon-projet-12345.my_dataset.covid_clean`
GROUP BY location
ORDER BY total_cases DESC;
```

---

## Développement / mise à jour
- Après modification de `flow.py` → **rebuild** la deployment :
```powershell
prefect deployment build flow.py:covid_elt -n covid-daily --pool process-pull --apply
```
- Pour modifier l’horaire : adapter `--cron` et `--timezone`.

---

## 📎 Commandes utiles
```powershell
prefect work-pool ls
prefect deployment ls
prefect flow-run ls
prefect config view
```
