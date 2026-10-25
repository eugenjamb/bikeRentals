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

## VPS hosting: same approach as the existing apps

The application is copied directly to `/home/deploy/apps/bike-rentals`, with `.venv`, `backend`, `frontend`, `model` and `outputs` inside. There are no container or release-management tools. The model is served with Uvicorn under systemd; Nginx forwards the public path to loopback port 8003.

The new app's unit and route configurations are prepared on the VPS as `bike-rentals.service` and `bike-rentals.conf` in that app directory. Installation requires sudo in your SSH terminal:

```bash
ssh contabo
sudo install -m 644 /home/deploy/apps/bike-rentals/bike-rentals.service /etc/systemd/system/bike-rentals.service
sudo install -m 644 /home/deploy/apps/bike-rentals/bike-rentals.conf /etc/nginx/snippets/bike-rentals.conf
```

Use `sudoedit /etc/nginx/sites-available/project1` and add this one include beside the existing showcase/project2 includes, inside the HTTPS server block. Keep all existing routes and certificate settings:

```nginx
include /etc/nginx/snippets/bike-rentals.conf;
```

Then validate/start the new app before reloading Nginx:

```bash
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now bike-rentals
curl -f http://127.0.0.1:8003/api/health
sudo systemctl reload nginx
```

Public URL after installation: `https://169.58.96.231/bike-rentals/`. This setup does not install or restart Project 1, Project 2 or the showcase services. Logs: `sudo journalctl -u bike-rentals -n 50 --no-pager`.
