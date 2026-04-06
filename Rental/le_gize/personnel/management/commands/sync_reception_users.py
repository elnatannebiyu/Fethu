from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from personnel.models import Reception


class Command(BaseCommand):
    help = 'Create Reception profiles for users with role="reception" that don\'t have one yet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Find all users with role='reception' that don't have a Reception profile
        reception_users = User.objects.filter(role='reception').exclude(reception_profile__isnull=False)
        
        if not reception_users.exists():
            self.stdout.write(self.style.SUCCESS('No reception users found without profiles.'))
            return
        
        created_count = 0
        
        for user in reception_users:
            if dry_run:
                self.stdout.write(f'Would create Reception profile for: {user.username} ({user.get_full_name()})')
            else:
                try:
                    reception = Reception.objects.create(user=user)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created Reception profile for: {user.username} '
                            f'({user.get_full_name()}) - ID: {reception.employee_id}'
                        )
                    )
                    created_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to create Reception profile for {user.username}: {str(e)}'
                        )
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would create {reception_users.count()} Reception profile(s).'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully created {created_count} Reception profile(s).'
                )
            )
