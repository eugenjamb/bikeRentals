# Prediction API

The backend validates requests and calls the existing fitted pipeline. It does not train models, query external weather or recalculate experiment scores.

From the repository root, with the venv activated:

```bash
python -m pip install -r backend/requirements.txt
python backend/scripts/export_content.py
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8003
```

`export_content.py` packages small public assets from recorded experiment files and five date-selected historical scenarios. It requires the local source dataset and completed experiment artifacts; the running API does not require the full dataset. Re-export after deliberately replacing the fitted model. The server rejects mismatched model/showcase fingerprints.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Readiness and loaded-model fingerprint |
| `GET /api/study` | Recorded scores, charts and grid-search results |
| `GET /api/scenarios` | Historical replay choices |
| `GET /api/scenarios/{id}` | Past-only request and separate observed outcome |
| `POST /api/predict` | Run the saved pipeline |
| `GET /api/figures/{filename}` | Whitelisted public experiment PNGs |

API documentation: `http://127.0.0.1:8003/docs`. Prediction input has a target-hour timestamp, known holiday/working-day flags and exactly 168 ordered observations. Each observation has `timestamp` and `count` (nullable for missing hours). The last completed count is required. Future observations, duplicate/out-of-order timestamps, target components and invalid calendar flags are rejected.

The model is loaded once at startup. Predictions are serialized through a lock with one native computation thread. Counts remain unrounded in `predicted_rentals`; `display_rentals` is a presentation convenience. No uncertainty interval is claimed.

Code map:

- `app/main.py`: routes and startup lifecycle.
- `app/schemas.py`: input/output contract.
- `app/service.py`: one loaded model and prediction calls.
- `app/settings.py`: paths and deployment prefix.
- `app/assets/`: exported study and replay data.

Tests:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest -c backend/pytest.ini backend/tests
```

The production build in `frontend/dist` is served by the same FastAPI app when present. Nginx strips `/bike-rentals/` and forwards to loopback port 8003; `ROOT_PATH=/bike-rentals` keeps API docs aware of the external prefix.

## VPS hosting

The application is live at [https://169.58.96.231/bike-rentals/](https://169.58.96.231/bike-rentals/). Service and public health were verified on 25 October 2026.

| Setting | Value |
| --- | --- |
| App directory | `/home/deploy/apps/bike-rentals` |
| Runtime | Python venv + one Uvicorn worker |
| Process manager | `bike-rentals.service` under systemd |
| Internal address | `127.0.0.1:8003` |
| Public route | `/bike-rentals/`, forwarded by Nginx |
| Nginx snippet | `/etc/nginx/snippets/bike-rentals.conf` |
| API docs | `https://169.58.96.231/bike-rentals/docs` |

No containers or release-management folders are used. Existing Project 1, Project 2 and showcase services remain separate.

From your own terminal, connect using the real address rather than relying on a local SSH alias:

```bash
ssh deploy@169.58.96.231
```

Once logged into the VPS:

```bash
# Inspect the app and recent logs.
systemctl status bike-rentals --no-pager
sudo journalctl -u bike-rentals -n 50 --no-pager

# Restart after deliberately updating backend code or the model.
sudo systemctl restart bike-rentals

# Check the internal and public API.
curl -f http://127.0.0.1:8003/api/health
curl -f https://169.58.96.231/bike-rentals/api/health
```

The one-command startup helper prepared on this server is:

```bash
bash /home/deploy/apps/bike-rentals/start.sh
```

It requests sudo if needed, installs/starts this app's service, validates the Nginx configuration and checks public health. It refuses to overwrite an unexpectedly changed shared configuration. This helper is server-local; there is no `deploy/` folder in the repository.

For frontend changes, rebuild locally with `npm run build` in `frontend`, then copy the built files from your local repository root:

```bash
scp -r frontend/dist/. deploy@169.58.96.231:/home/deploy/apps/bike-rentals/frontend/dist/
```

Static frontend changes do not require model retraining. Keep the model binary, exported study assets and recorded final-evaluation fingerprint consistent when changing model artifacts. The exporter rejects mismatched final-model fingerprints; do not present old scores as results of a new model.

Sudo passwords and private SSH keys must never be committed or pasted into API requests.
