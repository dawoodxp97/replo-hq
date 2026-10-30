# ADR 0001 — OAuth session model: one account, N provider identities, one token pair

Date: 2026-10-29 · Status: Accepted · Decides: D10 (multi-provider login)

## Context

Password auth works and must keep working. GitHub and Google login are being
added (D10a: all providers supported on the UI, interchangeable via one session
module). The questions that had to be settled before any code was written:

1. Where does a provider identity live?
2. What happens when the provider's email matches an existing account?
3. What does a successful OAuth login *issue*?

## Decision

**Identity storage.** A dedicated `user_oauth_identities` table — one row per
`(provider, provider_user_id)`, FK to `users` with CASCADE. Not columns on
`users`: providers are open-ended, a user can hold several identities at once,
and provider ids are only unique *per provider*.

**Session.** OAuth issues the *same* `Token`/`TokenWithUser` pair as password
login, produced by the same `auth_service.issue_tokens` call. There is no
"OAuth session" concept server-side; the session module on the frontend has one
job regardless of how login happened.

**Account linking.** On first login with a provider, if the provider's
**verified** email matches an existing user, the identity links to that user.
Otherwise a new passwordless user is created (`hashed_password` stays NULL).

**CSRF.** `state` is a signed JWT (`type: oauth_state`, provider-bound, 10 min
expiry) rather than a random nonce with a server-side store: the signature
proves we started the flow, and no Redis round trip sits in the login path.

**Unverified emails are never linked.** GitHub can report an unverified address;
linking on it is an account-takeover primitive. If a provider reports no
verified email at all, login fails with a clear message rather than minting an
account keyed to a provider subject (everything else in the product — password
reset, notifications — is email-addressed).

## Consequences

- Adding a provider is one adapter class + two Settings values. No migration
  (`provider` is a validated VARCHAR, not a PG enum), no schema change.
- Passwordless accounts cannot password-login (`authenticate` burns the KDF and
  refuses) — NULL password is "no credential", not a bypass.
- Sessions-valid-from revocation applies to OAuth sessions identically, because
  they are the same tokens.
- Two doors to one account means "sign out everywhere" (the
  `sessions_valid_from` cutoff) is the only revocation mechanism for both — the
  known refresh-rotation gap in `auth.py` now covers OAuth sessions too.
