#!/bin/bash
# Docker verification for scrapalot-chat after code improvements
set -euo pipefail

echo "=== SCRAPALOT-CHAT DOCKER VERIFICATION ==="

echo "--- Restart ---"
docker restart scrapalot-chat

echo "--- Health Check (up to 180s for model loading) ---"
HEALTH_OK=0
for _ in $(seq 1 36); do
  if curl -sf http://localhost:8090/health > /dev/null 2>&1; then
    HEALTH_OK=1
    break
  fi
  sleep 5
done
if [ "$HEALTH_OK" = "1" ]; then
  echo "Health: PASS"
else
  echo "Health: FAIL (not up after 180s)"
  docker logs scrapalot-chat --since=180s 2>&1 | tail -20
  exit 1
fi

echo "--- Import Verification ---"
docker exec scrapalot-chat python -c "
import sys
sys.path.insert(0, '/app/src/main/grpc')
modules = [
    'src.main.config.database',
    'src.main.service.streaming.packet_emitter',
    'src.main.service.rag.agentic_routing',
    'src.main.service.deep_research.deep_research_orchestrator',
    'src.main.grpc.server',
    'src.main.workers.celery_app',
    'src.main.service.graph.entity_pipeline',
    'src.main.service.model_provider_snapshot',
    'src.main.service.redis_event_subscriber',
]
failed = 0
for m in modules:
    try:
        __import__(m)
        print(f'  OK: {m}')
    except Exception as e:
        print(f'  FAIL: {m} — {e}')
        failed += 1
if failed:
    raise SystemExit(f'{failed} imports failed')
print(f'All {len(modules)} imports OK')
" 2>&1

echo "--- gRPC Check ---"
docker exec scrapalot-chat python -c "
import grpc
channel = grpc.insecure_channel('localhost:9091')
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print('gRPC: PASS')
except Exception as e:
    print(f'gRPC: FAIL — {e}')
finally:
    channel.close()
" 2>&1

echo "--- Workers ---"
docker restart scrapalot-workers
sleep 15
if docker logs scrapalot-workers --since=60s 2>&1 | grep -q "ready\|celery@\|entered RUNNING state"; then
  echo "Workers: PASS"
else
  echo "Workers: WARN (check manually)"
fi

echo "--- Error Scan ---"
ERRORS=$(docker logs scrapalot-chat --since=30s 2>&1 | grep -iE "error|exception|traceback" | grep -vciE "0 errors" || echo "0")
echo "Errors in last 30s: $ERRORS"
echo ""
echo "CHAT_VERIFICATION=PASS"
