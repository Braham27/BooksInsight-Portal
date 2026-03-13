# Open-source components we discussed and how they fit

## 1. **PSLmodels Tax-Calculator** (Primary engine in the plan)

Role in the architecture: **Tax calculation engine**

Why it was chosen:

* Models **US federal tax law**
* Deterministic calculations
* Permissive license (public domain / CC0)
* Widely used by economists and policy researchers
* Easier for commercial integration

In the architecture I wrote, this component sits here:

```
User → AI interview → Structured tax data
                      ↓
               Tax-Calculator
                      ↓
            Refund / liability
```

So yes, this one **was fully integrated into the plan.**

---

# 2. **PolicyEngine / OpenFisca**

Role: **alternative rule engine**

This was **not placed in the MVP architecture** for one main reason.

### License issue

PolicyEngine uses **AGPL**.

That means if you modify it and run it as a network service, you may need to **release your source code**.

For an internal system that might be fine.
For a future commercial product it can become restrictive.

Because you said:

> "Internally first, then maybe for business"

I recommended **Tax-Calculator first**.

But the architecture I wrote allows swapping engines later.

---

# 3. **IRS Direct File open source code**

Role: **reference architecture**

This is not a tax engine.

It is useful for studying:

* validation rules
* form flows
* UI patterns
* interview logic

It was **not included in the core system**, but you could study it to design your UI.

---

# What the architecture currently contains (open source)

### Core tax engine

* **Tax-Calculator**

### Potential additions

You could add open source components for other layers.

Examples:

Document processing

* **Tesseract OCR**
* **LayoutParser**

API backend

* **FastAPI**

Database

* **PostgreSQL**

Queue

* **Redis**

Object storage

* **MinIO**

These are not tax specific but they are open source and commonly used.

---

# Full open-source stack version (recommended)

If you want a **mostly open-source system**, it could look like this:

```
Frontend
Next.js

Backend
FastAPI

LLM layer
OpenAI or open source LLM

OCR
Tesseract

Document parsing
LayoutParser

Database
PostgreSQL

Object storage
MinIO

Queue
Redis

Tax engine
Tax-Calculator
```

---

# The most important open-source piece

Everything else can be swapped.

The **hardest part of tax software** is:

**encoding tax law correctly**

That is why the engine matters.

And among open source projects, **Tax-Calculator is the strongest US-focused option.**

---

# Critical warning (technical)

Most people building “AI tax apps” make a huge mistake.

They let the **LLM compute taxes**.

That is wrong.

Correct architecture:

```
AI = interview + explanation
Engine = tax math
```

This separation is what makes the system reliable.

---

If you want, I can also show you something very useful for your project:

**The 5 hardest technical problems you will face building this system.**

Most teams fail because they underestimate them.
