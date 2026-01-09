#!/usr/bin/env python3

### Traveling salesman problem - comparing algorithm - asymptotic runtime: O(n^2) ###


def comparingtsp(portnames: list, distances: list):

    initialvalue = len(portnames) // 2

    paths = []
    costs = []

    startrow = distances[0]

    candidates = [i for i in range(1, len(portnames)) if i != 0]
    candidates.sort(key=lambda j: startrow[j])

    for k in range(0, initialvalue):
        paths.append([0, candidates[k]])
        costs.append(distances[0][candidates[k]])

    print("The comparing route options calculated:")

    for diststep in range(2, len(portnames)):
        for p in range(initialvalue):
            route = paths[p]

            visitedcity = set(route)
            currentcity = route[-1]

            options = [(distances[currentcity][q], q) for q in range(len(portnames)) if q not in visitedcity]

            for element in options:
                value, index = element
                print(f"Processing... {portnames[index]} ({value} km)")

            if not options:
                continue

            distance, nextrow = min(options)

            paths[p].append(nextrow)
            costs[p] += distance

    for x in range(1, initialvalue):
        wayback = paths[x][-1]

        paths[x].append(0)
        costs[x] += distances[wayback][0]

    bestindex = min(range(1, initialvalue), key=lambda y: costs[y])
    bestpath = paths[bestindex]
    bestcost = costs[bestindex]

    print("The heuristic / comparative route is this:")
    print(" ".join(portnames[z] for z in bestpath))
    print(f"The heuristic / comparative distance is: {bestcost} km")


if __name__ == "__main__":
    # Example and exercise from online course, source: https://buildingai.elementsofai.com/
    portnames = ["PAN", "AMS", "CAS", "NYC", "HEL"]

    # Nautical miles converted to km, source: https://sea-distances.org/
    distances = [
        [0, 8943, 8019, 3652, 10545],
        [8943, 0, 2619, 6317, 2078],
        [8019, 2619, 0, 5836, 4939],
        [3652, 6317, 5836, 0, 7825],
        [10545, 2078, 4939, 7825, 0]
    ]

    # Function arguments portnames and distances (table / matrix) are variable exchangeable.
    comparingtsp(portnames, distances)

### Exact description of this simple comparative algorithmic approach stepwise written below: ###


# 0. Divide the input n (e.g. the length of the adjacency matrix) by 2 down to the nearest integer - so the calculation would be: n // 2 = x = result.
# 1. Set the variables in the count of the result from the initial calculation (0.) for the total distances and the comparison distances to 0 km.
# 2. Ignore the position that is the starting position, even for the comparison distances.
# 3. Depending on the result of the initial calculation (0.), go on with the following steps (3.x) in the number of that result from the calculation:
# 3.1 Select the shortest distance from the row with the starting position and add it to the total distance.
# 3.2 Select the second shortest distance from the starting position and add it to the first comparison distance.
# 3.3 Select the third shortest distance from the starting position and add it to the second comparison distance.
# 3.4 And so on and so fo(u)rth... ;-)
# 4. For each distance and comparison variable, go simultaneously to the row of the adjacency matrix with the same column index as the value selected from the previous row.
# 5. Ignore the positions that are not the current positions and those that can be traced back to the values / indices already mentioned for the total distance and the comparative distances.
# 6. Compare all total distances and comparative distances - and proceed with the shortest one - or with all, if they are the same.
# 7. Repeat this iteratively from step 3.1 until all indices have been processed.
# 8. In the final step, calculate the maximum value from the last row or the first row / remaining value / remaining index on it.
# 9. Output whichever distance is the shortest in km and the optimal route from the calculations above and terminate the algorithm.
