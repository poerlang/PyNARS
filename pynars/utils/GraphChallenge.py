"""
This is to generate a random strongly connected graph for testing NARS's question solving capability.

1. generate a complete connected graph.
2. randomly remove some edges.
3. randomly remove some edges again as "questions".
4. translate the graph as Narsese.

This is very brute-force and consider no efficiency.

Note that the graph might not be
"""
import random


def problem_generation(n):  # n is the number of vertices
    vertices = ["ID" + str(i) for i in range(n)]
    judgments = []
    questions = []
    for va in vertices:
        for vb in vertices:
            if va != vb:
                if random.random() < 0.5:  # keep 50% of a graph
                    if random.random() < 0.7:  # 70% of the graph is the belief
                        judgments.append("<" + va + "-->" + vb + ">.")
                    else:
                        questions.append("<" + va + "-->" + vb + ">?")
    for each in judgments:
        print(each)
    for each in questions:
        print(each)
    return judgments, questions

problem_generation(5)