class ContextManager:
    """Управляет контекстами работы - как Process Scheduler в ОС"""
    
    def switch_context(self, new_context):
        # Сохранить текущий контекст
        self.save_current_context()
        
        # Загрузить новый контекст
        relevant_docs = self.load_context(new_context)
        active_projects = self.get_active_projects(new_context)
        recent_files = self.get_recent_files(new_context)
        
        return {
            'docs': relevant_docs,
            'projects': active_projects,
            'recent': recent_files
        }