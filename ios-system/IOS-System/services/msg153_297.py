# scripts/seed_data.py

"""
Seed database with sample data
"""

from django.core.management.base import BaseCommand
from search.models import Document
from datetime import date

class Command(BaseCommand):
    help = 'Seed database with sample documents'
    
    def handle(self, *args, **options):
        documents = [
            {
                'title': 'SGB IX § 29 - Persönliches Budget',
                'content': '''
                    Das Persönliche Budget ist eine alternative Leistungsform,
                    bei der Menschen mit Behinderungen anstelle von Sach- oder
                    Dienstleistungen ein Budget zur Verfügung gestellt wird...
                ''',
                'document_type': Document.DocumentType.LAW,
                'category': 'Sozialrecht',
                'legal_code': 'SGB IX',
                'paragraph': '§ 29',
                'effective_date': date(2020, 1, 1),
                'is_active': True,
                'is_public': True,
            },
            # Add more sample documents...
        ]
        
        for doc_data in documents:
            doc, created = Document.objects.get_or_create(
                title=doc_data['title'],
                defaults=doc_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {doc.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Seeding completed!')
        )