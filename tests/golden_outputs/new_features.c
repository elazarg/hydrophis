#include <stdio.h>
void test_list_arrays(void) {
    int a[10];
    char *b[5];
    struct Node c[3];
}
struct Buffer {
    int len;
    char data[];
};
struct Flags {
    unsigned int a : 3;
    unsigned int b : 5;
    int c : 1;
};
struct {
    int x;
    int y;
} point_a, point_b;
union {
    int i;
    float f;
} data_u;
void test_infinite_loop(void) {
    int i = 0;
    for (;;) {
        i++;
        if (i > 10) {
            break;
        }
    }
}
void test_do_while(void) {
    int i = 0;
    do {
        printf("%d\n", i);
        i++;
    } while (i < 5);
}
#ifdef DEBUG
printf("debug mode\n");
#elif defined(VERBOSE)
printf("verbose mode\n");
#elif defined(QUIET)
printf("quiet mode\n");
#else
printf("normal mode\n");
#endif
#ifndef DISABLE_LOGGING
printf("logging enabled\n");
#elif defined(ERROR_ONLY)
printf("errors only\n");
#else
printf("logging disabled\n");
#endif
void test_switch(int x) {
    switch (x) {
    case 1:
        printf("one\n");
        break;
    case 2:
        printf("two or three\n");
    case 3:
        printf("three\n");
        break;
    default:
        printf("other\n");
        break;
    }
}
struct Node {
    int data;
    struct Node *next;
};
typedef struct List {
    struct Node *head;
} List;
void consume(List *l) {
    switch (l->head->data) {
    case 0:
        break;
    default:
        break;
    }
}
int main(void) {
    return 0;
}