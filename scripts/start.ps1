$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

for ($attempt = 1; $attempt -le 2; $attempt++) {
	try {
		docker compose up --build -d
		exit 0
	}
	catch {
		if ($attempt -eq 2) {
			throw
		}

		Start-Sleep -Seconds 5
	}
}
