# Scripts Guide

This directory contains start/stop scripts for local Docker-based runtime across platforms.

## Windows

- PowerShell:
	- `start.ps1` -> `docker compose up --build -d`
	- `stop.ps1` -> `docker compose down`
- Batch:
	- `start.bat` -> `docker compose up --build -d`
	- `stop.bat` -> `docker compose down`

## macOS / Linux

- `start.sh` -> `docker compose up --build -d`
- `stop.sh` -> `docker compose down`

## Notes

- Run scripts from repository root (`c:\Projects\pm`).
- Docker Desktop (or compatible Docker engine + Compose plugin) must be installed.