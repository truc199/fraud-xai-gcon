# Developer & Agent Guidelines for GContest Pipeline

This guide outlines rules and practices for modifying and running the fraud detection pipeline.

---

## 1. Package Management & Execution
*   This project uses `uv` for package management and execution.
*   **Do NOT use `pip install <package>`**. Use:
    ```bash
    uv add <package>
    ```
*   **Do NOT use `python <file.py>`**. Use:
    ```bash
    uv run <file.py>
    ```

---

## 2. Component Extensions Policy (No Code Deletion)
The architecture is designed around strictly typed interfaces in `src/pipeline/protocols.py`. 
To test or implement a new pipeline mechanism (e.g., a new feature engineering method, models, explainers, or loaders):

1.  **NEVER delete or overwrite existing component code** in the codebase.
2.  **Create a new file** in the appropriate directory (e.g. `src/pipeline/second_order_markov_loader.py`).
3.  **Implement a new class** that strictly declares the Python Protocol it implements in its class signature (e.g., `class SequenceRarityRule(RoutingRule):` is good; `class SequenceRarityRule:` is bad).
4.  **Plug it into the demo runner**: Import your new component in `run_pipeline.py` and instantiate it there to swap behaviors dynamically.
5.  **Align descriptions with rule logic**: For rules implementing `RoutingRule`, the `to_natural_language()` method must always align precisely with the active parameters and evaluation logic.

---

## 3. Pipeline Output Files
Each execution of `uv run run_pipeline.py` dynamically creates the following outputs inside the `data/` directory:

*   `data/anomaly_alerts_latest.csv`
    *   *Content*: Cleaned, anomaly-only transaction alerts (filtered by prediction flag).
    *   *Columns*: Reordered to display critical xAI outputs (`CUSTOMER_NUMBER`, `ANOMALY_SCORE`, `EXPLANATION`, `TOP_SHAP_CONTRIBUTORS`, `TOP_INTERACTIONS`, `COUNTERFACTUAL`) first, followed by raw transaction fields.
*   `data/anomaly_alerts_latest_metadata.json`
    *   *Content*: A companion metadata JSON mapping the **exact classes and components** used in that specific pipeline run.
    *   *Example*:
        ```json
        {
            "timestamp": "20260523_183618",
            "components": {
                "data_loader": "SecondOrderMarkovDataLoader",
                "preprocessor": "StandardPreprocessor",
                "model_agent": "CohortAnomalyModelAgent",
                "explainer": "SHAPExplainer",
                "plugins": ["ConsoleLoggerPlugin", "MetricsTrackerPlugin"]
            },
            "metrics": {
                "anomalies_flagged": 96,
                "total_records_evaluated": 5000
            }
        }
        ```
*   `data/exports/anomaly_alerts_YYYYMMDD_HHMMSS.csv`
    *   *Content*: Timestamped CSV archive of the anomaly logs.
*   `data/exports/anomaly_alerts_YYYYMMDD_HHMMSS_metadata.json`
    *   *Content*: Timestamped companion JSON metadata configuration archive.

---

## 4. Web UI Dashboard
This project includes a FastAPI-powered glassmorphic dark-theme web dashboard to trigger pipeline runs and visualize explanation results.

*   **Execution Command**:
    ```bash
    uv run uvicorn app:app --host 0.0.0.0 --port 8000
    ```
*   **Web Endpoints**:
    *   `GET /`: Serves the dashboard page.
    *   `GET /api/exports`: Scans `data/` and returns parsed CSV records and companion JSON metadata.
    *   `GET /api/run/stream`: Spawns `run_pipeline.py` and streams execution logs using Server-Sent Events (SSE).

---

## 5. Exploratory Data Analysis (EDA) Guidelines
*   **Location:** All EDA scripts, code, and textual analysis results must be placed in the `./eda` folder.
*   **Execution & Outputs:** 
    *   Every EDA script must persist its extracted features, aggregations, or intermediate results.
    *   All persistent outputs (e.g. CSVs, JSONs, parquet files, or pickle caches) must be written to the `./eda/outputs` folder.
    *   Subsequent analysis should read from these persisted outputs to avoid re-running expensive database queries or aggregations.
*   **Relative Paths:** All file paths must be defined relatively (e.g., using `os.path.dirname(__file__)` or relative to the workspace root). Hardcoding absolute paths is strictly prohibited to ensure portability across devices.
*   **No Metaphors:** All documentation, explanations, and code comments must use direct, literal language. Avoid metaphors, analogies, or descriptive figures of speech.

