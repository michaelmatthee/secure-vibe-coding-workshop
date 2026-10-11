AI Native Software Engineering and Spec Driven Development

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



Why specs?:
Discuss embeddings, mathematical calculations on embeddings, and how related concepts emerge as we conduct regression. King, Queen, male and female







