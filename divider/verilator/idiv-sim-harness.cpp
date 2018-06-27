#include "stdio.h"
#include "stdint.h"
#include "verilated.h"
#include "build/VIntDivRem4.h"
#include "../divider_input/cpp_input.dat"

inline void cycle(VIntDivRem4 *model)
{
  model->eval();
  model->clk = 0;
  model->eval();
  model->clk = 1;
  model->eval();
}

int main(int argc, char **argv)
{
  if (argc != 4)
  {
    printf("Please give exactly 3 arguments for (1)trace, (2)ncycle and (3)nbits\n");
    return 1;
  }
  int trace;
  sscanf(argv[1], "%d", &trace);

  long long ncycle;
  sscanf(argv[2], "%lld", &ncycle);

  int nbits;
  sscanf(argv[3], "%d", &nbits);

  VIntDivRem4 *idiv = new VIntDivRem4();

  // Reset the model
  idiv->reset = 1;
  cycle(idiv);
  idiv->reset = 0;
  cycle(idiv);

  long long time = 0, passed = 0;

  int len = (nbits*2-1)/32+1;

  int *ans = new int[len];

  for (long long time=0; time<ncycle; ++time)
  {
    idiv->resp_rdy = 1;
    idiv->req_val  = 1;

    int idx = time % num_inputs;

    for (int i=0; i<len; ++i)
      idiv->req_msg[i] = inp[idx][i];

    idiv->eval();

    if (idiv->req_rdy)
      for (int i=0; i<len; ++i)
        ans[i] = oup[idx][i];

    cycle(idiv);

    if (trace)
    {
      printf("req_rdy: %d resp_val: %d\n", idiv->req_rdy, idiv->resp_val);
    }

    if (idiv->resp_val)
    {
      for (int i=0; i<len; ++i)
        if (idiv->resp_msg[i] != ans[i])
        {
          printf("Test Failed\n");
          return 1;
        }
      passed += 1;
    }
  }

  printf("[%lld passed] idiv", passed );

  return 0;
}
