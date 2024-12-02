from django.test import TestCase
from django.urls import reverse
from .models import CachedFile
from unittest.mock import patch


class YandexDiskTests(TestCase):

    @patch('requests.get')
    def test_update_cache_if_needed(self, mock_get):
        """Тестирует обновление кэша, если данные устарели."""
        # Создаем данные для API ответа
        mock_response = {
            "_embedded": {
                "items": [
                    {"name": "file1.txt", "file": "http://example.com/file1.txt", "mime_type": "text/plain"},
                    {"name": "file2.jpg", "file": "http://example.com/file2.jpg", "mime_type": "image/jpeg"}
                ]
            }
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        public_key = "https://disk.yandex.ru/d/mykey"

        # Вызываем функцию, которая обновит кэш
        response = self.client.get(reverse('ya_disk:file_list') + f"?public_key={public_key}")

        # Проверяем, что файлы были добавлены в базу
        cached_files = CachedFile.objects.filter(public_key=public_key)
        self.assertEqual(cached_files.count(), 2)
        self.assertEqual(cached_files.first().name, "file1.txt")
        self.assertEqual(cached_files.last().name, "file2.jpg")

    @patch('requests.get')
    def test_file_list(self, mock_get):
        """Тестирует отображение файлов с Яндекс.Диска."""
        # Подготовка мок-данных
        mock_response = {
            "_embedded": {
                "items": [
                    {"name": "file1.txt", "file": "http://example.com/file1.txt", "mime_type": "text/plain",
                     "type": "file"},
                    {"name": "folder1", "file": "http://example.com/folder1", "mime_type": "application/x-directory",
                     "type": "dir"}
                ]
            }
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        public_key = "https://disk.yandex.ru/d/mykey"

        # Запрашиваем список файлов
        response = self.client.get(reverse('ya_disk:file_list') + f"?public_key={public_key}")

        # Проверка правильности ответа
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "file1.txt")
        self.assertContains(response, "folder1")
        self.assertContains(response, "type")
        self.assertNotContains(response, "application/x-directory")

    @patch('requests.get')
    def test_filter_files_by_category(self, mock_get):
        """Тестирует фильтрацию файлов по категориям."""
        mock_response = {
            "_embedded": {
                "items": [
                    {"name": "document1.pdf", "file": "http://example.com/document1.pdf",
                     "mime_type": "application/pdf", "type": "file"},
                    {"name": "image1.jpg", "file": "http://example.com/image1.jpg", "mime_type": "image/jpeg",
                     "type": "file"}
                ]
            }
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        public_key = "https://disk.yandex.ru/d/mykey"

        # Проверяем фильтрацию по категории "documents"
        response = self.client.get(reverse('ya_disk:file_list') + f"?public_key={public_key}&file_category=documents")
        self.assertContains(response, "document1.pdf")
        self.assertNotContains(response, "image1.jpg")

        # Проверяем фильтрацию по категории "images"
        response = self.client.get(reverse('ya_disk:file_list') + f"?public_key={public_key}&file_category=images")
        self.assertContains(response, "image1.jpg")
        self.assertNotContains(response, "document1.pdf")

    @patch('requests.get')
    def test_download_file(self, mock_get):
        """Тестирует скачивание одного файла."""
        mock_response = b"file content"
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200

        file_url = "http://example.com/file1.txt"

        response = self.client.get(reverse('ya_disk:download_file') + f"?file_url={file_url}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, mock_response)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="file1.txt"')

    @patch('requests.get')
    def test_download_multiple_files(self, mock_get):
        """Тестирует скачивание нескольких файлов в ZIP-архиве."""
        mock_response = b"file content"
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200

        file_urls = ["http://example.com/file1.txt", "http://example.com/file2.txt"]

        response = self.client.get(
            reverse('ya_disk:download_files') + f"?file_urls={file_urls[0]}&file_urls={file_urls[1]}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="files.zip"'))
        self.assertTrue(response.content.startswith(b'PK'))
