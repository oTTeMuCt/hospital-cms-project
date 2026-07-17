from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserRole

User = get_user_model()


@receiver(post_save, sender=User)
def create_patient_profile_on_user_creation(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.role != UserRole.PATIENT:
        return

    from patients.models import Patient

    if hasattr(instance, "patient_profile") and instance.patient_profile:
        return

    parts = [instance.last_name, instance.first_name, instance.middle_name]
    full_name = " ".join(p for p in parts if p).strip()
    if not full_name:
        full_name = instance.username

    Patient.objects.get_or_create(
        user=instance,
        defaults={
            "full_name": full_name,
            "email": instance.email or "",
        },
    )
