# Apps

Five categories that form a solid, practical benchmark for building web apps. They cover a wide range of architectural and functional complexity while remaining simple enough to implement and compare (e.g., time, lines of code, tools required, deployment difficulty, or AI-assisted development performance).

## 1. Static Content Site
**Simple example**: A personal portfolio or company landing page with a few pages (Home, About, Contact) and a contact form.  
**Why this category**: Baseline for pure frontend work. No database, minimal or no backend. Tests HTML/CSS/JS, static site generators, or JAMstack tools, plus basic form handling (often via a third-party service).

## 2. Database-Backed CRUD App
**Simple example**: A multi-user todo list or personal task manager with authentication (sign up, log in, create/read/update/delete tasks).  
**Why this category**: Classic full-stack web app. Requires database (SQLite/Postgres), auth, server-side logic or API routes, and a frontend. Represents the majority of SaaS/internal tools and community-style apps.

## 3. API / Backend Service
**Simple example**: A public REST or GraphQL API that returns weather data (or a simple notes API) with API key authentication and rate limiting.  
**Why this category**: Focuses on backend design, data modeling, authentication, documentation (OpenAPI), and consumption by other clients. Covers pure APIs, MCP servers, and microservice-style components with little or no UI.

## 4. Data / Visualization App
**Simple example**: An interactive dashboard (Streamlit, Dash, or a simple React + charting library app) that loads a CSV or connects to a database and lets users filter and visualize sales or stock data.  
**Why this category**: Emphasizes data handling, interactivity, and rapid UI generation. Common in analytics, BI, internal tools, and Python-centric workflows.

## 5. Real-Time Collaborative App
**Simple example**: A shared whiteboard or multi-user chat room where multiple people can see updates live (using WebSockets or a real-time database like Supabase Realtime).  
**Why this category**: Adds concurrency, live synchronization, and state management challenges. Represents modern collaborative tools, live dashboards, and apps that feel more “native.”

These five give a good spectrum:
- Static (content only)
- Traditional full-stack with persistence
- API-first / headless
- Data-centric / low-code style
- Real-time / concurrent

They are intentionally simple so a benchmark can measure things like scaffolding time, feature completeness, code quality, deployment, and maintainability without requiring weeks of work.