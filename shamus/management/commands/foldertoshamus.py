from django.core.management.base import BaseCommand
from shamus.logic import folder_to_shamus


class Command(BaseCommand):
    help = ('Copying mp3 from folder to Shamus. Set path to directory'
            ' which contains mp3, not subdirectories.')

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)

    def handle(self, *args, **options):
        for path in options['path']:
            folder_to_shamus(path)

