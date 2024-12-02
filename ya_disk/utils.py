import requests
from .models import CachedFile
from django.utils.timezone import now, timedelta
from django.db.models import QuerySet


def update_cache(public_key: str) -> QuerySet[CachedFile]:
    """
    Функция обновляет кэш списка файлов и папок с Яндекс.Диска, если кэш устарел (более 5 минут).
    """
    cached_files = CachedFile.objects.filter(public_key=public_key)
    if cached_files.exists():
        last_cached_at = cached_files.first().cached_at
        if now() - last_cached_at < timedelta(minutes=5):
            return cached_files

    # Обновление кэша из Яндекс.Диска
    url = "https://cloud-api.yandex.net/v1/disk/public/resources"
    params = {"public_key": public_key}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Выводим данные для отладки
    print("Response data:", data)

    items = data.get("_embedded", {}).get("items", [])
    CachedFile.objects.filter(public_key=public_key).delete()

    for item in items:
        # Логирование типа элемента
        print(f"Item type: {item.get('type')}, Name: {item.get('name')}")

        if item.get("type") == "dir":  # Папка
            CachedFile.objects.create(
                public_key=public_key,
                name=item["name"],
                file_url=item.get("href", ""),
                mime_type="application/x-directory",  # Можно указать специальный MIME для папок
            )
        elif item.get("type") == "file":  # Файл
            CachedFile.objects.create(
                public_key=public_key,
                name=item["name"],
                file_url=item.get("file", ""),
                mime_type=item.get("mime_type", "application/octet-stream"),  # Указываем MIME тип файла
            )

    return CachedFile.objects.filter(public_key=public_key)
