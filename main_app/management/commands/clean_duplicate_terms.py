# from django.core.management.base import BaseCommand
# from main_app.models import Term

# class Command(BaseCommand):
#     help = "Removes duplicate terms in the database"

#     def handle(self, *args, **kwargs):
#         count = 0
#         for term in Term.objects.all():
#             duplicates = Term.objects.filter(session=term.session, name=term.name)
#             if duplicates.count() > 1:
#                 count += duplicates.count() - 1
#                 duplicates[1:].delete()  # Keep one, delete others
        
#         self.stdout.write(self.style.SUCCESS(f"✅ Removed {count} duplicate terms!"))
