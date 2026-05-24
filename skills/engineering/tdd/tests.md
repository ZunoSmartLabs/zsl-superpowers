# Good and Bad Tests

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

Characteristics:

- Tests behavior users/callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts/order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying through external means instead of interface

```typescript
// BAD: Bypasses interface to verify
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: Verifies through interface
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

## Greenfield vs legacy code in TDD

The sections above assume **greenfield code** — you're designing the interface as part of the work. You control how dependencies arrive and what the public surface looks like; test-first lets you choose a shape that's naturally testable. *Greenfield isn't about age*: a brand-new function added to an old codebase is greenfield if you get to design its shape.

**Legacy code** is code already in place that isn't trustworthy under change. From the bundled *Working Effectively with Legacy Code* rules in [SKILL.md](SKILL.md): *"Treat code without trustworthy tests as legacy code: state what changes and what must remain."* The criterion is **test trust, not age** — yesterday's untested code is legacy; so is well-aged code whose tests pin implementation details rather than behaviour.

The practical question on any `/tdd` invocation: *do I get to choose the interface, or am I forced to work behind one that's already there?*

- **Choose** → greenfield path: write the failing test for the new behaviour; the interface emerges from the test.
- **Forced** → legacy path: characterize the existing behaviour first (next section). See [mocking.md](mocking.md) for internal-seam moves.

Most non-trivial `/tdd` work has both — a new module (greenfield) calling into existing untested code (legacy at the boundary).

## Characterization tests for legacy code

The flow above is greenfield: write the test for the new behavior, watch it fail, make it pass. **Legacy code needs the opposite first move** — pin the *existing* behavior with a test before changing anything, even if the behavior is ugly. Otherwise you're changing code without a safety net, and "fix" silently becomes "regression."

This is *characterization* — the test documents what the system **does**, not what it should do.

```typescript
// Bug report: discount sometimes wrong for $100+ orders.

// Step 1: characterize. Pin what the code currently does, ugly behavior
// included. Don't normalize, don't "improve" — capture what really happens.
test("characterize: discount applies twice for orders >= $100", () => {
  const order = { total: 150, customer: { tier: "gold" } };
  expect(applyDiscount(order)).toEqual({ ...order, total: 121.5 });
});

// Step 2: now write the bug-fix test, watch it fail (RED).
test("discount applies once, not twice, for orders >= $100", () => {
  const order = { total: 150, customer: { tier: "gold" } };
  expect(applyDiscount(order)).toEqual({ ...order, total: 135 });
});

// Step 3: fix the code. Bug-fix test goes GREEN; the characterization
// test goes RED — delete it (it documented a bug, and the bug is gone).
```

The bundled *Working Effectively with Legacy Code* rules in [SKILL.md](SKILL.md) cover the broader legacy loop: find change point → find observation point → create or exploit a seam → break the blocker → test → change → refactor locally. See [mocking.md](mocking.md) for when seam moves apply.
