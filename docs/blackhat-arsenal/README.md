# BlackHat Arsenal Demo Plan

## Positioning

TrustInspect is an **Evidence-Based Trustworthy AI Testing Workbench for LLM and Agentic Applications**.

It is not a traditional web application security scanner. The demo should focus on AI behavior, evidence capture, dynamic test generation, and repeatable findings.

## Demo message

> TrustInspect turns informal prompt experiments into reproducible Trustworthy AI assessments by profiling the target, generating contextual tests, executing static and dynamic catalogs, collecting evidence, and producing findings that engineering and assurance teams can review and re-test.

## Recommended demo targets

### 1. PromptAirlines

Role: Public AI challenge and external reference target.

Purpose:

- Demonstrate web UI scanning
- Demonstrate hidden instruction following
- Demonstrate evidence capture and adaptive test generation

### 2. TrustInspect Demo Chatbot

Role: Controlled self-hosted target.

Purpose:

- Vulnerable vs hardened comparison
- Before/after mitigation report
- Deterministic demo independent of third-party uptime

### 3. TrustInspect Demo RAG

Role: Controlled self-hosted RAG target.

Purpose:

- Retrieved-context manipulation
- Indirect prompt injection
- Document-as-data vs instruction confusion

### 4. Damn Vulnerable LLM Agent adapter

Role: Agentic workflow demo.

Purpose:

- Tool-use behavior
- Unsafe delegation
- Excessive agency
- Agent trace evidence

### 5. AgentDojo adapter

Role: Research-grade agentic benchmark.

Purpose:

- Benchmark-driven evaluation
- Indirect prompt injection scenarios
- Multi-step tool behavior evidence

## Targets to avoid in public narrative

Avoid positioning around PortSwigger/Burp or generic web security labs. TrustInspect should not be confused with web application DAST. Generic public customer-service bots may be useful for development, but are not ideal for public demos.

## Live demo flow

```text
1. Show CLI banner and target profile
2. Run adaptive scan with --max-dynamic-tests 4
3. Show prompt/response live in terminal
4. Open report
5. Explain Target Capability Profile
6. Explain Generated Test Plan
7. Show finding evidence
8. Re-run after mitigation in controlled demo target
```
