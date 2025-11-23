#include <stdio.h>
void test_casts(void) {
    int x = 42;
    float y = ((float)(x));
    void *p = ((void*)(x));
    char c = ((char)(65));
}
void test_escaped_identifiers(void) {
    int _ = 5;
    char *FILE__ = "test.c";
    int x = 10;
}
#define MAX 100
#define MIN 0
#undef MAX
#undef MIN
#define DEBUG 1
#define VERBOSE 2
#undef DEBUG
#undef VERBOSE
_Atomic int counter;
_Atomic int *ptr;
_Alignas(16) int aligned_var;
_Alignas(64) int aligned_array[10];
void test_alignof(void) {
    size_t a = _Alignof(struct Node);
    size_t b = _Alignof(int);
}
struct Node {
    int data;
    struct Node *next;
};
void test_static_assert(void) {
    _Static_assert(sizeof(struct Node) > 0, "Node size must be positive");
}
_Thread_local int tls_var;
static _Thread_local int static_tls;
struct Outer {
    int a;
    struct {
        int x;
        int y;
    };
    int b;
};
struct Tagged {
    int tag;
    union {
        int i;
        float f;
        double d;
    };
};
struct Widget {
    enum {
        RED = 0,
        GREEN = 1,
        BLUE = 2,
    } color;
    int value;
};
enum {
    OK = 0,
    ERROR = 1,
    PENDING = 2,
} global_status;
typedef int BinaryFunc(int, int);
typedef void UnaryFunc(double);
typedef int NoArgFunc(void);
int add(int, int);
int (*callback)(int, int);
void (*handler)(void);
typedef int (*BinOp)(int, int);
int apply(int (*f)(int, int), int a, int b) {
    return f(a, b);
}
void test_function_cast(void) {
    void *ptr = ((void*)(0));
    int (*fp)(int, int) = ((int (*)(int, int))(ptr));
}
int main(void) {
    return 0;
}
