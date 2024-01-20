from celery import shared_task
from . import models
from .chatgpt.main import get_cover_letter

@shared_task
def create_cover_letter(cover_letter_id:int):
    cover_letter = models.CoverLetter.objects.get(cover_letter_id)
    cover_letter.cover_letter = get_cover_letter(cover_letter.profile.about_me, cover_letter.job_description)
    cover_letter.save()
