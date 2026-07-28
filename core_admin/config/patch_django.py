import django.template.context
from copy import copy

def patch_django_context():
    try:
        def patched_copy(self):
            duplicate = self.__class__.__new__(self.__class__)
            for key, val in self.__dict__.items():
                if key != 'dicts':
                    duplicate.__dict__[key] = copy(val)
            duplicate.dicts = self.dicts[:]
            return duplicate
            
        django.template.context.BaseContext.__copy__ = patched_copy
    except Exception:
        pass
