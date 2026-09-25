"""minipipe — сквозной мини-пайплайн курса. Только numpy."""

from minipipe.distance import squared_distances
from minipipe.kmeans import KMeans
from minipipe.knn import KNN
from minipipe.metrics import accuracy, confusion_counts
from minipipe.prep import minmax_scale, shuffled, standardize
from minipipe.split import train_test_split

__version__ = "0.1.0"

__all__ = [
    "KNN",
    "KMeans",
    "__version__",
    "accuracy",
    "confusion_counts",
    "minmax_scale",
    "shuffled",
    "squared_distances",
    "standardize",
    "train_test_split",
]
