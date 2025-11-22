#include <stdio.h>
struct PlainStruct {
    int a;
    int b;
};
struct PlainStruct x;
struct PlainStruct *ptr;
typedef struct TypedefStruct {
    int x;
    int y;
} TypedefStruct;
TypedefStruct ts;
struct TypedefStruct ts2;
struct VarStruct {
    int data;
} v1;
struct MultiVarStruct {
    int value;
} v2, v3, v4;
typedef struct Combined {
    int field;
} Combined;
Combined c1, c2;
void test(void) {
    TypedefStruct t;
    t.x = 10;
    t.y = 20;
    TypedefStruct *p = &t;
    p->x = 5;
    TypedefStruct arr[3];
    arr[0] = {1, 2};
}
void test2(void) {
    struct PlainStruct ps;
    ps.a = 1;
    ps.b = 2;
    struct PlainStruct *pptr = &ps;
    pptr->a = 3;
}
typedef struct Point {
    int x;
    int y;
} Point;
typedef struct Point *PointPtr;
void test3(void) {
    PointPtr pp;
}
enum Color {
    RED = 0,
    GREEN = 1,
    BLUE = 2,
};
void test4(void) {
    enum Color c = RED;
    if (c == GREEN) {
        printf("green\n");
    }
}
union Data {
    int i;
    float f;
};
void test5(void) {
    union Data d;
    d.i = 42;
}
struct ExplicitStruct {
    int value;
};
void test6(void) {
    struct ExplicitStruct es;
    es.value = 100;
}