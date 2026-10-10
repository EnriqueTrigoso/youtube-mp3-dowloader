"""Pruebas unitarias sin red para la entrada de URLs."""

import tempfile
import unittest
from pathlib import Path

from descargar_mp3 import es_url_youtube, leer_urls


class LecturaDeURLsTests(unittest.TestCase):
    def test_dominios_aceptados(self):
        for url in (
            "https://youtu.be/abc123",
            "https://www.youtube.com/watch?v=abc123",
            "https://music.youtube.com/watch?v=abc123",
            "https://m.youtube.com/shorts/abc123",
        ):
            with self.subTest(url=url):
                self.assertTrue(es_url_youtube(url))

    def test_dominios_rechazados(self):
        for url in (
            "https://youtube.com.falso.net/watch?v=1",
            "https://falso-youtube.com/watch?v=1",
            "ftp://youtube.com/video",
            "https://example.com/video",
            "hola",
            "https://youtube.com:abc/watch?v=1",
        ):
            with self.subTest(url=url):
                self.assertFalse(es_url_youtube(url))

    def test_lee_lineas_sin_comentarios_ni_duplicados(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "urls.txt"
            ruta.write_text(
                "\ufeff# URLs\n\nhttps://youtu.be/uno\n"
                "  https://www.youtube.com/watch?v=dos  \n"
                "https://youtu.be/uno\nhttps://example.com/no\n",
                encoding="utf-8",
            )
            urls, avisos = leer_urls(ruta)
            self.assertEqual(
                urls, ["https://youtu.be/uno", "https://www.youtube.com/watch?v=dos"]
            )
            self.assertEqual(len(avisos), 2)
            self.assertIn("Línea 5", avisos[0])
            self.assertIn("Línea 6", avisos[1])

    def test_archivo_sin_urls(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "vacio.txt"
            ruta.write_text("# Sólo comentario\n\n", encoding="utf-8")
            urls, avisos = leer_urls(ruta)
            self.assertEqual(urls, [])
            self.assertEqual(avisos, [])


class LotesTests(unittest.TestCase):
    def test_procesa_varias_urls_aunque_una_falle(self):
        """Verifica el flujo principal con un yt-dlp falso, sin red ni FFmpeg."""
        import contextlib
        import io
        import sys
        import types
        from unittest.mock import patch

        from descargar_mp3 import ejecutar

        class ErrorDescarga(Exception):
            pass

        class YoutubeDLFalso:
            opciones = None
            descargadas = []

            def __init__(self, opciones):
                type(self).opciones = opciones

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def download(self, urls):
                type(self).descargadas.extend(urls)
                if "fallido" in urls[0]:
                    raise ErrorDescarga("video no disponible")
                return 0

        falso = types.ModuleType("yt_dlp")
        falso.YoutubeDL = YoutubeDLFalso
        utilidades = types.ModuleType("yt_dlp.utils")
        utilidades.DownloadError = ErrorDescarga

        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            archivo = raiz / "videos.txt"
            archivo.write_text(
                "https://youtu.be/bien\nhttps://youtu.be/fallido\nhttps://youtu.be/bien2\n",
                encoding="utf-8",
            )
            salida = raiz / "mp3"
            with (
                patch.dict(sys.modules, {"yt_dlp": falso, "yt_dlp.utils": utilidades}),
                patch("descargar_mp3.shutil.which", return_value="/bin/mock"),
                contextlib.redirect_stdout(io.StringIO()) as out,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                codigo = ejecutar(["-a", str(archivo), "-o", str(salida), "-q", "320"])

            self.assertEqual(codigo, 1)
            self.assertEqual(len(YoutubeDLFalso.descargadas), 3)
            self.assertEqual(YoutubeDLFalso.opciones["postprocessors"][0]["preferredquality"], "320")
            self.assertTrue(salida.is_dir())
            self.assertIn("Procesadas sin error: 2 | Fallidas: 1", out.getvalue())


if __name__ == "__main__":
    unittest.main()
