# Coding Standards

These are non-negotiable for every change. Where the project has its own linter, formatter or
style guide, follow it. These rules add to the project's own conventions and never override them.

## 1. No duplication

- **Search before you write.** Before writing a helper, validation, mapping, query or constant,
  search the codebase (`grep` for the domain terms, function-name verbs and literal values).
  Reuse or extend what exists.
- **Extract on the second occurrence.** If the same logic (not merely similar-looking code)
  appears twice, including in code you just wrote, extract it into a well-named function, module or
  constant, and use that from both places.
- **Duplicated knowledge counts too.** A rule such as a max length, a status list, a URL or a
  regex lives in one place. Literals that encode business rules become named constants.
- **Don't abstract coincidences.** Two pieces of code that look alike but change for different
  reasons should stay separate. Don't build a generic framework for a single use.
- **Tests may repeat setup for readability**, but shared fixtures and builders beat copy-pasted
  20-line setups.

## 2. Small, focused functions

- **One function does one thing at one level of abstraction.** If you need "and" to describe it,
  split it.
- **Size:** aim for 20 lines or fewer. More than 40 lines needs a real reason. Any function you
  have to scroll to read is too long.
- **Nesting:** two levels at most inside a function. Use guard clauses and early returns instead
  of `if` pyramids, and extract loop bodies into named functions.
- **Parameters:** three at most. Beyond that, pass a named options object or a type. No boolean
  flag parameters that switch behavior. Write two functions instead.
- **Separate commands from queries.** A function either returns information or changes state,
  not both (unless the convention is obvious, like `pop`).
- **Keep classes and modules cohesive.** One reason to change. No god objects, no `utils` dumping
  grounds. Name a module after the concept it holds.

## 3. Descriptive names

- **Names reveal intent:** `activeSubscriptionsByCustomerId`, not `data`, `list2`, `map` or `res`.
- **No cryptic abbreviations:** `customer`, not `cust`; `count`, not `cnt`; `manager`, not `mgr`.
  Widely known acronyms (`id`, `url`, `http`, `db`) are fine.
- **No single-letter names**, except `i`/`j` in a short index loop or a lambda of one or two lines
  where the meaning is obvious from the call (`users.map(user => user.id)` is still preferred).
- **Avoid meaningless words:** `data`, `info`, `item`, `obj`, `temp`, `value`, `thing`, `stuff`,
  `handle`, `process`, `manager`, `helper`, unless qualified (`retryPolicy`, not `helper`).
- **Make the grammar fit:** functions are verbs (`calculateInvoiceTotal`), booleans are predicates
  (`isExpired`, `hasAccess`, `shouldRetry`), collections are plural, and event handlers say what
  happened (`onPaymentFailed`).
- **Put units in names** when a value has a unit: `timeoutMs`, `maxFileSizeBytes`, `priceCents`.
- **Use the domain language** from the product brief and architecture consistently. One concept
  gets one name, everywhere.
- **Follow the project's casing conventions** for files, types, functions and constants.

## 4. Correctness and robustness

- **Validate at the boundaries** (requests, external input, config) and trust internal calls.
- **Fail fast with meaningful errors.** Never swallow exceptions. Catch only what you can handle,
  and add context when re-raising. Error messages say what failed and with which identifiers.
- **No magic values.** Use named constants or configuration.
- **Avoid hidden state:** no mutable globals and no surprising side effects. Prefer pure functions
  for logic, and keep I/O at the edges.
- **Handle the edge cases** listed in the task, plus the obvious ones: empty, null or missing
  values, boundaries, duplicates, concurrency, and timeouts on external calls.
- **Be precise with types.** No `any` or `object` escape hatches without a comment saying why.

## 5. Performance hygiene

- No queries or remote calls inside loops (N+1). Batch or join instead.
- Every list that can grow is paginated or bounded.
- Don't load more data than you use. Select only the columns you need.
- Use the indexes and caching specified in the task. Don't add caches that the task doesn't
  ask for.

## 6. Tests

- Test **behavior through public interfaces**, not private implementation details.
- One behavior per test. The test name states the scenario and expectation
  (`returns_404_when_order_belongs_to_another_user`).
- Use the Arrange / Act / Assert structure. Tests must be deterministic: no real network, no
  sleeps, and controlled time and randomness.
- Cover every acceptance criterion and test case listed in the task, plus the error paths.

## 7. Comments and hygiene

- Comments explain **why** (a constraint, a trade-off, a link to an issue), never what the next
  line does. Clear names replace most comments.
- No commented-out code, no debug prints or logs, and no leftover TODOs. A real follow-up goes in
  the PR's notes.
- No unrelated changes: no drive-by refactors, reformatting of untouched code or dependency
  bumps. If something nearby needs fixing, note it as a follow-up.
- Don't add a new dependency unless the task specifies it.
- Public functions and modules get doc comments where the project's convention expects them.

## Self-review checklist (run against the full diff before opening a PR)

- [ ] I searched for existing code that does this, and reused it instead of duplicating it.
- [ ] No logic or business rule appears in two places in the diff, or in the diff and the codebase.
- [ ] No function exceeds about 40 lines or two nesting levels, and none has more than three
      parameters or a boolean mode flag.
- [ ] Every name is descriptive, unabbreviated and consistent with the domain terms. No `data`,
      `tmp`, `res`, `x`, `obj`, `mgr` or `cnt`.
- [ ] No magic numbers or strings, no swallowed errors, no debug leftovers, no commented-out code.
- [ ] Inputs are validated at the boundary, and edge cases from the task are handled.
- [ ] No N+1 queries or unbounded lists.
- [ ] Tests cover every acceptance criterion and error path, and they pass along with lint, type
      checks and formatting.
- [ ] The diff contains only in-scope changes, and every "Provides" contract matches the task
      file exactly.
