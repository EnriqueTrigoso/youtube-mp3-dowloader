#!/usr/bin/env python3
"""Descarga en MP3 los videos de YouTube enumerados en un archivo de texto.

Requisitos: Python 3.10+, yt-dlp[default], FFmpeg/FFprobe y Deno.
Solo descarga contenido para el que tengas autorización.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
CALIDADES = ("128", "192", "256", "320")


def es_url_youtube(url: str) -> bool:
    """Acepta HTTPS/HTTP de YouTube, no imitaciones de sus dominios."""
    try:
        datos = urlparse(url)
        host = (datos.hostname or "").lower()
        puerto = datos.port  # Detecta puertos mal formados, p. ej. :abc.
    except ValueError:
        return False

    if datos.scheme not in ("http", "https") or datos.username or datos.password:
        return False
    if puerto is not None and puerto not in (80, 443):
        return False
    return host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")


def leer_urls(ruta: Path) -> tuple[list[str], list[str]]:
    """Lee una URL por línea, omitiendo vacíos, comentarios y duplicados.

    Devuelve las URLs válidas y las advertencias de líneas omitidas.
    """
    contenido = ruta.read_text(encoding="utf-8-sig")
    urls: list[str] = []
    advertencias: list[str] = []
    vistas: set[str] = set()

    for numero, linea in enumerate(contenido.splitlines(), start=1):
        url = linea.strip()
        if not url or url.startswith("#"):
            continue
        if not es_url_youtube(url):
            advertencias.append(f"Línea {numero}: URL de YouTube no válida, se omite.")
            continue
        if url in vistas:
            advertencias.append(f"Línea {numero}: URL duplicada, se omite.")
            continue
        vistas.add(url)
        urls.append(url)

    return urls, advertencias


def ejecutar(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Descarga videos de YouTube como archivos MP3, leyendo urls.txt."
    )
    parser.add_argument(
        "--archivo", "-a", type=Path, default=BASE / "urls.txt",
        help="Archivo TXT con una URL de YouTube por línea (por defecto: urls.txt).",
    )
    parser.add_argument(
        "--salida", "-o", type=Path, default=BASE / "descargas",
        help="Carpeta para los MP3 (por defecto: descargas/).",
    )
    parser.add_argument(
        "--calidad", "-q", choices=CALIDADES, default="192",
        help="Bitrate MP3 de salida en kbps (por defecto: 192).",
    )
    parser.add_argument(
        "--sin-historial", action="store_true",
        help="No usar el historial para omitir videos procesados anteriormente.",
    )
    args = parser.parse_args(argv)

    if not args.archivo.is_file():
        print(f"ERROR: No existe el archivo de URLs: {args.archivo}", file=sys.stderr)
        print("Copia urls.ejemplo.txt como urls.txt y agrega las URLs.", file=sys.stderr)
        return 2

    try:
        urls, advertencias = leer_urls(args.archivo)
    except (OSError, UnicodeError) as exc:
        print(f"ERROR al leer {args.archivo}: {exc}", file=sys.stderr)
        return 2

    for advertencia in advertencias:
        print(f"AVISO: {advertencia}")

    if not urls:
        print("ERROR: No se encontraron URLs válidas en el archivo.", file=sys.stderr)
        return 2

    faltantes = [exe for exe in ("ffmpeg", "ffprobe") if shutil.which(exe) is None]
    if faltantes:
        print(
            "ERROR: Faltan " + ", ".join(faltantes) + " en PATH. Instala FFmpeg y abre otra terminal.",
            file=sys.stderr,
        )
        return 2

    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
    except ImportError:
        print('ERROR: Instala yt-dlp con: py -m pip install -U "yt-dlp[default]"', file=sys.stderr)
        return 2

    try:
        args.salida.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR al crear la carpeta de salida: {exc}", file=sys.stderr)
        return 2

    opciones = {
        "format": "bestaudio/best",
        "outtmpl": str(args.salida / "%(title).150s [%(id)s].%(ext)s"),
        "windowsfilenames": True,
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 3,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": args.calidad,
        }],
    }
    if not args.sin_historial:
        opciones["download_archive"] = str(args.salida / ".descargados.txt")

    fallidos = 0
    procesados = 0
    print(f"URLs: {len(urls)} | Calidad MP3: {args.calidad} kbps | Destino: {args.salida.resolve()}")

    try:
        with YoutubeDL(opciones) as ydl:
            for indice, url in enumerate(urls, start=1):
                print(f"\n[{indice}/{len(urls)}] {url}", flush=True)
                try:
                    codigo = ydl.download([url])
                    if codigo == 0:
                        procesados += 1
                    else:
                        fallidos += 1
                        print(f"ERROR: la descarga terminó con código {codigo}.", file=sys.stderr)
                except DownloadError as exc:
                    fallidos += 1
                    print(f"ERROR en la URL {indice}: {exc}", file=sys.stderr)
                except Exception as exc:
                    fallidos += 1
                    print(f"ERROR inesperado en la URL {indice}: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nDescargas interrumpidas por el usuario.", file=sys.stderr)
        return 130

    print(f"\nFinalizado. Procesadas sin error: {procesados} | Fallidas: {fallidos}.")
    if not args.sin_historial:
        print("Las URLs ya registradas en el historial se omiten en futuras ejecuciones.")
    print("Nota: la calidad final depende del audio original de YouTube.")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(ejecutar())
