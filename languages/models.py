from django.db import models
import uuid


class Language(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    native_name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    flag_emoji = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    story_submission_min_level = models.CharField(max_length=2, default='B2')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'languages'
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'
        ordering = ['name']

    def __str__(self):
        return f'{self.flag_emoji} {self.name}'


class CEFRLevel(models.Model):

    LEVEL_CHOICES = [
        ('A1', 'A1 — Beginner'),
        ('A2', 'A2 — Elementary'),
        ('B1', 'B1 — Intermediate'),
        ('B2', 'B2 — Upper-Intermediate'),
        ('C1', 'C1 — Advanced'),
        ('C2', 'C2 — Mastery'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='cefr_levels',
    )
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
 
    min_vocabulary = models.PositiveIntegerField(default=0)
    max_vocabulary = models.PositiveIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'cefr_levels'
        verbose_name = 'Уровень CEFR'
        verbose_name_plural = 'Уровни CEFR'
        ordering = ['order']
        unique_together = ('language', 'level')

    def __str__(self):
        return f'{self.language.name} — {self.level}'