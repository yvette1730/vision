from torch import optim
from torch.distributed.optim import ZeroRedundancyOptimizer as ZeRO

from general.config import cfg

import torch

from .lamb import LAMB

OPTIMIZERS = {
    "ADAM": optim.Adam,
    "SGD": optim.SGD,
    "LAMB": LAMB,
    "ZERO": ZeRO,
}


def make_optimizer(params):
    # TODO: add support for *args where args are objects to be optimized
    # ie: make_optim(*args, params):
    # assert not (args and params)

    print(cfg.SOLVER.OPTIM)

    kwargs = dict(
        params=params,
        lr=cfg.SOLVER.OPTIM.LR,
        weight_decay=float(cfg.SOLVER.OPTIM.DECAY),
    )

    if cfg.SOLVER.OPTIM.BODY == "SGD":
        kwargs["momentum"] = cfg.SOLVER.OPTIM.MOMENTUM
    if cfg.SOLVER.OPTIM.BODY == "ADAM":
        kwargs["betas"] = cfg.SOLVER.OPTIM.BETAS
    if cfg.SOLVER.OPTIM.BODY == "ZERO":
        kwargs["optimizer_class"] = optim.Adam

    optimizer =  OPTIMIZERS[cfg.SOLVER.OPTIM.BODY](**kwargs)
    return optimizer
