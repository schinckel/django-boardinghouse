"""
"""
__version__ = '0.1'
__release__ = '0.1a2'

def inject_app_defaults():
    """
    Automatically inject the default settings for this app.
    
    If settings has already been configured, then we need to add
    our defaults to that (if not overridden), and in all cases we
    also want to inject our settings into the global_settings object,
    so we can use diffsettings.
    
    Based on:
    http://passingcuriosity.com/2010/default-settings-for-django-applications/
    but with improvements for importing/assignation failures.
    """
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