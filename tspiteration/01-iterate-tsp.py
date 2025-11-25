#!/usr/bin/env python3

import itertools as it

### Traveling salesman problem - brute force solution - asymptotic runtime: O(n!) ###


def bruteforcetsp(portnames: list, distances: list):

    input = []
    output = []
    counter = 1
    distance = []

    for a in range(1, len(portnames)):
        input.append(int(counter))
        counter += 1

    for iteration in it.permutations(input, len(portnames) - 1):
        list = [0]

        for number in iteration:
            list.append(number)

        output.append(list)

    print("All possible route options calculated:")

    for element in output:
        print(" ".join([portnames[i] for i in element]))

    # The following code snippet below was generated, source: https://copilot.microsoft.com/
    for sublist in output:
        total = 0

        for x in range(len(sublist) - 1):
            city1 = sublist[x]
            city2 = sublist[x + 1]
            total += distances[city1][city2]

        total += distances[sublist[-1]][sublist[0]]
        distance.append(total)
    # Generated code snippet from source above ends here.

    print("The optimal / shortest routes are these:")

    for y in range(1, len(distance)):
        if distance[y] == min(distance):
            print(" ".join([portnames[j] for j in output[y]]), f"{portnames[0]}")

    print(f"The optimal / shortest distance is: {min(distance)} km")


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
    bruteforcetsp(portnames, distances)

### Note: This code was not submitted to the cited online course, as lines 33 - 42 were AI generated; ###
