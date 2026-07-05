#!/bin/sh
set -eu

BROKERS="${KAFKA_BOOTSTRAP_SERVERS:-redpanda:9092}"
TOPIC="${KAFKA_TOPIC:-sounds-right.events}"

rpk topic create "$TOPIC" --brokers "$BROKERS" --partitions 3 --replicas 1 || true
