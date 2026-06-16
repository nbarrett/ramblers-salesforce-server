#!/usr/bin/env bash
#
# One-shot Azure setup for the Python server. Run AFTER `az login` and `gh auth login`.
#
#   bash python/infra/azure-setup.sh [name] [location]
#
# Provisions the Function App + storage (which doubles as the overlay store),
# creates a service principal for GitHub Actions, and sets the repo secrets/vars
# so the next push deploys. Re-runnable.

set -euo pipefail

NAME="${1:-ramblers-sf-py}"
LOCATION="${2:-uksouth}"
RG="${NAME}-rg"
REPO="nbarrett/ramblers-salesforce-server"
ROOT="$(git rev-parse --show-toplevel)"

echo "==> Resource group: $RG ($LOCATION)"
az group create -n "$RG" -l "$LOCATION" -o none

echo "==> Provisioning Function App + storage (Bicep)"
FUNC_APP=$(az deployment group create \
  -g "$RG" \
  -f "$ROOT/python/infra/main.bicep" \
  -p name="$NAME" location="$LOCATION" \
  --query properties.outputs.functionAppName.value -o tsv)
echo "    Function App: $FUNC_APP"

SUB=$(az account show --query id -o tsv)

echo "==> Creating service principal for GitHub Actions"
CREDS=$(az ad sp create-for-rbac \
  --name "${NAME}-github" \
  --role contributor \
  --scopes "/subscriptions/$SUB/resourceGroups/$RG" \
  --json-auth)

echo "==> Setting GitHub secrets and variables on $REPO"
printf '%s' "$CREDS" | gh secret set AZURE_CREDENTIALS --repo "$REPO"
gh variable set AZURE_FUNCTIONAPP_NAME --repo "$REPO" --body "$FUNC_APP"
gh variable set AZURE_DEPLOY_ENABLED --repo "$REPO" --body "true"
gh variable set DEFAULT_DEPLOY_TARGET --repo "$REPO" --body "python"

echo
echo "Done. The next push to main deploys the Python server to Azure,"
echo "or run the Deploy workflow manually with target=python."
echo "Remember to set ENTRA_TENANT_ID / ENTRA_AUDIENCE on the Function App"
echo "before switching real consumers to AUTH_MODE=entra."
