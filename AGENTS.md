
# AGENTS.md — HardWareHouse

## 1. Project context

HardWareHouse (HWH) is a Django e-commerce application for computer hardware, product catalogs, inventory management, PC building, compatibility checks, recommendations, and online purchasing.

Main technologies:
- Python 3.13 and Django 4.2
- PostgreSQL
- Railway for application and database hosting
- Gunicorn as the application server
- Cloudflare R2 for static and media files
- GitHub for version control and deployments
- PayPal Sandbox with verified IPN processing
- Custom Django chatbot with Ollama Cloud for intent classification
- Django ORM and deterministic rules for catalog queries and hardware compatibility

AWS EC2, Amazon RDS, Amazon S3, Nginx, and Voiceflow are not part of the current deployed architecture.

## 2. General development rules

- Inspect the relevant existing code before modifying it.
- Reuse existing project conventions.
- Prefer small, maintainable changes.
- Avoid unnecessary refactoring.
- Do not modify unrelated functionality.
- Preserve existing APIs, routes, templates, and database relationships unless the task explicitly requires changes.
- Never invent product specifications, stock, prices, or payment results.
- Explain any assumptions that cannot be verified from the repository.

## 3. Production safety

- NEVER connect to or modify Railway production databases without explicit authorization.
- NEVER execute destructive operations against production.
- NEVER truncate, reset, or overwrite production tables.
- Preserve historical orders, payments, PayPal IPNs, boletas, inventory, and product IDs.
- Never reuse or reassign product IDs referenced by historical purchases.
- Do not run seed_test_data, sincronizar_catalogo_demo, loaddata, or full database restores in production.
- Inspect proposed Django migrations before applying them.
- Never run production migrations automatically without authorization.
- Never expose credentials, API keys, database URLs, or private customer data.

The production catalog includes demonstration data. Do not treat synthetic stock and prices as verified real-world inventory.

## 4. Git workflow

- Work on feature branches instead of modifying main directly.
- Never automatically commit, push, merge, or deploy without explicit approval.
- Prefer Pull Requests for code review.
- Do not add unrelated files to commits.
- Never commit .env, private credentials, local database dumps, temporary scripts, logs, or Python bytecode.
- Review git diff and changed filenames before proposing a commit.
- Remember that pushing to main can trigger an automatic Railway deployment.

## 5. Testing standards

- Run python manage.py check after Django code changes.
- Run focused tests for the modified modules.
- Add regression tests for confirmed bugs.
- Do not run the entire test suite for every small modification unless necessary.
- Never run tests using the Railway production database.
- Use isolated test databases.
- Mock external APIs such as Ollama Cloud and PayPal unless an integration test is explicitly requested.
- Validate user-controlled data on the Django backend, not only in JavaScript.
- Pay special attention to stock limits, cart totals, authentication, checkout, and payment security.

## 6. Database and migrations

- Inspect Django models before changing their structure.
- Prefer backward-compatible migrations.
- Explain new migrations and their production implications.
- Preserve compatibility specifications used by the PC builder.
- Do not rewrite existing applied migration history.
- If DATABASE_URL is configured, verify its destination before any database operation.
- Use PostgreSQL for database-sensitive integration tests.

## 7. Chatbot and AI

- Ollama Cloud is used primarily to interpret user intent.
- Django ORM is the authoritative source for product data, prices, and stock.
- Hardware compatibility must be checked by the existing Django compatibility rules.
- Preserve the rule-based fallback when Ollama is unavailable.
- Avoid unnecessary LLM requests.
- Preserve privacy checks and conversation isolation.
- Do not make real Ollama API calls in automated unit tests.

## 8. Frontend and usability

- Keep the interface responsive on desktop and mobile.
- Follow existing HardWareHouse branding and visual conventions.
- Preserve accessibility for forms, buttons, navigation, and offcanvas menus.
- Validate forms on both client and server.
- Do not introduce broken links or placeholder functionality presented as operational.

## 9. QA documentation

Every bug fix should report:
- Problem detected.
- Root cause.
- Files modified.
- Solution implemented.
- Tests executed.
- Results and remaining limitations.
- Whether a database migration is required.
- Whether deployment is safe.

Maintain traceability with the HardWareHouse QA documentation, but do not claim tests passed unless they were executed.

## 10. Reporting and communication

- Communicate progress and results in Spanish.
- Keep reports concise and technically precise.
- Prefer grouped improvements to reduce Railway deployments.
- Identify production risks before proposing deployment.
- Finish each development task with a clear summary and GO/NO-GO recommendation.
