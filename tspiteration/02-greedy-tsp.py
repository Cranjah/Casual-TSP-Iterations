#!/usr/bin/env python3

### Traveling salesman problem - greedy algorithm - asymptotic runtime: O(n^2) ###


def greedyalgotsp(portnames: list, distances: list):

    visitedcity = [True]
    currentcity = 0
    distance = 0
    route = [0]

    for a in range(1, len(portnames)):
        visitedcity.append(False)

    print("The greedy route option calculated:")

    while len(route) < len(portnames):
        nextcity = min(
            (i for i in range(len(portnames)) if not visitedcity[i]),
            key=lambda i: distances[currentcity][i],
        )

        diststep = distances[currentcity][nextcity]
        distance += diststep

        print(f"{portnames[currentcity]} ---> {portnames[nextcity]} ({diststep} km)")

        route.append(nextcity)

        visitedcity[nextcity] = True
        currentcity = nextcity

    distback = distances[currentcity][0]
    distance += distback

    route.append(0)

    print(f"{portnames[currentcity]} ---> {portnames[0]} ({distback} km)")

    print("The suboptimal / greedy route is this:")
    print(" ".join([portnames[j] for j in route]))
    print(f"The suboptimal / greedy distance is: {distance} km")


if __name__ == "__main__":
    # Example and exercise from online course, source: https://buildingai.elementsofai.com/
    portnames = ["PAN", "AMS", "CAS", "NYC", "HEL"]

    # Nautical miles converted to km, source: https://sea-distances.org/
    distances = [
        [0, 8943, 8019, 3652, 10545],
        [8943, 0, 2619, 6317, 2078],
        [8019, 2619, 0, 5836, 4939],
        [3652, 6317, 5836, 0, 7825],
        [10545, 2078, 4939, 7825, 0],
    ]

    # Function arguments portnames and distances (table / matrix) are variable exchangeable.
    greedyalgotsp(portnames, distances)

### Exact description of this simple greedy algorithmic approach stepwise written below: ###


# 0. Set the variable for the total distance to 0 km.
# 1. Go to the start position in the distance matrix (distances[0][0]).
# 2. Ignore the position that is the starting position.
# 3. Select the shortest distance from the row containing the starting position and add it to the total distance.
# 4. Go to the row with the same column index as the value selected from the previous row.
# 5. Ignore the positions that are not current positions and those that map back to the values / indices, that have already been mentioned.
# 6. Repeat this recursively/iteratively from step 3 until all indexes have been processed.
# 7. In the last step, calculate the maximum value from the last row or first row / the remaining value / index on it.
# 8. Output the total distance with the value in km and terminate the algorithm.
