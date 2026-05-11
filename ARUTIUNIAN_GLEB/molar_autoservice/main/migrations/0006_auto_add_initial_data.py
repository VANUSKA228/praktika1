from django.db import migrations

def add_initial_roles(apps, schema_editor):
    Role = apps.get_model('main', 'Role')
    roles = [
        ('client', 'Клиент'),
        ('master', 'Мастер'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    for name, title in roles:
        Role.objects.get_or_create(name=name, defaults={'title': title})

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0005_alter_scheduleshift_options'),
    ]
    operations = [
        migrations.RunPython(add_initial_roles),
    ]