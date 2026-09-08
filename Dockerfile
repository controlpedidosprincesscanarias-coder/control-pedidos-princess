# (2026-09-07, v12.32.42) Runtime Docker — sustituye al runtime nativo de Python
# de Render (ver render.yaml). Motivo: el PDF de pedido oficial, una vez
# firmado/sellado en papel y vuelto a escanear para adjuntarlo, pierde toda
# su capa de texto (comprobado con un PDF real firmado: 0 caracteres
# extraíbles) — para poder seguir leyendo el Nº de Pedido y el Total en ese
# caso, la app pasa a intentar OCR con Tesseract como último recurso (ver
# _ocr_texto_pdf_pedido_oficial() en app.py). Tesseract es un binario del
# sistema operativo, no un paquete de pip, y el runtime nativo de Python de
# Render NO permite apt-get ni ningún otro instalador del sistema — solo
# runtime: docker lo permite (confirmado en la documentación/comunidad de
# Render). Fuera de este cambio de runtime, la app sigue siendo exactamente
# la misma: mismo `requirements.txt`, mismo comando de arranque (ver
# `dockerCommand` en render.yaml, no CMD fijo aquí, para poder seguir
# ajustándolo sin reconstruir la imagen — ver GUIA_DESPLIEGUE.md).

FROM python:3.12-slim
# (imagen "3.12-slim", no fijada a un patch exacto como el 3.12.9 de
# `.python-version` — Debian slim + Tesseract vía apt-get más abajo, sin
# relación con el número de patch de Python; si se quiere fijar un patch
# exacto, comprobar primero que esa etiqueta existe en Docker Hub antes de
# desplegar, este entorno de desarrollo no tiene acceso a red para
# comprobarlo)

# Tesseract OCR + modelo de idioma español ("spa") — sin este segundo
# paquete, Tesseract solo trae el modelo de inglés por defecto y fallaría
# sistemáticamente con el idioma real de estos documentos (pedidos en
# español). --no-install-recommends mantiene la imagen ligera (no hace
# falta ningún otro idioma ni herramienta de Tesseract).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Capa de dependencias separada del código: un cambio en app.py no invalida
# la caché de `pip install` (que es la capa más lenta del build).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
# Puerto por el que escucha Gunicorn (ver dockerCommand en render.yaml,
# --bind 0.0.0.0:$PORT) — Render solo autodetecta el puerto si NO se fija la
# variable de entorno PORT; al fijarla explícitamente en render.yaml, este
# EXPOSE es solo documentación para quien lea el Dockerfile, coherente con
# ese valor.
EXPOSE 10000

# Sin CMD aquí a propósito: el comando de arranque real vive en
# `dockerCommand` (render.yaml), igual que antes vivía en `startCommand` con
# el runtime nativo — un único sitio para cambiarlo sin tocar este archivo
# ni reconstruir la imagen desde cero. Para levantarlo en local sin
# render.yaml, ver el comando completo en GUIA_DESPLIEGUE.md / README.md.
