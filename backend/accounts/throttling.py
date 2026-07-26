"""
DRF throttling configuration for login protection and rate limiting.
"""
from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle for login endpoint to prevent brute-force attacks.
    Allows 5 attempts per minute for anonymous users.
    """
    scope = "login"


class LoginBurstThrottle(AnonRateThrottle):
    """
    Burst throttle for login - 10 attempts per hour.
    """
    scope = "login_burst"