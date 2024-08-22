from django.contrib import admin
from django.apps import apps


def register_all_models(admin_site):
    app = apps.get_app_config('IMS_Admin')  # Replace 'IMS_Admin' with the name of your app if different
    for model_name, model in app.models.items():
        try:
            admin_site.register(model)
        except admin.sites.AlreadyRegistered:
            pass

# Call the function to register all models
register_all_models(admin.site)
