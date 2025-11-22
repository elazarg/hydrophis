#include <stdio.h>
#include <stdlib.h>
#define MAX_SIZE 100
typedef struct Node {
    int data;
    Node *next;
} Node;
Node* create_node(int value) {
    Node *node = malloc(sizeof(Node));
    if (node == NULL) {
        return NULL;
    }
    node->data = value;
    node->next = NULL;
    return node;
}
void print_list(Node *head) {
    Node *curr = head;
    while (curr != NULL) {
        printf("%d ", curr->data);
        curr = curr->next;
    }
    printf("\n");
}
#define MAX(a, b) ((a > b ? a : b))
int main(void) {
    Node *head = create_node(1);
    head->next = create_node(2);
    head->next->next = create_node(3);
    print_list(head);
    for (int i = 0, j = 10; i < 5; i++, j--) {
        printf("i=%d, j=%d\n", i, j);
    }
    do {
        i++;
        printf("i=%d\n", i);
    } while (i < 10);
    return 0;
}