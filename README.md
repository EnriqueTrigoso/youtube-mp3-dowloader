# YouTube a MP3 por lotes (Python)

Descarga en MP3 el audio de varios videos de YouTube leyendo un archivo `urls.txt` (una URL por línea), sin copiar y pegar las direcciones una a una. Usa [yt-dlp](https://github.com/yt-dlp/yt-dlp) y FFmpeg.

## Requisitos

- Python **3.10 o superior**.
- **FFmpeg**, con `ffmpeg` y `ffprobe` accesibles desde `PATH`.
- **Deno**, recomendado por yt-dlp para resolver los desafíos JavaScript de YouTube.
- Conexión a Internet.

### Instalación en Windows (PowerShell)

```powershell
winget install -e --id Gyan.FFmpeg
winget install DenoLand.Deno
py -m pip install -U -r requirements.txt
```

Abre una terminal nueva tras instalar los programas. Puedes comprobar los ejecutables con `ffmpeg -version`, `ffprobe -version` y `deno --version`.

### Instalación en Linux/macOS

Instala `ffmpeg` (incluido `ffprobe`) y Deno con el gestor de paquetes de tu sistema. Después instala las dependencias Python:

```bash
python3 -m pip install -U -r requirements.txt
```

Si usas un entorno virtual, créalo y actívalo antes de instalar.

## Uso

1. Si aún no existe `urls.txt`, copia `urls.ejemplo.txt` a `urls.txt`:

   ```powershell
   Copy-Item urls.ejemplo.txt urls.txt
   ```

2. Abre `urls.txt` y coloca **una URL completa por línea**:

   ```text
   https://www.youtube.com/watch?v=ID_VIDEO_1
   https://youtu.be/ID_VIDEO_2
   # Esta línea es un comentario y se ignora
   ```

3. Ejecuta el script:

   ```powershell
   py descargar_mp3.py
   ```

Los MP3 se guardan en `descargas/`, con el título y el identificador del video en el nombre. La carpeta se crea automáticamente. No se descargan playlists completas: cada enlace se trata como un video individual.

### Opciones

```powershell
# Convertir a MP3 de 320 kbps (no mejora la calidad original)
py descargar_mp3.py --calidad 320

# Elegir archivo de enlaces y destino
py descargar_mp3.py --archivo mis_videos.txt --salida "C:\Musica"

# Desactivar temporalmente el historial de descargas
py descargar_mp3.py --sin-historial

# Ver todas las opciones
py descargar_mp3.py --help
```

Los argumentos también tienen formas cortas: `-a`, `-o` y `-q`. En Linux/macOS reemplaza `py` por `python3`.

### Funcionamiento y errores

- Omite líneas vacías, comentarios (`#`), URLs de otros sitios y URLs idénticas repetidas.
- Usa el mejor audio disponible y lo convierte a MP3 (192 kbps por defecto; 128/192/256/320 configurables).
- Continúa con el siguiente video cuando falla una descarga y muestra un resumen final.
- Guarda un historial en `descargas/.descargados.txt` para **no volver a descargar** videos ya procesados. Si borras un MP3 y quieres recuperarlo, elimina su registro del historial o ejecuta con `--sin-historial`.
- Las URLs reales (`urls.txt`), los audios y el historial están excluidos de Git mediante `.gitignore`.
- `320 kbps` es el bitrate del archivo de salida, **no una garantía de calidad original**.

Si YouTube modifica sus protecciones, prueba actualizar: `py -m pip install -U "yt-dlp[default]"`. Deno debe estar instalado y actualizado. Algunos videos pueden requerir iniciar sesión, pueden no estar disponibles en tu país o pueden impedir la descarga.

## Publicación en GitHub

Este proyecto puede publicarse como repositorio **privado** con GitHub CLI desde PowerShell. Si aún no tienes GitHub CLI:

```powershell
winget install -e --id GitHub.cli
```

En una terminal nueva, dentro de la carpeta del proyecto, inicia sesión y crea el repositorio:

```powershell
gh auth login
git init -b main
git add .
git commit -m "feat: descargar audio MP3 desde urls.txt"
gh repo create youtube-mp3-lotes --private --source . --remote origin --push
```

Si Git solicita una identidad para el primer commit, configura `git config --global user.name` y `git config --global user.email` con tus propios datos. `urls.txt` y los MP3 no se subirán porque están en `.gitignore`.

## Pruebas sin descargas reales

```powershell
py -m unittest discover -s tests -v
```

Las pruebas comprueban la lectura del TXT y la validación de URLs sin conectarse a YouTube.

## Uso responsable

Descarga únicamente contenido propio o para el cual tengas autorización. Respeta los derechos de autor y las condiciones del servicio aplicables.
