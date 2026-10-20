# Oxiworld / Oxidane

A SaaS learning-platform project with a Django backend and Next.js frontend. The repository includes backend code and deployment/operational support files.

## Project Focus

The project explores subscription-based access to learning content and integrations for account access and payments.

## Main Components

- Django backend
- Next.js and TypeScript frontend
- PostgreSQL data layer
- Subscription and payment workflows
- Authentication and connected-service integrations
- Operational scripts for checking selected deployment and service behaviours

## Technology

Django · Next.js · TypeScript · PostgreSQL · Redis · Celery · Gunicorn · Nginx

## Live Demo

[Open the web application](https://oxidane-two.vercel.app/)

## Repository Layout

- `backend/` — backend application
- `Procfile` — process configuration used by the deployment environment
- `check_*.py` and related scripts — operational checks for selected service behaviours

## Local Development

The project requires its backend and frontend dependencies plus environment-specific configuration for services such as the database, authentication, and payment provider. Review the configuration and dependency files in `backend/` before running it locally.

Do not commit credentials, API keys, payment secrets, or production environment files. Use environment variables and local-only configuration for development.

## Important

This README is an initial project overview, not a complete deployment guide. Before a new contributor can reproduce the environment reliably, document the exact backend/frontend setup commands, required environment variables (names only, never secret values), database migration steps, and test commands.
