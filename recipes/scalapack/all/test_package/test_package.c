#include <mpi.h>
#include <lapacke.h>
#include <stdio.h>

void sl_init_(lapack_int *ictxt, const lapack_int *nprow, const lapack_int *npcol);
void blacs_gridinfo_(const lapack_int *ictxt, lapack_int *nprow,
                     lapack_int *npcol, lapack_int *myrow, lapack_int *mycol);
void blacs_gridexit_(const lapack_int *ictxt);
void blacs_exit_(const lapack_int *continue_flag);

int main(int argc, char **argv) {
  MPI_Init(&argc, &argv);

  int world_size = 0, world_rank = 0;
  MPI_Comm_size(MPI_COMM_WORLD, &world_size);
  MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

  lapack_int NPROW = (lapack_int)world_size;
  lapack_int NPCOL = 1;

  lapack_int ictxt = 0;

  sl_init_(&ictxt, &NPROW, &NPCOL);

  lapack_int myrow = -1, mycol = -1, q_nprow = -1, q_npcol = -1;
  blacs_gridinfo_(&ictxt, &q_nprow, &q_npcol, &myrow, &mycol);

  printf("Rank %d/%d -> BLACS ctxt=%d grid %dx%d coords=(%d,%d)\n",
         world_rank, world_size, (int)ictxt, (int)q_nprow, (int)q_npcol,
         (int)myrow, (int)mycol);

  blacs_gridexit_(&ictxt);

  lapack_int cont = 0;
  blacs_exit_(&cont);
}
