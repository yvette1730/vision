from general.config import cfg
from general.data.loader import build_loaders
from general.models import build_model
from .tester import Tester

from .newtrainer import Trainer


class Experiment:
    """docstring"""

    def __init__(self):
        model = build_model()
        loaders = build_loaders()
        self.trainer = Trainer(model, loaders["train"])
        self.tester = Tester(self.trainer.model, loaders["test"])
        print('built exp')

    def run(self):
        print('run')
        if cfg.EXP.TRAIN:
            self.trainer.run()
        if cfg.EXP.TEST:
            self.tester.run()


class Split5x2Experiment(Experiment):
    """5 Seeds of 2-fold cross validation"""

    def __init__(self):
        pass

    def run():
        for split in range(5):
            for swap in [0, 1]:
                set_seed(cfg.seed + split)
                cfg.LOADER.SWAP = swap
                super().__init__()
                super().run()


EXPERIMENTS = {
    "DEFAULT": Experiment,
    "5x2": Split5x2Experiment,
}


def build_experiment():
    print(cfg.EXP)
    return EXPERIMENTS[cfg.EXP.BODY]()
