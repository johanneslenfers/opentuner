#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "algorithm.h"

// Function to initialize a matrix with random values
void initialize_matrix(double matrix[N][N], int seed) {
    srand(seed);
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            matrix[i][j] = (double)(rand() % 100) / 10.0;  // Random values between 0.0 and 10.0
        }
    }
}

// Function to verify the result
int verify_result(double C[N][N], double C_ref[N][N]) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (abs(C[i][j] - C_ref[i][j]) > 1e-6) {
                return 0;  // Verification failed
            }
        }
    }
    return 1;  // Verification passed
}

int main() {
    double A[N][N], B[N][N], C[N][N], C_ref[N][N];
    clock_t start, end;

    // Initialize matrices
    initialize_matrix(A, 1);
    initialize_matrix(B, 2);

    // Compute reference result
    matmul(A, B, C_ref);

    // Measure performance
    start = clock();
    matmul(A, B, C);
    end = clock();

    // Verify the result
    if (verify_result(C, C_ref)) {
        printf("Verification passed!\n");
    } else {
        printf("Verification failed!\n");
        return 1;
    }

    // Report execution time
    double time_taken = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Time: %f\n", time_taken);

    return 0;
}
