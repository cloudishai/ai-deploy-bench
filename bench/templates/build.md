You are being evaluated by an automated benchmark that measures what it takes for an AI coding agent
to build an application and deploy it to {cloud_name} ({cloud_url}). No human is available: never
wait for input or confirmation, make reasonable decisions on your own, and keep going until the task
is complete.

This is step 1 of 2: build the application. Deploying it to {cloud_name} is step 2.

- Build the application specified in `TASK.md` (copied below) in the current directory.
- Before writing any code, decide the stack and record it in `STACK.md`: the two or three most
  plausible options for this app on {cloud_name} (they may differ in language, framework, data
  store or hosting model, for example static files versus a server), how each fares on
  simplicity, reliability and fit with {cloud_name}, and which you chose and why. There is no
  default language or framework; choose what fits this app best.
- Make sure it works locally: install dependencies, start it, and exercise every requirement, for
  example with curl. Add automated tests where they are cheap to write.
- Don't deploy anything or create cloud resources yet. Cloud credentials aren't available in this step.
- When you're done, stop any servers you started and reply with a short summary of the stack and how
  to run the app.

Environment: a fresh GitHub Actions Ubuntu runner (user `runner`, passwordless sudo) with the
usual languages and runtimes (Node.js, Python, Go, Java, Ruby, PHP, .NET), Docker, git and
internet access.

---

{task}
