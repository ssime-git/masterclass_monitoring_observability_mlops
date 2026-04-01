# Masterclass Outline

## The Starting Point: A Business Need

A support team needs to classify incoming messages automatically. The goal is to route tickets faster by predicting whether each message is about `billing`, `technical`, or `account` issues.

That is the business problem. But turning this into a production system requires answering questions that go far beyond the model itself:

- How do we expose the model to users securely?
- How do we know the system is healthy once it runs?
- How do we investigate when something goes wrong?

This masterclass treats these questions as first-class requirements, not afterthoughts.

## Requirements Defined Before Any Code

Before building anything, we define both what the system must do and how it must behave. These requirements guide every decision across all branches.

**Functional requirements:**

- A user can authenticate and receive a session
- An authenticated user can classify a support message
- The application returns a label, a confidence score, and recent prediction history
- The system rejects unauthenticated requests

**Non-functional requirements:**

- The public entry point must apply rate limiting to protect the system
- Services must be isolated enough to scale, replace, or troubleshoot independently
- The system must expose metrics so we can monitor its health *(addressed in branch 02)*
- The system must produce structured logs and traces so we can investigate individual requests *(addressed in branch 03)*
- Application state must be inspectable locally

The key insight: monitoring and observability are non-functional requirements that must be planned from the architecture phase. The way you split services, the boundaries you define, the identifiers you propagate, all of these choices determine whether monitoring and debugging will be easy or painful later.

## Branch Progression

### `01-architecture-base` -- Build the Foundation

This branch implements the application architecture. Every structural choice is made with the full list of requirements in mind, including the ones about monitoring and observability that will be activated later.

What you explore:

- How services are split and what each one owns
- Where the security boundary lives
- How a request flows from the user to the model and back
- Why metrics endpoints are already present even though nothing collects them yet

Questions to answer:

- Which service is exposed publicly?
- Where is the session token created?
- Which parts are stateful and which are stateless?
- Which service actually performs inference?

### `02-monitoring-prometheus-grafana` -- Answer "What Is Happening?"

This branch activates the monitoring non-functional requirement. Prometheus starts collecting the metrics that the services already expose, and Grafana turns them into dashboards.

What you explore:

- How to read a dashboard organized around four signals: traffic, errors, latency, saturation
- How to distinguish healthy traffic from degraded behavior
- How to tell whether a failure comes from the application or the edge

Questions to answer:

- Is traffic reaching the application?
- Are failures concentrated on authentication, inference, or ingress?
- Is latency increasing on one service or across the whole path?

By the end of this branch, you can detect symptoms. But you cannot yet explain them.

### `03-observability-otel` -- Answer "Why Is It Happening?"

This branch activates the observability non-functional requirement. Services now produce structured logs and distributed traces. Combined with the existing metrics, you can follow a single request from symptom to root cause.

What you explore:

- How to correlate a request across services using shared identifiers
- How to move from a metric spike to the exact request that caused it
- How logs and traces complement metrics to tell the full story

Questions to answer:

- Which specific request became slow?
- Where was time spent inside the request path?
- Was the failure caused by the application or by the edge layer?

## Recommended Order of Exploration

1. Start on `main` and read this outline to understand the business context and the requirements.
2. Switch to `01-architecture-base`: run the stack, explore the architecture, understand why each service exists.
3. Switch to `02-monitoring-prometheus-grafana`: reproduce the monitoring manipulations, learn to read dashboards.
4. Switch to `03-observability-otel`: reproduce the investigation manipulations, practice following a request from symptom to cause.

At each branch, the README provides step-by-step manipulations. The `docs/` folder provides deeper context on the concepts and tools introduced in that branch.
