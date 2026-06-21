#!/usr/bin/env bash
#
# One-shot Azure Container Apps setup for the Python server.
# Run AFTER `az login` and `gh auth login`.
#
#   bash python/infra/azure-setup.sh [name] [location] [acr-name]
#
# Creates the resource group and container registry, builds and pushes the image,
# then deploys main.bicep: the managed environment, storage + overlay table, Key
# Vault, and the Container App (user-assigned identity reading the overlay secret
# from Key Vault). Creates a deploy service principal and sets the GitHub Actions
# vars/secrets so the next push to main redeploys. Re-runnable.
#
# For Entra auth, run entra-setup.sh afterwards and set AUTH_MODE=entra with the
# tenant id and audience it prints. Every setting is documented in CONFIGURATION.md.

set -euo pipefail

NAME="${1:-ramblers-sf-py}"
LOCATION="${2:-uksouth}"
ACR_NAME="${3:-$(echo "${NAME}acr" | tr -d '-' | tr '[:upper:]' '[:lower:]')}"
RG="${NAME}-rg"
REPO="nbarrett/ramblers-salesforce-server"
ROOT="$(git rev-parse --show-toplevel)"
IMAGE_TAG="$(git rev-parse --short HEAD)"

echo "==> Resource group: $RG ($LOCATION)"
az group create -n "$RG" -l "$LOCATION" -o none

echo "==> Container registry: $ACR_NAME (must be globally unique)"
az acr create -n "$ACR_NAME" -g "$RG" --sku Basic -o none 2>/dev/null || true
ACR_LOGIN_SERVER=$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)

echo "==> Build + push image (tag $IMAGE_TAG)"
az acr build -r "$ACR_NAME" -t "ramblers-sf-py:${IMAGE_TAG}" \
  -f "$ROOT/python/Dockerfile" "$ROOT/python" -o none
IMAGE="${ACR_LOGIN_SERVER}/ramblers-sf-py:${IMAGE_TAG}"

echo "==> Deploy main.bicep (Container App + storage + Key Vault)"
az deployment group create \
  -g "$RG" \
  -f "$ROOT/python/infra/main.bicep" \
  -p name="$NAME" location="$LOCATION" containerImage="$IMAGE" \
     acrLoginServer="$ACR_LOGIN_SERVER" acrName="$ACR_NAME" \
  -o none
FQDN=$(az containerapp show -n "$NAME" -g "$RG" \
  --query properties.configuration.ingress.fqdn -o tsv)

SUB=$(az account show --query id -o tsv)
echo "==> Service principal for GitHub Actions deploys"
CREDS=$(az ad sp create-for-rbac \
  --name "${NAME}-github" \
  --role contributor \
  --scopes "/subscriptions/$SUB/resourceGroups/$RG" \
  --json-auth)

echo "==> Setting GitHub secrets and variables on $REPO"
printf '%s' "$CREDS" | gh secret set AZURE_CREDENTIALS --repo "$REPO"
gh variable set AZURE_RESOURCE_GROUP --repo "$REPO" --body "$RG"
gh variable set AZURE_ACR_NAME --repo "$REPO" --body "$ACR_NAME"
gh variable set AZURE_CONTAINERAPP_NAME --repo "$REPO" --body "$NAME"
gh variable set AZURE_DEPLOY_ENABLED --repo "$REPO" --body "true"
gh variable set DEFAULT_DEPLOY_TARGET --repo "$REPO" --body "python"

echo
echo "Live at: https://${FQDN}"
echo "The next push to main redeploys via .github/workflows/deploy.yml."
echo "For Entra auth: run python/infra/entra-setup.sh, then set AUTH_MODE=entra"
echo "with the ENTRA_TENANT_ID and ENTRA_AUDIENCE it prints. See CONFIGURATION.md."
