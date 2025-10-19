#!/usr/bin/env python3
import os
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

LINKS_FILE = "links.txt"
OUTPUT_DIR = "Тематические"
COOKIES_FILE = "cookies.txt"

def read_links(path):
    if not os.path.exists(path):
        print(f"⚠ Файл {path} не найден!")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def download(url, out_dir=OUTPUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, "%(id)s_%(title)s.%(ext)s"),
        "format": "best",
        "noplaylist": True,
        "quiet": False,
        "no_warnings": True,
        "retries": 3,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }

    # если есть cookies.txt — используем
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            title = info.get("title") or info.get("id")
            ext = info.get("ext", "mp4")
            print(f"✅ Скачано: {title}.{ext}")
        except DownloadError as e:
            print(f"❌ Ошибка: {url}\n{e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {url}\n{e}")

def main():
    links = read_links(LINKS_FILE)
    if not links:
        print("⚠ В файле нет ссылок.")
        return
    print(f"📄 Найдено ссылок: {len(links)}")
    for url in links:
        print(f"\n=== Скачиваю: {url} ===")
        download(url)

if __name__ == "__main__":
    main()
