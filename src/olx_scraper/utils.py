import numpy as np


def split_list(data: list[int], num_chunks: int) -> list[list[int]]:
    """
    Splits a list into a specified number of approximately equal chunks.
    """
    return list(map(lambda x: x.tolist(), np.array_split(data, num_chunks)))
