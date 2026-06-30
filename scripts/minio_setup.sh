#!/bin/sh

until /usr/bin/mc alias set myminio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}; do
  echo 'Waiting for MinIO...'
  sleep 2
done

/usr/bin/mc mb --ignore-existing myminio/marketplace-media || true
/usr/bin/mc anonymous set public myminio/marketplace-media

until /usr/bin/mc admin config set myminio notify_webhook:1 endpoint="http://fastapi:8000/api/v1/webhooks/minio" queue_limit="10"; do
  echo 'Waiting for webhook config...'
  sleep 2
done

/usr/bin/mc admin service restart myminio || true
echo 'Waiting for MinIO to restart...'
sleep 10

until /usr/bin/mc event add myminio/marketplace-media arn:minio:sqs::1:webhook --event put; do
  echo 'Waiting for event add...'
  sleep 2
done

echo 'Minio setup complete.'
