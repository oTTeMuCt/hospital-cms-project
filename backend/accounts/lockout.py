"""
Account lockout mechanism to prevent brute-force attacks.

Tracks failed login attempts and temporarily locks accounts
after exceeding the maximum allowed failures.
"""
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from .models import UserRole

User = get_user_model()
logger = logging.getLogger("accounts.lockout")

# Configurable lockout settings
MAX_FAILED_ATTEMPTS = 5  # Max failed attempts before lockout
LOCKOUT_DURATION_MINUTES = 15  # Duration of lockout in minutes
LOCKOUT_CACHE_PREFIX = "account_lockout_"
FAILED_ATTEMPTS_PREFIX = "failed_login_"


def get_failed_attempts_key(user_id: int) -> str:
    """Generate cache key for tracking failed attempts."""
    return f"{FAILED_ATTEMPTS_PREFIX}{user_id}"


def get_lockout_key(user_id: int) -> str:
    """Generate cache key for lockout status."""
    return f"{LOCKOUT_CACHE_PREFIX}{user_id}"


def increment_failed_attempts(user_id: int) -> int:
    """
    Increment failed login attempts counter.
    Returns the current count of failed attempts.
    """
    key = get_failed_attempts_key(user_id)
    try:
        attempts = cache.get(key, 0)
        attempts = int(attempts) + 1
        # Keep the counter for 1 hour
        cache.set(key, attempts, timeout=3600)
        return attempts
    except (ValueError, TypeError) as exc:
        logger.error("Failed to increment attempts for user %s: %s", user_id, exc)
        return 0


def reset_failed_attempts(user_id: int) -> None:
    """Reset failed attempts counter after successful login."""
    try:
        cache.delete(get_failed_attempts_key(user_id))
        cache.delete(get_lockout_key(user_id))
    except Exception as exc:
        logger.error("Failed to reset lockout for user %s: %s", user_id, exc)


def is_account_locked(user_id: int) -> bool:
    """
    Check if account is currently locked out.
    Returns True if account is locked, False otherwise.
    """
    try:
        lockout_key = get_lockout_key(user_id)
        lockout_until = cache.get(lockout_key)
        if lockout_until is None:
            return False
        if isinstance(lockout_until, str):
            from django.utils.timezone import make_aware
            from datetime import datetime
            try:
                lockout_until = make_aware(datetime.fromisoformat(lockout_until))
            except (ValueError, TypeError):
                return True
        if timezone.now() >= lockout_until:
            cache.delete(lockout_key)
            reset_failed_attempts(user_id)
            return False
        return True
    except Exception as exc:
        logger.error("Failed to check lockout for user %s: %s", user_id, exc)
        return False


def apply_lockout(user_id: int) -> None:
    """
    Apply account lockout for the configured duration.
    """
    try:
        lockout_until = timezone.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        cache.set(
            get_lockout_key(user_id),
            lockout_until.isoformat(),
            timeout=int(timedelta(minutes=LOCKOUT_DURATION_MINUTES).total_seconds()),
        )
        user = User.objects.filter(pk=user_id).first()
        logger.warning(
            "Account locked: user_id=%s, username=%s, role=%s, until=%s",
            user_id,
            getattr(user, "username", "unknown"),
            getattr(user, "role", UserRole.PATIENT),
            lockout_until.isoformat(),
        )
    except Exception as exc:
        logger.error("Failed to apply lockout for user %s: %s", user_id, exc)


def get_remaining_lockout_time(user_id: int) -> int:
    """
    Get remaining lockout time in seconds.
    Returns 0 if account is not locked.
    """
    try:
        lockout_key = get_lockout_key(user_id)
        lockout_until = cache.get(lockout_key)
        if lockout_until is None:
            return 0
        if isinstance(lockout_until, str):
            from django.utils.timezone import make_aware
            from datetime import datetime
            try:
                lockout_until = make_aware(datetime.fromisoformat(lockout_until))
            except (ValueError, TypeError):
                return 0
        remaining = (lockout_until - timezone.now()).total_seconds()
        return max(0, int(remaining))
    except Exception as exc:
        logger.error("Failed to get remaining lockout time for user %s: %s", user_id, exc)
        return 0


def admin_unlock_account(user_id: int) -> bool:
    """
    Admin override to unlock an account.
    Returns True if successfully unlocked, False otherwise.
    """
    try:
        reset_failed_attempts(user_id)
        logger.info("Admin unlocked account: user_id=%s", user_id)
        return True
    except Exception as exc:
        logger.error("Failed to admin unlock account %s: %s", user_id, exc)
        return False