"""
Dataset splitting utility for ResumeLens AI.
Ensures document-level grouping to prevent data leakage between train/val/test splits.
"""

import random
from typing import Tuple, List, Dict, Any
import pandas as pd


def split_dataframe_by_document(
    df: pd.DataFrame,
    doc_col: str = "document_id",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits a DataFrame by document_id so that all rows associated with a document
    stay strictly within one split, eliminating leakage.
    """
    random.seed(random_seed)
    unique_docs = sorted(list(df[doc_col].unique()))
    random.shuffle(unique_docs)

    n_train = max(1, int(len(unique_docs) * train_ratio))
    n_val = max(1, int(len(unique_docs) * val_ratio))

    train_docs = set(unique_docs[:n_train])
    val_docs = set(unique_docs[n_train:n_train + n_val])
    test_docs = set(unique_docs[n_train + n_val:])

    train_df = df[df[doc_col].isin(train_docs)].copy()
    val_df = df[df[doc_col].isin(val_docs)].copy()
    test_df = df[df[doc_col].isin(test_docs)].copy()

    return train_df, val_df, test_df
