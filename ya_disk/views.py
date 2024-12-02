import io
import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import PublicKeyForm
from zipfile import ZipFile
from urllib.parse import unquote
from .utils import update_cache


# Списки MIME типов по категориям
# Список можно расширить MIME-типами...
MIME_CATEGORIES = {
    "documents": ["application/pdf", "application/msword", "application/xml", "text/plain"],
    "images": ["image/jpeg", "image/png", "image/gif", "image/svg+xml"],
    "videos": ["video/mp4", "video/webm", "video/avi", "video/mpeg"],
    "audio": ["audio/mp4", "audio/mpeg", "audio/aac", "audio/x-wav"],
}


def index(request):
    """
    Главная страница с формой для ввода публичной ссылки.
    """
    if request.method == "POST":
        form = PublicKeyForm(request.POST)
        if form.is_valid():
            public_url = form.cleaned_data["public_url"]
            return redirect(f"/files/?public_key={public_url}")
    else:
        form = PublicKeyForm()

    return render(request, "ya_disk/index.html", {"form": form})


def file_list(request):
    """
    Отображение списка файлов и папок с фильтрацией по категории.
    """
    public_key = request.GET.get("public_key")
    if not public_key:
        return render(request, "disk/error.html", {"message": "Public key is missing."})

    try:
        cached_files = update_cache(public_key)
    except requests.exceptions.RequestException as e:
        return render(request, "disk/error.html", {"message": f"API request failed: {e}"})

    # Формирование категорий для фильтрации
    available_categories = {
        "all": "Все файлы",
        "documents": "Документы",
        "images": "Изображения",
        "videos": "Видео",
        "audio": "Аудио",
    }

    # Применение фильтрации по категории только к файлам
    selected_category = request.GET.get("file_category", "all")
    if selected_category != "all":
        mime_types = MIME_CATEGORIES.get(selected_category, [])
        # Фильтруем только файлы по типу MIME
        files = cached_files.filter(mime_type__in=mime_types).exclude(mime_type="application/x-directory")
    else:
        # Если выбран фильтр "all", показываем все файлы
        files = cached_files.exclude(mime_type="application/x-directory")

    # Папки фильтруются отдельно и всегда отображаются
    folders = cached_files.filter(mime_type="application/x-directory")

    return render(
        request,
        "ya_disk/file_list.html",
        {
            "files": files,
            "folders": folders,
            "available_categories": available_categories,
            "selected_category": selected_category,
            "public_key": public_key,
        },
    )


def download_file(request):
    """
    Скачивание одного файла.
    """
    file_url = request.GET.get("file_url")
    if not file_url:
        return HttpResponse("URL-адрес файла не указан.", status=400)

    try:
        # Выполняем запрос для загрузки файла
        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        # Извлекаем имя файла из заголовков
        filename = None
        content_disposition = response.headers.get("Content-Disposition")
        if content_disposition:
            import re
            match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^;"]+)', content_disposition)
            if match:
                filename = unquote(match.group(1))

        if not filename:
            filename = file_url.split("/")[-1]

        # Возвращаем файл в HTTP-ответе
        response_to_user = HttpResponse(
            response.content,
            content_type=response.headers.get("Content-Type", "application/octet-stream"),
        )
        response_to_user["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response_to_user

    except requests.exceptions.RequestException as e:
        return HttpResponse(f"Не удалось загрузить файл. {e}", status=500)


def download_files(request):
    """
    Скачивание выбранных файлов в виде ZIP-архива.
    Args: request: запрос с параметрами выбранных файлов.
    Returns: HttpResponse: ответ с архивом.
    """
    file_urls = request.GET.getlist("file_urls")
    if not file_urls:
        return HttpResponse("Файлы для загрузки не выбраны.", status=400)

    # Создание временного буфера для хранения ZIP-архива
    zip_buffer = io.BytesIO()

    with ZipFile(zip_buffer, "w") as zip_file:
        for file_url in file_urls:
            try:
                # Выполнение запроса на скачивание файла по URL
                response = requests.get(file_url, stream=True)
                response.raise_for_status()  # Проверка успешности запроса

                # Получение имени файла из заголовков Content-Disposition или URL
                filename = None
                content_disposition = response.headers.get("Content-Disposition")
                if content_disposition:
                    import re
                    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^;"]+)', content_disposition)
                    if match:
                        filename = unquote(match.group(1))

                if not filename:
                    filename = file_url.split("/")[-1]

                # Добавление файла в архив
                zip_file.writestr(filename, response.content)

            except requests.exceptions.RequestException as e:
                continue  # Игнорируем ошибку

    zip_buffer.seek(0)
    response = HttpResponse(
        zip_buffer,
        content_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="selected_files.zip"'}
    )
    return response
