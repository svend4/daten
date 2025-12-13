# 1. Создать production Dockerfile
# Скопировать из ФАЙЛА 19, секция "Production Dockerfile"

# 2. Создать docker-compose.prod.yml
# Скопировать из ФАЙЛА 19

# 3. Создать Nginx конфиг
mkdir -p nginx/conf.d
# Скопировать nginx.conf из ФАЙЛА 19

# 4. Получить SSL сертификаты
sudo certbot certonly --standalone -d ios-search.com