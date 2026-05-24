# When to Mock

Mock at **system boundaries** only:

- External APIs (payment, email, etc.)
- Databases (sometimes - prefer test DB)
- Time/randomness
- File system (sometimes)

Don't mock:

- Your own classes/modules
- Internal collaborators
- Anything you control

## Designing for Mockability

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in rather than creating them internally:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create specific functions for each external operation instead of one generic function with conditional logic:

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint

## Legacy code: internal seams are sometimes necessary

The "don't mock your own code" rule above assumes **greenfield code** — you're designing the interface as part of the work and can avoid the need for internal seams from the start.

When changing **legacy code** — code already in place that isn't trustworthy under change (see [tests.md](tests.md) for the full definition; test-trust, not age) — Feathers' moves apply instead. Create the *narrowest useful seam* to break the test-blocking dependency, then refactor with confidence.

- **Sprout** — add new behavior as a separate, testable unit; the legacy code calls into it.
- **Wrap** — wrap the legacy code so the new logic sits in a testable wrapper.
- **Parameterize / Inject** — turn a hidden dependency into a parameter or constructor arg.
- **Extract & override** — pull dependency-using code into a method; subclass-override in tests.

These are seams created *to enable testing*, not abstractions for production flexibility. See the bundled *Working Effectively with Legacy Code* rules in [SKILL.md](SKILL.md). Two guardrails: pick the narrowest seam that breaks the blocker, and don't leave test-only seams permanent — once the code is under test, fold the seam into the production design or remove it.

When the existing behavior is unclear, [characterize it first](tests.md) — see *Characterization tests for legacy code* — before introducing any seam.
