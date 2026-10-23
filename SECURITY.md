# Security

## What this tool is

NexusAgent is a lightweight agent framework: it loads tools, calls an LLM adapter, and
executes tool results **locally on your machine**. It is a library/framework, not a hosted
service — there is no server, no telemetry, and no outbound connection unless you wire one
into a tool you write.

## The real threat model

The risk in any agent framework is **tool execution**: an agent that can call tools can, by
design, run code (shell commands, file writes, network requests) on the host. That power is
the point of the framework; the safety is *your* responsibility as the integrator:

- **Treat the LLM as untrusted input.** A prompt-injected model response can attempt to drive
  a tool toward destructive actions. Restrict which tools are registered, and keep dangerous
  tools (shell, filesystem delete) out of untrusted deployments.
- NexusAgent does **not** log secrets you pass in, but it echoes tool I/O into the
  conversation log. Do not feed it credentials you would not want in a local text file.
- Run untrusted agents inside an OS sandbox / container / dedicated low-privilege account.
  The framework has no built-in sandbox; "runs locally" means "runs with your privileges".

## Supported versions

| version | status |
|---|---|
| 0.2.x | current, supported |
| < 0.2 | unsupported; upgrade first |

Python 3.10+ on Linux / macOS / Windows.

## Reporting a vulnerability

Use GitHub's **private vulnerability reporting** on the repository (Security → Report a
vulnerability), or email the maintainer address on the GitHub profile. Please do not open a
public issue for an unfixed vulnerability. Expected first response within 5 working days.
