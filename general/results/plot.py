import warnings
from statistics import mean, variance

import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

from general.results import out
from general.config import cfg
import os
import torch

warnings.filterwarnings("ignore")


def mkfig(fname, legend=True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            fig, ax = plt.subplots()
            result = func(*args, **kwargs, fig=fig, ax=ax)

            if legend:
                plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(out.get_path(), fname))
            plt.close("all")

            return result
        return wrapper
    return decorator


@mkfig("loss.png")
def show_loss(loss, lr=None, *args, **kwargs):
    """plots loss over time"""

    epoch_size = cfg.LOADER.SIZE // (
        cfg.LOADER.BATCH_SIZE * cfg.world_size * cfg.SOLVER.GRAD_ACC_EVERY
    )
    #   # len(loss) // cfg.SOLVER.MAX_EPOCH
    X = [i for i, _ in enumerate(loss)]
    plt.plot(X, loss, label="loss")
    if lr:
        plt.plot(X, lr, label="learning rate")

    epochs = list(range(cfg.SOLVER.MAX_EPOCH))
    # plt.xticks([i * epoch_size for i in epochs], epochs)


@mkfig("accuracy.png")
def show_accuracy(acc,  *args, **kwargs):
    """plots accuracy over time"""
    plt.plot([i for i, _ in enumerate(acc)], acc, color='r', label="accuracy")


def calc_confusion(Y, Yh):
    """calculate confusion matrix"""

    confusion = torch.zeros((cfg.LOADER.NCLASSES, cfg.LOADER.NCLASSES))
    Y, Yh = torch.argmax(Y, 1), torch.argmax(Yh, 1)
    for y, yh in zip(Y.view(-1), Yh.view(-1)):
        confusion[y, yh] += 1

    acc = confusion.diag().sum() / confusion.sum(1).sum()
    return confusion, acc



@mkfig("confusion.png", legend=False)
def show_confusion(Y, Yh, *args, **kwargs):
    """builds confusion matrix"""

    confusion, acc = calc_confusion(Y, Yh)

    # plt.rcParams.update({"font.size": 18}) # way too big...
    plt.matshow(confusion, cmap=plt.cm.Blues, alpha=0.3)

    for i in range(confusion.shape[0]):
        for j in range(confusion.shape[1]):
            plt.text(x=j, y=i, s=int(confusion[i, j]), va="center", ha="center", size="xx-large")

    # plt.title(f"Confusion Matrix")
    plt.xlabel("Predictions")
    plt.ylabel("Ground Truth")


@mkfig("embed.png")
def show_tsne(Y, Yh, *args, **kwargs):
    """docstring"""
    # ax = fig.add_subplot(projection="3d")

    tsne = TSNE(n_components=2, random_state=cfg.SOLVER.SEED)  # could do 3 dim
    Yh = tsne.fit_transform(Yh.cpu().numpy(), Y.cpu().numpy())

    scatter = plt.scatter(Yh[:, 0], Yh[:, 1], c=Y.view(-1).tolist(), alpha=0.3)
    # ax.scatter(Yh[:,0], Yh[:,1],Yh[:,2], c=Y.view(-1).tolist())
    # ax.view_init(0, 180)
    plt.legend(*scatter.legend_elements())


def calc_dprime(Y, Yh):
    """measures if positive pairs are different from negative pairs"""

    phist = {i: [] for i in range(cfg.LOADER.NCLASSES)}
    nhist = {i: [] for i in range(cfg.LOADER.NCLASSES)}
    C = set(range(cfg.LOADER.NCLASSES))

    Y = Y.view(-1)

    for c in C:
        pos = Yh[(Y == c).view(-1)]
        neg = Yh[(Y != c).view(-1)]

        dist = lambda a, b: (a - b).pow(2).sum(-1).sqrt()
        angle = (
            lambda a, b: torch.acos(torch.dot(a, b) / (torch.linalg.norm(a) * torch.linalg.norm(b)))
            * 180
            / 3.141592
        )

        n = len(pos) // 2
        ppairs = [angle(i, j) for i, j in zip(pos[:n], pos[n : 2 * n])]
        npairs = [angle(i, j) for i, j in zip(pos[:n], neg[n : 2 * n])]

        phist[c] =  ppairs
        nhist[c] =  npairs

    pall, nall = [], []
    for c in C:
        pall += [float(x) if not torch.isnan(x) else -1 for x in phist[c][:1000]]
        nall += [float(x) for x in nhist[c][:1000]]

    dprime = (2**0.5 * abs(mean(pall) - mean(nall))) / ((variance(pall) + variance(nall)) ** 0.2)
    return pall, nall, dprime


@mkfig("dprime.png")
def show_dprime(Y, Yh, *args, **kwargs):
    """docstring"""

    pall, nall, dprime = calc_dprime(Y, Yh)

    plt.hist(pall, label="positive", bins=30, alpha=0.5)
    plt.hist(nall, label="negative", bins=30, alpha=0.5)

    plt.title( f"Population Distance (d_prime={round(dprime,4)})")
    plt.xlabel("angle")
    plt.ylabel("frequency")


PLOTS = {
    "LOSS": show_loss,
    "CONFUSION": show_confusion,
    "TSNE": show_tsne,
    "DPRIME": show_dprime,
}
