## Casual-TSP-Iterations

In this repository I will publish my experiments regarding the P-NP-Problem (which is one of the Millennium Prize Problems and one of the most important unresolved problems of the theoretical computer science and computational complexity theory). Especially the Traveling Salesman Problem (TSP) as one of the NP-complete problems is in focus of my experiments in here. The algorithms are - for experimentations sake and exact comparable calculations - implemented in Python 3 and follow an example for a TSP from the University of Helsinki in its online course on "Building AI" (via "Elements of AI"), which inspired me besides my cooperative studies in computer science at Berlin School for Economics and Law and pracitical phases at DB Systel GmbH to use some of my free time on it - as I think this could also be a useful training for problems I will face while I'm working at DB Systel GmbH and in general for a railway or logistics company.

**01-iterate-tsp.py** is my first naively implemented and logically scaleable - but not runtime scaleable - exact solution to the TSP with mainly a brute-force approach and different list operations - written in Python. The asymptotic runtime would be O(n!), which is no solution in terms of efficiency and with this far away from a solution to the overall P-NP-Problem.

**02-greedy-tsp.py** is my second implemented algorithmic approach, also a logically scaleable and this time also runtime scaleable - but not exact - solution to the TSP with mainly a greedy approach - written in Python. The asymptotic runtime would be O(n^2), which is a polynomial solution in terms of efficiency but not an effective solution to the overall P-NP-Problem.

**...maybe more to come...**
