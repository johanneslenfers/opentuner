#include "algorithm.h"
#include <stdlib.h>

#define BLOCK_SIZE 32  // Adjust based on your CPU cache size

// Standard tiled matrix multiplication without AVX
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
                        double sum = C[i * size + j];
                        for (int k = kk; k < kk + BLOCK_SIZE && k < size; k++) {
                            sum += A[i * size + k] * B[k * size + j];
                        }
                        C[i * size + j] = sum;
                    }
                }
            }
        }
    }
}
