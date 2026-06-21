#!/usr/bin/env bash
#
# Key Vault for the Salesforce connected-app private key (Phase 4 / HQ).
#
#   bash python/infra/keyvault-setup.sh [name] [location]
#
# Assigns the Container App a system-managed identity, creates an RBAC Key Vault,
# and grants the identity read access to its secrets. The private key itself is
# HQ's to add later. Run after `az login`. Re-runnable.

set -euo pipefail

NAME="${1:-ramblers-sf-py}"
LOCATION="${2:-uksouth}"
RG="${NAME}-rg"
VAULT="${NAME}-kv"
APP="$NAME"

az provider show --namespace Microsoft.KeyVault --query registrationState -o tsv | grep -q Registered \
  || az provider register --namespace Microsoft.KeyVault --wait

PRINCIPAL=$(az containerapp identity assign -n "$APP" -g "$RG" --system-assigned --query principalId -o tsv)
az keyvault create -n "$VAULT" -g "$RG" -l "$LOCATION" --enable-rbac-authorization true -o none

SUB=$(az account show --query id -o tsv)
SCOPE="/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.KeyVault/vaults/$VAULT"
az role assignment create \
  --assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" --scope "$SCOPE" -o none

echo "Key Vault $VAULT ready, Container App identity granted secret read."
echo "HQ add the Salesforce JWT private key with:"
echo "  az keyvault secret set --vault-name $VAULT --name sf-jwt-private-key --file <path-to-pem>"
