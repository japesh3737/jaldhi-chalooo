from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from planner.models import SavedRoute
from planner.sample import sample_route
from planner.validation import clean_route


class Command(BaseCommand):
    help = 'Create or refresh the clearly labeled New Delhi sample for an existing user.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)

    def handle(self, *args, **options):
        try:
            user = get_user_model().objects.get(username=options['username'])
        except get_user_model().DoesNotExist:
            raise CommandError('Register that username first; this command does not create accounts or passwords.')
        sample = sample_route()
        SavedRoute.objects.update_or_create(owner=user, name=sample['name'], defaults={'data': clean_route(sample)})
        self.stdout.write(self.style.SUCCESS('Sample route saved. Open My routes to try it.'))
