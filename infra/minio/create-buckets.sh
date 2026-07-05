#!/bin/sh
set -eu

# Access MinIO using correct protocol scheme (http vs https)
scheme="http"
if [ "${MINIO_SECURE:-}" = "true" ]; then
	scheme="https"
fi

mc alias set local "${scheme}://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

mc mb --ignore-existing "local/${MINIO_TEMP_AUDIO_BUCKET}"
mc mb --ignore-existing "local/${MINIO_TRANSCRIPTS_BUCKET}"
mc mb --ignore-existing "local/${MINIO_ARTIFACTS_BUCKET}"
mc mb --ignore-existing "local/${MINIO_PUBLIC_BUCKET}"

# Determine CORS selection mode. Use MINIO_CORS_MODE if set (local|production),
# otherwise fall back to auto-detection using MINIO_API_CORS_ALLOW_ORIGIN.
if [ -n "${MINIO_CORS_MODE:-}" ]; then
	mode="${MINIO_CORS_MODE}"
else
	if echo "${MINIO_API_CORS_ALLOW_ORIGIN:-}" | grep -q "localhost"; then
		mode="local"
	else
		mode="production"
	fi
fi

case "${mode}" in
	local)
		CORS_FILE="/workspace/infra/minio/cors-local.json"
		;;
	production)
		CORS_FILE="/workspace/infra/minio/cors-temp-audio.json"
		;;
	*)
		echo "Unknown MINIO_CORS_MODE='${mode}', defaulting to production"
		CORS_FILE="/workspace/infra/minio/cors-temp-audio.json"
		;;
esac

echo "Applying MinIO CORS mode: ${mode} (file: ${CORS_FILE})"

# Apply CORS and make buckets private
mc cors set "local/${MINIO_TEMP_AUDIO_BUCKET}" "${CORS_FILE}" || echo "failed to set cors for ${MINIO_TEMP_AUDIO_BUCKET}"
mc cors set "local/${MINIO_TRANSCRIPTS_BUCKET}" "${CORS_FILE}" || echo "failed to set cors for ${MINIO_TRANSCRIPTS_BUCKET}"
mc cors set "local/${MINIO_ARTIFACTS_BUCKET}" "${CORS_FILE}" || echo "failed to set cors for ${MINIO_ARTIFACTS_BUCKET}"
mc cors set "local/${MINIO_PUBLIC_BUCKET}" "${CORS_FILE}" || echo "failed to set cors for ${MINIO_PUBLIC_BUCKET}"

mc anonymous set none "local/${MINIO_TEMP_AUDIO_BUCKET}"
mc anonymous set none "local/${MINIO_TRANSCRIPTS_BUCKET}"
mc anonymous set none "local/${MINIO_ARTIFACTS_BUCKET}"
mc anonymous set none "local/${MINIO_PUBLIC_BUCKET}"
