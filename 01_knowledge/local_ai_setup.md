# Local AI Setup: Ollama + OpenWebUI

## Установка Ollama (Linux)

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Проверка:

```bash
ollama run mistral
```

Проверка API:

```bash
curl http://localhost:11434
```

---

## Обновление Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

После обновления:

```bash
systemctl status ollama
ollama list
```

Модели не удаляются.

---

## Управление Ollama

Сервис:

```bash
systemctl status ollama
systemctl restart ollama
systemctl enable ollama
```

---

## Установка OpenWebUI (через podman)

```bash
sudo podman run -d \
  -p 3000:8080 \
  --add-host=host.containers.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

---

## Подключение OpenWebUI к Ollama

URL:

```
http://localhost:11434
```

или по сети:

```
http://192.168.1.138:11434
```

---

## Проверка моделей

```bash
ollama list
curl http://localhost:11434/api/tags
```

---

## Обновление OpenWebUI

```bash
sudo systemctl stop container-open-webui
sudo podman pull ghcr.io/open-webui/open-webui:main
sudo systemctl start container-open-webui
```

---

## Автозапуск OpenWebUI (systemd)

Создание:

```bash
sudo podman generate systemd --name open-webui --files --new
sudo mv container-open-webui.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable container-open-webui
```

---

## Перезапуск OpenWebUI

```bash
sudo systemctl restart container-open-webui
```

---

## Доступ

Локально:

```
http://localhost:3000
```

По сети:

```
http://192.168.1.138:3000
```

---

## Полезные модели

```bash
ollama pull mistral
ollama pull llama3
ollama pull phi3
ollama pull deepseek-coder
```

---

## Примечания

* Все данные OpenWebUI хранятся в volume `open-webui`
* Ollama хранит модели отдельно
* Интернет не требуется после загрузки моделей
* Работает полностью локально
