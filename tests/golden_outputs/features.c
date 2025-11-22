#include <stdio.h>
void test_pointers(void) {
    int x = 5;
    int *px = &x;
    int v = (*px);
    (*px) = 10;
    int arr[10];
    int *p0 = &arr[0];
    int **pp = &px;
    (*(*pp)) = 42;
}
void test_arrays(void) {
    int arr[5] = {1, 2, 3, 4, 5};
    int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};
    matrix[1][2] = 42;
    int sparse[10] = {[0] = 1, [5] = 6, [9] = 10};
}
void test_qualifiers(void) {
    const int x = 5;
    volatile int flag;
    unsigned int u = 42;
    unsigned long long big = 1000000;
}
void test_casts(void) {
    int i = ((int)(3.14));
    void *vp;
    int *p = ((int*)(vp));
    char c = ((char)(65));
}
void test_inc_dec(void) {
    int i = 0;
    i++;
    ++i;
    i--;
    --i;
    int arr[10];
    arr[i++] = 5;
}
void test_control(void) {
    int x = 5;
    if (x > 0) {
        printf("positive\n");
    } else if (x < 0) {
        printf("negative\n");
    } else {
        printf("zero\n");
    }
    while (x < 10) {
        x += 1;
    }
    for (int i = 0; i < 5; i++) {
        printf("%d\n", i);
    }
    do {
        x++;
    } while (x < 20);
}
#ifdef DEBUG
printf("Debug mode\n");
#endif
#define BUFFER_SIZE 1024
#define PI 3.14159
#define SQUARE(x) ((x * x))
#define MIN(a, b) ((a < b ? a : b))
typedef struct Point {
    int x;
    int y;
} Point;
void test_struct(void) {
    Point p = {10, 20};
    struct Point q = {.x = 5, .y = 10};
    p.x = 3;
}
typedef union Data {
    int i;
    float f;
    char c;
} Data;
void test_union(void) {
    Data d;
    d.i = 42;
    d.f = 3.14;
}
typedef enum Color {
    RED = 0,
    GREEN = 1,
    BLUE = 2,
} Color;
void test_enum(void) {
    Color c = RED;
    if (c == GREEN) {
        printf("green\n");
    }
}
void test_goto(void) {
    int i = 0;
LOOP:
    if (i > 10) {
        goto END;
    }
    i++;
    goto LOOP;
END:
    printf("done\n");
}