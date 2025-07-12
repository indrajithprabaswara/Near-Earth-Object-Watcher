# Near-Earth Object Watcher

This project watches the NASA NEO feed and stores close approaches in PostgreSQL. A
daily job fetches new objects and alerts Slack when any approach is closer than
0.05 AU. A small dashboard shows a live chart via Server Sent Events.

## Development

```bash
docker-compose up --build --detach
```

## Tests

```bash
pip install -r requirements.txt
pytest
```
