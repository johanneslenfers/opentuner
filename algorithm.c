#include "algorithm.h"
#include <stdlib.h>
#include <immintrin.h>  // For AVX/AVX2 intrinsics

#define BLOCK_SIZE 32  // Adjust based on your CPU cache size

// Optimized matrix multiplication using AVX and 1D indexing
void matmul(double* A, double* B, double* C, int size) {
    // Initialize result matrix to zero
    for (int i = 0; i < size * size; i++) {
        C[i] = 0.0;
    }

    // Tiled matrix multiplication
    for (int ii = 0; ii < size; ii += BLOCK_SIZE) {
        for (int jj = 0; jj < size; jj += BLOCK_SIZE) {
            for (int kk = 0; kk < size; kk += BLOCK_SIZE) {
                // Compute block multiplication
                for (int i = ii; i < ii + BLOCK_SIZE && i < size; i++) {
                    for (int j = jj; j < jj + BLOCK_SIZE && j < size; j++) {
                        __m256d c_vec = _mm256_loadu_pd(&C[i * size + j]); // Load C[i][j] into vector
                        for (int k = kk; k < kk + BLOCK_SIZE && k < size; k += 4) {
                            __m256d a_vec = _mm256_loadu_pd(&A[i * size + k]); // Load 4 values from A[i][k]
                            __m256d b_vec = _mm256_loadu_pd(&B[k * size + j]); // Load 4 values from B[k][j]
                            c_vec = _mm256_fmadd_pd(a_vec, b_vec, c_vec); // Multiply and accumulate
                        }
                        _mm256_storeu_pd(&C[i * size + j], c_vec); // Store back to C[i][j]
                    }
                }
            }
        }
    }
}
