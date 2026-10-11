AI Native Software Engineering and Spec Driven Development

https://openai.com/index/harness-engineering/

Context engineering:
what matters most isn’t how clever your prompt is. It’s whether the model receives the right information to reason well. Your system prompt, your rules files, the code snippets you reference, the tool definitions the runtime injects, the conversation history that accumulates over the session: all of it lands in the context window and shapes what the agent does next.
Context engineering is the discipline of making that context work well. It means deciding what to include and what to leave out, structuring information so the model’s attention lands where it matters, and keeping the context accurate as sessions evolve and codebases change.
The agent that works well in your codebase today isn’t a better model than the one that made mistakes last month. It’s the same model with better context.
Rules file: A rules file committed to your repository benefits every engineer on the team, in every session, automatically. 
Skill file: A skill written once for a recurring task type provides its benefits every time that task is performed.

Prompt engineering is a local optimization: tuning one input for one interaction. 
Context engineering is a systems discipline: managing the full state the model sees across an entire session, and across all the sessions your team runs over the lifetime of a project.

The model’s attention capacity, its ability to weigh every piece of information appropriately, gets stretched thinner as the context grows longer.
We only have about 50% of our context window that's effective. Context rot, earlier insights are sandwiched in the middle between static prompts at the start and recent output at the end. 
As humans, we rely on our second brain to safekeep and record information. AI succumbs to the same limitation, it also needs to refer to external files. 


Story:
Engineer A opens their AI assistant and types: “Add rate limiting to the payment endpoint, max 10 requests per minute.” The agent produces a response in 30 seconds. It creates a middleware function that uses a sliding-window algorithm keyed on the client IP address, installs a Redis client dependency to track counts, and adds the middleware to the route. The code looks clean. The tests the agent generates pass. Engineer A reviews the output, sees nothing obviously wrong, and merges the pull request.

An incident surfaces three days later. A user behind a corporate NAT gateway, where hundreds of employees share a single IP address, is being rate-limited even though they have barely used the API. Meanwhile, a user with a dynamic residential IP who has been submitting fraudulent payment attempts is bypassing the limit entirely by reconnecting through a different address. The implementation was technically correct for the problem as stated. The problem was never stated correctly.

Engineer B receives the same ticket. Before opening the AI assistant, they spend 10 minutes writing. They note that:

rate limiting must be per authenticated user, not per IP, because the existing user base includes corporate customers behind shared NATs

the existing auth middleware already attaches a user_id to every authenticated request, so the rate limiter should key on that

the retry logic for idempotent payment operations must not count toward the limit if the request carries the same idempotency key

the existing observability stack expects rate limit events to emit a specific metric format, and they paste in the format from the metrics conventions document

the Redis instance available for this service is in the same availability zone

the team has an approved wrapper library for cache access.

Future looking:
Exceptional engineers in the AI era are those who can define the right problem, design the right system, and own the quality of the result.

AI changes what engineers spend their time on. It does not make engineering unnecessary. The demand for people who can define complex systems, verify that they work, and own their quality is not going down. What is changing is the tools to which those people have access.
Frederick P. Brooks on the Essence of Software Engineering, there's no silver bullet -- the hard problem of software engineering is what we say, not how to say it. 

The traditional software-engineering workflow was designed when the bottleneck was implementation speed. A senior engineer’s primary value was in the quality and speed of their implementation across this chain.
However, today, implementation speed is no longer a limitation -- AI can produce a first pass within minutes. The constraint shifts upstream, to requirement clarity and specification quality; and downstream to verify the implementation meets those. 
Also, before we owned the code implementation. Today AI writes the code, we own the decisions. Decisions guided by our judgement to either accept or reject a work artefact. Historically, we'd refine our understanding of the problem during coding implementation. 
A good design emerged as we played around in the code for a while, we got our hands dirty. However, AI doesn't accumulate understanding the way we do, if a task is underspecified it makes assumptions to complete the task (sometimes the quickest way to solve a problem, not necessarily the best way to solve a problem).

Barry Boehm’s analysis of 1970s TRW and IBM projects, reported in his book Software Engineering Economics (Prentice Hall, 1981), showed that the relative cost of fixing defects increases sharply the later they are found.
In large projects, he found, a requirements defect discovered in operation can cost up to two orders of magnitude more to correct than one caught during the requirements or early design phase. AI amplifies this ratio, because fast generation means you can accumulate a large volume of misaligned output quickly before anyone notices.
The hard problem to solve for: ALIGNMENT!!!

Human in the loop (calibrated automation over maximum automation):
- Reviewing specs before execution
- Reviewing output before integration
- Escalating high-risk decisions
HITL is fastest when we do it at specification time, before the agent generates anything. A 10-minute spec review can prevent hours of correcting a misaligned implementation

you need the skills that sit at the intersection of judgment, communication, and system ownership

<img width="1886" height="1074" alt="image" src="https://github.com/user-attachments/assets/3f862a3f-b20a-46ce-aba2-e513dda10ed7" />

https://martinfowler.com/articles/harness-engineering.html
https://martinfowler.com/articles/exploring-gen-ai/13-role-of-developer-skills.html
https://en.wikipedia.org/wiki/Jevons_paradox

Why specs?:
Discuss embeddings, mathematical calculations on embeddings, and how related concepts emerge as we conduct regression. King, Queen, male and female

https://jsdevai.com/pillars/spec-driven-development/
https://github.com/alfonsograziano/ai-native-engineering







