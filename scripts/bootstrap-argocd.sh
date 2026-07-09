#!/usr/bin/env bash
set -euo pipefail

ACR_NAME="${ACR_NAME:-dahredacrr0710a}"
ACR_LOGIN_SERVER="${ACR_LOGIN_SERVER:-dahredacrr0710a.azurecr.io}"
ARGOCD_VERSION="${ARGOCD_VERSION:-v3.4.5}"
DEX_VERSION="${DEX_VERSION:-v2.45.0}"
REDIS_VERSION="${REDIS_VERSION:-8.2.3-alpine}"

kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply --server-side --force-conflicts \
  -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

az acr import -n "$ACR_NAME" \
  --source "quay.io/argoproj/argocd:${ARGOCD_VERSION}" \
  --image "argoproj/argocd:${ARGOCD_VERSION}" \
  >/dev/null 2>&1 || true

az acr import -n "$ACR_NAME" \
  --source "ghcr.io/dexidp/dex:${DEX_VERSION}" \
  --image "dexidp/dex:${DEX_VERSION}" \
  >/dev/null 2>&1 || true

az acr repository delete -n "$ACR_NAME" \
  --image "library/redis:${REDIS_VERSION}" \
  --yes \
  >/dev/null 2>&1 || true

az acr import -n "$ACR_NAME" \
  --source "docker.io/library/redis:${REDIS_VERSION}" \
  --image "library/redis:${REDIS_VERSION}" \
  >/dev/null

kubectl -n argocd set image deployment/argocd-applicationset-controller \
  "argocd-applicationset-controller=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}"
kubectl -n argocd set image deployment/argocd-dex-server \
  "copyutil=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}" \
  "dex=${ACR_LOGIN_SERVER}/dexidp/dex:${DEX_VERSION}"
kubectl -n argocd set image deployment/argocd-notifications-controller \
  "argocd-notifications-controller=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}"
kubectl -n argocd set image deployment/argocd-redis \
  "secret-init=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}" \
  "redis=${ACR_LOGIN_SERVER}/library/redis:${REDIS_VERSION}"
kubectl -n argocd set image deployment/argocd-repo-server \
  "copyutil=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}" \
  "argocd-repo-server=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}"
kubectl -n argocd set image deployment/argocd-server \
  "argocd-server=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}"
kubectl -n argocd set image statefulset/argocd-application-controller \
  "argocd-application-controller=${ACR_LOGIN_SERVER}/argoproj/argocd:${ARGOCD_VERSION}"

kubectl -n argocd rollout status deploy/argocd-applicationset-controller --timeout=180s
kubectl -n argocd rollout status deploy/argocd-dex-server --timeout=180s
kubectl -n argocd rollout status deploy/argocd-notifications-controller --timeout=180s
kubectl -n argocd rollout status deploy/argocd-redis --timeout=180s
kubectl -n argocd rollout status deploy/argocd-repo-server --timeout=180s
kubectl -n argocd rollout status deploy/argocd-server --timeout=180s
kubectl -n argocd rollout status statefulset/argocd-application-controller --timeout=180s

kubectl -n argocd get pods
