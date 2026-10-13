You are being evaluated by an automated benchmark that measures what it takes for an AI coding agent
to build an application and deploy it to {cloud_name} ({cloud_url}). No human is available: never
wait for input or confirmation, make reasonable decisions on your own, and keep going until the task
is complete.

This is step 1 of 2: build the application. Deploying it to {cloud_name} is step 2.

- Build the application specified in `TASK.md` (copied below) in the current directory.
- It will run on {cloud_name}, so choose a stack and project layout that suit how {cloud_name} runs
  applications.
- Make sure it works locally: install dependencies, start it, and exercise every requirement, for
  example with curl. Add automated tests where they are cheap to write.
- Don't deploy anything or create cloud resources yet. Cloud credentials aren't available in this step.
- When you're done, stop any servers you started and reply with a short summary of the stack and how
  to run the app.

Environment: a fresh GitHub Actions Ubuntu runner (user `runner`, passwordless sudo) with Node.js,
Python, Docker, git and internet access.

---

{task}
