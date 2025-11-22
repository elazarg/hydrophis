from stdio import *
from stdlib import *

MAX_SIZE: macro = 100              # #define MAX_SIZE 100

class Node:
    data: int
    next: -Node

def create_node(value: int) -> -Node:
    node: -Node = malloc(sizeof(Node))
    if node == None:
        return None
    node._.data = value
    node._.next = None
    return node

def print_list(head: -Node) -> void:
    curr: -Node = head
    while curr != None:
        printf("%d ", curr._.data)
        curr = curr._.next
    printf("\n")

def MAX(a, b):                     # macro
    a if a > b else b

def main() -> int:                 # function
    head: -Node = create_node(1)
    head._.next = create_node(2)
    head._.next._.next = create_node(3)

    print_list(head)

    # C-style for: for (int i = 0, j = 10; i < 5; i++, j--)
    for (i, j) in (int, int)((i := 0, j := 10))(i < 5)((i ** _, j // _)):
        printf("i=%d, j=%d\n", i, j)

    # do { ... } while (i < 10);
    while ():
        i ** _
        printf("i=%d\n", i)
        if i < 10:
            continue

    return 0
