# Prompt

Create a benchmark that measures what it takes to build and deploy applications to different cloud providers (see clouds.md) when using an AI coding agent, like Claude Code, using different models (see models.md).

API keys for each service will be provided for you to store in github actions secrets. API keys to the models will also be provider for you to store in github actions secrets.

The benchmark should measure completion success, tokens used, time taken to build, time taken to deploy, expected monthly cost, etc.

The benchmark should run in GitHub with a different session for each cloud provider, then the results are collected and the results are committed to this repo under a /results folder time high-level results shown in the README file at the root of this folder.