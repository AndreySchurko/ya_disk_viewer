from django.db import models


class CachedFile(models.Model):
    """
    Модель для кэширования данных о файлах на Яндекс.Диске.
    """
    cached_at = models.DateTimeField(auto_now=True, verbose_name='Created (Cached)')
    public_key = models.CharField(max_length=250, verbose_name='Public key')
    name = models.CharField(max_length=250, verbose_name='Name')
    file_url = models.URLField(verbose_name='File URL')
    mime_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='MIME Type')
    is_directory = models.BooleanField(default=False)  # Для хранения информации о папке

    def __str__(self):
        return self.name
