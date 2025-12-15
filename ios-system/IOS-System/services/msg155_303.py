# search/management/commands/import_documents.py

from django.core.management.base import BaseCommand
from search.models import Document
import json
import csv
from pathlib import Path

class Command(BaseCommand):
    help = 'Import documents from JSON or CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to JSON or CSV file'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='File format'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for bulk creation'
        )
    
    def handle(self, *args, **options):
        file_path = Path(options['file_path'])
        file_format = options['format']
        batch_size = options['batch_size']
        
        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return
        
        if file_format == 'json':
            self.import_from_json(file_path, batch_size)
        else:
            self.import_from_csv(file_path, batch_size)
    
    def import_from_json(self, file_path, batch_size):
        """Import from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            doc = Document(
                title=item['title'],
                content=item['content'],
                document_type=item.get('document_type', 'ARTICLE'),
                category=item.get('category', 'General'),
                legal_code=item.get('legal_code', ''),
                paragraph=item.get('paragraph', ''),
                tags=item.get('tags', []),
                is_active=True,
                is_public=True
            )
            documents.append(doc)
            
            if len(documents) >= batch_size:
                Document.objects.bulk_create(documents, ignore_conflicts=True)
                self.stdout.write(f'Imported {len(documents)} documents')
                documents = []
        
        # Import remaining
        if documents:
            Document.objects.bulk_create(documents, ignore_conflicts=True)
            self.stdout.write(f'Imported {len(documents)} documents')
        
        self.stdout.write(
            self.style.SUCCESS('Import completed!')
        )
    
    def import_from_csv(self, file_path, batch_size):
        """Import from CSV file"""
        documents = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                doc = Document(
                    title=row['title'],
                    content=row['content'],
                    document_type=row.get('type', 'ARTICLE'),
                    category=row.get('category', 'General'),
                    legal_code=row.get('legal_code', ''),
                    is_active=True
                )
                documents.append(doc)
                
                if len(documents) >= batch_size:
                    Document.objects.bulk_create(documents, ignore_conflicts=True)
                    self.stdout.write(f'Imported {len(documents)} documents')
                    documents = []
        
        if documents:
            Document.objects.bulk_create(documents, ignore_conflicts=True)
            self.stdout.write(f'Imported {len(documents)} documents')
        
        self.stdout.write(
            self.style.SUCCESS('Import completed!')
        )