# Raphael Project Alignment

Raphael is being built as a hybrid assistant-agent system: simple to talk to like ChatGPT, but able to act like a controlled employee that can take delegated work, break it into tasks, execute safely, report progress, and improve over time only through approved training gates.

## Primary Goal

Build Raphael as a stable, scalable, adaptive multi-agent system with one authoritative control path for task decomposition, execution, evaluation, repair, learning, and progress reporting.

## Product Direction

Raphael should support this user flow:

1. The user gives an idea, request, or delegated task in plain language.
2. Raphael turns it into a mission.
3. Mission Control breaks the mission into controlled tasks.
4. Workers execute only assigned tasks.
5. Raphael reports status and progress in simple language.
6. Training suggestions can improve the system only after approval and testing.
7. Future tools such as web search, files, terminal, email, calendar, app building, and deployment must be added through permission gates and sandboxing.

## Required Design Principles

- Simple user experience first: the main interface should feel like a chat assistant, not a developer console.
- Mission Control stays authoritative: workers do not create plans, approve tools, apply training, or mark missions complete by themselves.
- Bounded autonomy: Raphael can act, but risky actions require explicit permission and audit trails.
- Event-driven state: important mission and task changes must be recorded.
- Privacy by default: secrets, tokens, and sensitive information must be redacted before storage.
- Secure tool access: terminal, files, browser, email, calendar, and deployment tools require allowlists, sandboxing, and approval levels.
- Continuous verification: tests, CI, and safety checks must run before major expansion.
- Mobile-first control: the iPhone app is a communication/import/export hub, while heavy agent work runs off-device.
- Future command center: a web dashboard should later show missions, agents, logs, approvals, updates, downloads, and profit/user tracking.

## What Raphael Is Not

- Not just a chatbot.
- Not an uncontrolled autonomous agent.
- Not a terminal that can freely run anything.
- Not a system where workers can self-modify.
- Not an app repo or social app codebase.

## Current Build Priority Order

1. Keep the repo separated from the app project.
2. Keep the chat-style interface simple.
3. Maintain mission/event/training safety.
4. Add tests and CI before expanding autonomy.
5. Add rate limits and input limits.
6. Add a tool permission registry.
7. Add sandbox rules for terminal and file access.
8. Add prompt-injection defenses before web/browser/file ingestion.
9. Add agent departments and manager agents after core safety is stable.
10. Build the future command center after core agents are reliable.
