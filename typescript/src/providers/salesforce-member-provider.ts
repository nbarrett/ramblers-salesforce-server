import type {
  ApplyConsentOptions,
  ApplyConsentResult,
  ListMembersOptions,
  ListMembersResult,
  MemberProvider,
  SalesforceMember,
} from "@ramblers/sf-contract";
import type { SalesforceConnection } from "../salesforce/connection.js";

export class SalesforceMemberProvider implements MemberProvider {
  constructor(private readonly conn: SalesforceConnection | undefined) {}

  async listMembers(_options: ListMembersOptions): Promise<ListMembersResult> {
    void this.conn;
    throw new NotImplemented("SalesforceMemberProvider.listMembers", [
      "Phase 4 (Ramblers HQ): write the SOQL query to fetch Contacts (or Member__c)",
      "for the given groupCode, then map each record through salesforceToMember().",
      "When this body is filled in, throw a clear error if this.conn is undefined,",
      "since a missing connection means the server is misconfigured.",
    ]);
  }

  async applyConsent(_options: ApplyConsentOptions): Promise<ApplyConsentResult> {
    void this.conn;
    throw new NotImplemented("SalesforceMemberProvider.applyConsent", [
      "Phase 4 (Ramblers HQ): perform a composite Salesforce request that updates",
      "the member's consent fields and inserts a ConsentEvent__c record.",
    ]);
  }
}

export function salesforceToMember(_record: unknown): SalesforceMember {
  throw new NotImplemented("salesforceToMember", [
    "Phase 4 (Ramblers HQ): implement the field mapping from a typed Salesforce",
    "record (Contact / Member__c / person account - HQ to confirm) to the",
    "SalesforceMember wire shape from @ramblers/sf-contract. The 36 Insight Hub",
    "fields plus the three granular consent flags are documented in the contract.",
  ]);
}

export function memberToSalesforce(_member: SalesforceMember): unknown {
  throw new NotImplemented("memberToSalesforce", [
    "Phase 4 (Ramblers HQ): implement the reverse mapping for consent writeback.",
  ]);
}

export class NotImplemented extends Error {
  readonly notes: readonly string[];
  constructor(symbol: string, notes: readonly string[]) {
    super(`${symbol} is not implemented yet`);
    this.name = "NotImplemented";
    this.notes = notes;
  }
}
