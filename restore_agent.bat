@echo off
:: =============================================================================
::  restore_agent.bat — Lanzador del agente de restauración (Opción C)
::  © VAMA 2026 — Central Compras Princess Canarias
::
::  Se ejecuta cada minuto via Programador de Tareas de Windows.
::  Comprueba si hay una petición de restauración pendiente desde el panel
::  web; si la hay, la procesa y termina. Si no hay nada, termina enseguida.
:: =============================================================================

:: ── CONFIGURACIÓN ──────────────────────────────────────────────────────────

:: Misma cadena de conexión que usa backup_pedidos.bat
set DATABASE_URL=postgresql://postgres.zvkbnlwibsgryicueiuc:Princess2026!Canarias@aws-0-eu-west-1.pooler.supabase.com:6543/postgres

:: Misma ruta de red que usa backup_pedidos.bat — los backups de seguridad
:: previos a una restauración (pre_restore_*) se guardan aquí también,
:: junto a los backups diarios, para que sean visibles desde el panel web.
set BACKUP_DESTINO=G:\CARPETA COMPRADORES\COMPRADOR 1 - VICTOR MARTIN\04.PEDIDOS EXTERNOS CONTROL\Backups

set SCRIPT_DIR=%~dp0
set SCRIPT_PY=%SCRIPT_DIR%restore_agent.py

:: ── VERIFICACIONES PREVIAS ──────────────────────────────────────────────────

if not exist "%SCRIPT_PY%" (
    echo [ERROR] No se encuentra restore_agent.py en %SCRIPT_DIR%
    exit /b 1
)

:: ── EJECUCIÓN (un solo ciclo; el Programador de Tareas se encarga de repetir) ─

python "%SCRIPT_PY%" >> "%SCRIPT_DIR%restore_agent.log" 2>&1

exit /b %ERRORLEVEL%
