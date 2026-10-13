# Apps

Five categories that form a solid, practical benchmark for building web apps. They cover a wide range of architectural and functional complexity while remaining simple enough to implement and compare (e.g., time, lines of code, tools required, deployment difficulty, or AI-assisted development performance).

## 1. Static Content Site
**The app**: A company landing page with a few pages (Home, About, Contact) and a contact form.  
**Why this category**: Baseline for pure frontend work. No database, minimal or no backend. Tests HTML/CSS/JS, static site generators, or JAMstack tools, plus basic form handling (often via a third-party service).

## 2. Database-Backed CRUD App
**The app**: A multi-user todo list for small teams, with authentication (sign up, log in, create/read/update/delete tasks).  
**Why this category**: Classic full-stack web app. Requires database (SQLite/Postgres), auth, server-side logic or API routes, and a frontend. Represents the majority of SaaS/internal tools and community-style apps.

## 3. API / Backend Service
**The app**: A public REST API for notes, run as a personal side project, with API key authentication and rate limiting.  
**Why this category**: Focuses on backend design, data modeling, authentication, documentation (OpenAPI), and consumption by other clients. Covers pure APIs, MCP servers, and microservice-style components with little or no UI.

## 4. Data / Visualization App
**The app**: An interactive sales dashboard for a small company that loads its order data from a CSV and lets users filter and visualize it.  
**Why this category**: Emphasizes data handling, interactivity, and rapid UI generation. Common in analytics, BI, internal tools, and Python-centric workflows.

## 5. Real-Time Collaborative App
**The app**: A multi-user chat room for a hobby club, where members see each other's messages live (using WebSockets or Server-Sent Events).  
**Why this category**: Adds concurrency, live synchronization, and state management challenges. Represents modern collaborative tools, live dashboards, and apps that feel more “native.”

These five give a good spectrum:
- Static (content only)
- Traditional full-stack with persistence
- API-first / headless
- Data-centric / low-code style
- Real-time / concurrent

Each app describes one concrete product rather than a choice of examples, so every agent builds the same thing. The descriptions also imply who runs it, because hosting plans depend on that: some free plans are for non-commercial use only. Three apps are a business's (the landing page, the team todo list and the sales dashboard) and two are personal or community projects (the notes API and the club chat), so the comparison includes both. The specs never say it outright; the agent has to infer it, as it would from a real request.

They are intentionally simple so a benchmark can measure things like scaffolding time, feature completeness, code quality, deployment, and maintainability without requiring weeks of work.