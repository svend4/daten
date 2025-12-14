class IOSRoot:
    """Главный интерфейс системы - точка входа"""
    
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.global_index = GlobalIndex(f"{root_path}/global-index.db")
        self.ontology = MasterOntology(f"{root_path}/master-ontology.json")
        self.registry = SystemRegistry(f"{root_path}/system-registry.yaml")
        self.access_control = AccessControlHub(f"{root_path}/config/security.config")
        
    def search(self, query: str, context: dict = None) -> List[Document]:
        """Глобальный поиск по всей системе"""
        return self.global_index.search(query, context)
    
    def get_domain(self, domain_name: str) -> Domain:
        """Получить домен знаний"""
        return self.registry.get_domain(domain_name)
    
    def list_domains(self) -> List[str]:
        """Список всех доменов"""
        return self.registry.list_domains()
    
    def create_domain(self, name: str, config: dict) -> Domain:
        """Создать новый домен"""
        domain = Domain(name, config)
        self.registry.register_domain(domain)
        return domain