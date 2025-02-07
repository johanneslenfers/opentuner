#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <immintrin.h>  // For AVX/AVX2 intrinsics
#include "algorithm.h"

#define N 512  // Define matrix size
#define BLOCK_SIZE 32  // Adjust based on your CPU cache size
#define NUM_RUNS 5  // Number of runs for median timing

// Function to allocate a dynamic 1D matrix
double* allocate_matrix(int size) {
    double* matrix = (double*)malloc(size * size * sizeof(double));
    if (!matrix) {
        perror("Memory allocation failed");
        exit(EXIT_FAILURE);
    }
    return matrix;
}

// Function to free a dynamic 1D matrix
void free_matrix(double* matrix) {
    free(matrix);
}

// Function to initialize a matrix with random values
void initialize_matrix(double* matrix, int size, int seed) {
    srand(seed);
    for (int i = 0; i < size; i++) {
        for (int j = 0; j < size; j++) {
            matrix[i * size + j] = (double)(rand() % 100) / 10.0;  // Random values between 0.0 and 10.0
        }
    }
}

// Function to verify the result
int verify_result(double* C, double* C_ref, int size) {
    for (int i = 0; i < size; i++) {
        for (int j = 0; j < size; j++) {
            if (abs(C[i * size + j] - C_ref[i * size + j]) > 1e-6) {
                return 0;  // Verification failed
            }
        }
    }
    return 1;  // Verification passed
}

// Function to flush cache by writing a large dummy array
void flush_cache() {
    size_t cache_size = 32 * 1024 * 1024; // Assume a 32MB cache size
    char *dummy = (char*)malloc(cache_size);
    if (dummy) {
        for (size_t i = 0; i < cache_size; i++) {
            dummy[i] = i % 256;
        }
        free(dummy);
    }
}

// Function to compute median of execution times
double median_time(double* times, int num_runs) {
    for (int i = 0; i < num_runs - 1; i++) {
        for (int j = i + 1; j < num_runs; j++) {
            if (times[i] > times[j]) {
                double temp = times[i];
                times[i] = times[j];
                times[j] = temp;
            }
        }
    }
    return times[num_runs / 2];
}

int main() {
    double* A = allocate_matrix(N);
    double* B = allocate_matrix(N);
    double* C = allocate_matrix(N);
    double* C_ref = allocate_matrix(N);
    double times[NUM_RUNS];

    // Initialize matrices
    initialize_matrix(A, N, 1);
    initialize_matrix(B, N, 2);

    // Compute reference result
    matmul(A, B, C_ref, N);

    // Execute multiple runs and measure time
    
    for (int run = 0; run < NUM_RUNS; run++) {
        printf("Run %d: ", run + 1);
        // Clear output matrix
        for (int i = 0; i < N * N; i++) {
            C[i] = 0.0;
        }
        flush_cache();  // Ensure fresh execution
        clock_t start = clock();
        matmul(A, B, C, N);
        clock_t end = clock();
        times[run] = ((double)(end - start)) / CLOCKS_PER_SEC;
        printf("%f seconds\n", times[run]);
    }

    // Compute median execution time
    double time_median = median_time(times, NUM_RUNS);

    // Verify the result
    if (verify_result(C, C_ref, N)) {
        printf("Verification passed!\n");
    } else {
        printf("Verification failed!\n");
        return 1;
    }

    // Report median execution time
    printf("Median Time: %f\n", time_median);

    // Free allocated memory
    free_matrix(A);
    free_matrix(B);
    free_matrix(C);
    free_matrix(C_ref);

    return 0;
}
