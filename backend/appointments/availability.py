from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Appointment, AppointmentStatus

DEFAULT_DURATION = timedelta(minutes=30)


def occupied_bookings(doctor, start, end):
    return Appointment.objects.filter(doctor=doctor, scheduled_at__lt=end).filter(
        Q(end_time__gt=start) | Q(scheduled_at__gt=start - DEFAULT_DURATION, end_time__isnull=True),
    ).exclude(status=AppointmentStatus.CANCELLED)


def work_interval(workday, day):
    tz = timezone.get_default_timezone()
    return [timezone.make_aware(datetime.combine(day, value), tz) for value in (workday.starts_at, workday.ends_at)]
