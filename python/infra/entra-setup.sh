#!/usr/bin/env bash
#
# Entra app registrations for the Python server's AUTH_MODE=entra.
#
#   bash python/infra/entra-setup.sh [api-app-name] [consumer-app-name]
#
# Idempotently creates an API app (the resource the server validates tokens for)
# and a consumer app (one per consumer, e.g. NGX-Ramblers, MailMan) that fetches
# tokens by the OAuth2 client-credentials flow. Run after `az login`. Prints the
# ENTRA_TENANT_ID / ENTRA_AUDIENCE to set on the Container App. No secrets are
# stored by this script; create the consumer secret with `az ad app credential
# reset` when you need one.

set -euo pipefail

API_NAME="${1:-ramblers-sf-api}"
CONSUMER_NAME="${2:-ramblers-sf-consumer-ngx}"
ROLE_VALUE="members.read"

app_id_for() {
  az ad app list --filter "displayName eq '$1'" --query "[0].appId" -o tsv
}

TENANT=$(az account show --query tenantId -o tsv)

echo "==> API app: $API_NAME"
API_APP_ID=$(app_id_for "$API_NAME")
if [ -z "$API_APP_ID" ]; then
  API_APP_ID=$(az ad app create --display-name "$API_NAME" --sign-in-audience AzureADMyOrg --query appId -o tsv)
fi
az ad app update --id "$API_APP_ID" --identifier-uris "api://$API_APP_ID"
OBJ_ID=$(az ad app show --id "$API_APP_ID" --query id -o tsv)

if [ -z "$(az ad app show --id "$API_APP_ID" --query "appRoles[?value=='$ROLE_VALUE'] | [0].value" -o tsv)" ]; then
  ROLE_ID=$(uuidgen)
  az rest --method PATCH \
    --url "https://graph.microsoft.com/v1.0/applications/$OBJ_ID" \
    --headers "Content-Type=application/json" \
    --body "{\"api\":{\"requestedAccessTokenVersion\":2},\"appRoles\":[{\"id\":\"$ROLE_ID\",\"allowedMemberTypes\":[\"Application\"],\"displayName\":\"$ROLE_VALUE\",\"value\":\"$ROLE_VALUE\",\"description\":\"Read members and write consent\",\"isEnabled\":true}]}"
fi
az ad sp show --id "$API_APP_ID" >/dev/null 2>&1 || az ad sp create --id "$API_APP_ID" -o none
API_SP_ID=$(az ad sp show --id "$API_APP_ID" --query id -o tsv)
ROLE_ID=$(az ad app show --id "$API_APP_ID" --query "appRoles[?value=='$ROLE_VALUE'] | [0].id" -o tsv)

echo "==> Consumer app: $CONSUMER_NAME"
CONSUMER_APP_ID=$(app_id_for "$CONSUMER_NAME")
if [ -z "$CONSUMER_APP_ID" ]; then
  CONSUMER_APP_ID=$(az ad app create --display-name "$CONSUMER_NAME" --sign-in-audience AzureADMyOrg --query appId -o tsv)
fi
az ad sp show --id "$CONSUMER_APP_ID" >/dev/null 2>&1 || az ad sp create --id "$CONSUMER_APP_ID" -o none
CONSUMER_SP_ID=$(az ad sp show --id "$CONSUMER_APP_ID" --query id -o tsv)

echo "==> Granting $ROLE_VALUE to the consumer"
EXISTING=$(az rest --method GET \
  --url "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignedTo" \
  --query "value[?principalId=='$CONSUMER_SP_ID'] | [0].id" -o tsv 2>/dev/null || true)
if [ -z "$EXISTING" ]; then
  az rest --method POST \
    --url "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignedTo" \
    --headers "Content-Type=application/json" \
    --body "{\"principalId\":\"$CONSUMER_SP_ID\",\"resourceId\":\"$API_SP_ID\",\"appRoleId\":\"$ROLE_ID\"}" -o none
fi

echo
echo "Set on the Container App (az containerapp update --set-env-vars):"
echo "  AUTH_MODE=entra"
echo "  ENTRA_TENANT_ID=$TENANT"
echo "  ENTRA_AUDIENCE=$API_APP_ID"
echo
echo "A consumer fetches a token with:"
echo "  client_id=$CONSUMER_APP_ID  scope=api://$API_APP_ID/.default  grant_type=client_credentials"
echo "Create or rotate its secret with: az ad app credential reset --id $CONSUMER_APP_ID"
