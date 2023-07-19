def find_internal_nodes_num(tree):
    parent_count = [0] * len(tree)

    for node in tree:
        if node != -1:
            parent_count[node] += 1

    return sum(count > 0 for count in parent_count)

my_tree = [4, 4, 1, 5, -1, 4, 5]
find_internal_nodes_num(my_tree)