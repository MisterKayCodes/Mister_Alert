Level-Up Dev Rulebook by MisterKay (2025 Edition)
The consolidated, ultimate guide for moving from “writing code” to “architecting resilient systems.”

This rulebook is mandatory for all development, testing, and deployment phases.


# Part 1: The Core Architecture (Stability & State)

**Rule 1:** The System is always in a known state
The application must always know exactly what it is doing—whether idle, processing, waiting for confirmation, or resting.
Unknown or undefined states are bugs waiting to happen.

**Rule 2:** Store all critical state in durable storage
Never keep vital information only in temporary variables or RAM. Use a database, persistent files, or external caches so the state survives restarts, crashes, or updates.

**Rule 3:** Single responsibility per file
Each file must do one job. No “mega-files” handling logic, database, API handlers, and helpers all at once.
If you cannot summarize a file’s purpose in one sentence, it is too complex.

**Rule 4:** Logic must be explicit and readable
Avoid vague or magical code.

Good example:

if missed_days >= 2:
    return RESET_TO_TODAY
Bad example:

if x > 2:
    do_special_thing()


**Rule 5:** Idempotency (Same input, same result)
The system must behave predictably. If the same command is received twice, the result should be the same as if it happened once.

**Rule 6:** No “smart” guessing
The system must wait for explicit commands. It should never guess user intent.



# Part 2: Resilience & Professionalism (Maintenance & Growth)

**Rule 7:** Expect failure, design for recovery
Crashes, network timeouts, and database hiccups will happen. Design the system to handle partial completions and retries gracefully.

**Rule 8:** Boring code is good code
Write code that is easy to read and maintain, even if it is slightly longer. Avoid clever one-liners and deep nesting.

**Rule 9:** Write automated tests for core logic
Tests are your safety net. Cover state changes, business logic, and previous bug fixes with unit tests.

**Rule 10:** Observability (Logs + Metrics)
Implement detailed logs with timestamps and context. Use metrics and “heartbeats” to monitor system health and catch downtime proactively.

**Rule 11:** Separate business logic from integrations
Keep core rules (e.g., task management) separate from external APIs (Telegram, database).

**Rule 12:** Handle errors explicitly
Never crash silently or use empty catch blocks. Use try/except blocks to log clear error messages and keep the system in a known state.




# Part 3: The Senior Workflow (Deployment & Security)
**Rule 13:** Consistent style and pinned dependencies
Follow a consistent naming and formatting style. Pin library versions to avoid unexpected breakage.

**Rule 14:** Security and Data Minimization
Never log sensitive data. Validate and sanitize all user inputs. Only collect necessary data and delete what is no longer needed.

**Rule 15:** Clean Version Control
Use Git properly with small, atomic commits and clear messages. Use branches for new features and merge only after testing.

**Rule 16:** The “Boy Scout” Rule
Always leave code cleaner than you found it. Fix small violations to prevent technical debt.

**Rule 17:** Documentation is the “Why”
Maintain documentation that explains architectural decisions and setup instructions.

**Bonus Rule 18:** The Safe Deployment Protocol
When deploying updates or fixes:

Backup: Back up production data first.
Staging: Test updates locally or in a dev environment, including running all tests.
Graceful Stop: Stop the service safely on your server.
Atomic Update: Pull code and update dependencies.
Monitor: Restart and watch logs and metrics immediately for anomalies.
Rollback Plan: Be ready to revert to the previous version instantly if things fail.


# Summary

Junior devs focus on making it work. Senior devs focus on making it last. Following these rules turns code into a resilient, maintainable system.