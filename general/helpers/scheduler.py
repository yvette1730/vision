from torch.optim.lr_scheduler import (
    MultiStepLR,
    ReduceLROnPlateau,
    StepLR,
    _LRScheduler,
)
from general.config import cfg
import torch


class PolyScheduler(_LRScheduler):
    def __init__(self, optimizer, last_epoch=-1):
        # nbatch = cfg.LOADER.SIZE // cfg.LOADER.BATCH_SIZE
        self.max_steps = cfg.SOLVER.MAX_ITER
        self.warmup_steps = self.max_steps // 10 # cfg.SCHEDULER.WARMUP_ITER

        self.base_lr = cfg.SOLVER.OPTIM.LR
        self.warmup_lr_init = 1e-4
        self.power = 2

        super(PolyScheduler, self).__init__(optimizer, -1, False)
        self.last_epoch = last_epoch

    def get_warmup_lr(self):
        alpha = float(self.last_epoch) / float(self.warmup_steps)
        return [self.base_lr * alpha for _ in self.optimizer.param_groups]

    def get_lr(self):
        if self.last_epoch == -1:
            return [self.warmup_lr_init for _ in self.optimizer.param_groups]
        if self.last_epoch < self.warmup_steps:
            return self.get_warmup_lr()

        else:
            alpha = pow(
                1
                - float(self.last_epoch - self.warmup_steps)
                / float(self.max_steps - self.warmup_steps),
                self.power,
            )
            return [self.base_lr * alpha for _ in self.optimizer.param_groups]


schedulers = {
    "STEP": lambda optim: StepLR(optim, step_size=1, gamma=cfg.SCHEDULER.GAMMA),
    "POLY": PolyScheduler,
}


def make_scheduler(optimizer):
    print(cfg.SCHEDULER)
    return schedulers[cfg.SCHEDULER.BODY](optimizer)


def test_scheduler():
    """docstring"""

    net = torch.nn.Linear(1, 1)
    scheduler = make_scheduler(torch.optim.Adam(net.parameters()))
    for _ in range(cfg.SOLVER.MAX_ITER):
        lr = scheduler.get_lr()
        scheduler.step()
        print(lr)


if __name__ == "__main__":
    test_scheduler()
