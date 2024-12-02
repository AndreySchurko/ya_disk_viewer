from django.urls import path
from . import views

app_name = "ya_disk"


urlpatterns = [
    path("", views.index, name="index"),  # Начальная страница с формой
    path("files/", views.file_list, name="file_list"),  # Список файлов и папок
    path("download-file/", views.download_file, name="download_file"),  # Скачивание одного файла
    path("download/", views.download_files, name="download_files"),  # Скачивание нескольких файлов архивом
]
