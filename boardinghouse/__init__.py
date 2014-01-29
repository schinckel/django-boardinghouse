"""
"""
__version__ = '0.1'
__release__ = '0.1a2'

def inject_app_defaults():
    try:
        import settings as app_settings
        from django.conf import settings, global_settings
        from django.core.exceptions import ImproperlyConfigured
    except ImportError:
        return

    for key in dir(app_settings):
        if key.isupper():
            value = getattr(app_settings, key)
            setattr(global_settings, key, value)
            if not hasattr(settings, key):
                # We can just ignore failures, as this means we are
                # not set up, so global_settings will suffice.
                try:
                    setattr(settings, key, value)
                except (ImproperlyConfigured, ImportError):
                    pass

inject_app_defaults()