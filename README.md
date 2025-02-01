# Mind-Evolution

I referred to this paper https://arxiv.org/pdf/2501.09891 and designed this system according to its principles.

Mind Evolution is a genetic-based evolutionary search strategy that operates in natural language
space. The figure illustrates how Mind Evolution evolves a population of solution candidates toward higher
quality candidates for a travel planning task. The candidate population is improved through an iterative process,
where an LLM is used to recombine and refine candidates in each iteration.

![image](https://github.com/ch-tseng/Mind-Evolution/blob/main/flow.PNG)

The specific process is as follows:
1. Generate initial candidate solutions: The model generates multiple initial candidate solutions.
2. Evaluation and feedback: The evaluator evaluates each candidate and provides feedback, pointing out problems and areas for improvement in the candidate.
3. Improve candidate solutions: Based on the feedback from the evaluator, the model improves the candidate solutions. This process includes operations such as selection, crossover, and mutation to generate new candidate solutions.
4. Repeated evaluation and improvement: New candidate solutions are evaluated and improved again, and this process is repeated until a satisfactory solution is found or the limitation of computing resources is reached.
