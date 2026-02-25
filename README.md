# Project Management MVP

## Run (Docker)

```bash
docker compose up --build
```

App URL: `http://localhost:8000`

## Stop

```bash
docker compose down
```

## Script shortcuts

- Windows PowerShell: `scripts/start.ps1`, `scripts/stop.ps1`
- Windows Batch: `scripts/start.bat`, `scripts/stop.bat`
- macOS/Linux: `scripts/start.sh`, `scripts/stop.sh`

## Test

### Manual smoke test

1. Start the app:

	```bash
	docker compose up --build -d
	```

2. Open `http://localhost:8000`.

3. Verify sign-in and auth flow:
	- You should see **Sign in** first.
	- Log in with:
	  - Username: `user`
	  - Password: `password`
	- You should then see the **Kanban Studio** board.

4. Verify Kanban interactions:
	- Rename a column.
	- Add a card.
	- Move a card between columns.
	- Remove a card.
	- Edit a card (click **Edit**, update title/details, click **Save**).

5. Verify logout:
	- Click **Log out**.
	- You should return to **Sign in**.

### Automated tests

From `frontend/`:

```bash
npm run test:unit
npm run test:e2e
```

From project root:

```bash
docker compose exec pm-app sh -lc "PYTHONPATH=/app/backend uv run --with pytest --with httpx pytest"
```

### Optional API auth check (PowerShell)

```powershell
$s = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-WebRequest http://localhost:8000/api/auth/login -Method Post -WebSession $s -ContentType 'application/json' -Body '{"username":"user","password":"password"}'
(Invoke-WebRequest http://localhost:8000/api/auth/me -WebSession $s).Content
Invoke-WebRequest http://localhost:8000/api/auth/logout -Method Post -WebSession $s
```

### Troubleshooting

- If startup fails, check container logs:

  ```bash
  docker compose logs pm-app --tail 200
  ```
