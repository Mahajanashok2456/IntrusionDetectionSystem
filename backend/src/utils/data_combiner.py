import pandas as pd
import numpy as np
import logging
import os
from typing import Optional, Tuple
import config

def combine_datasets(
    original_data_path: str,
    synthetic_data_path: Optional[str] = None,
    synthetic_data: Optional[pd.DataFrame] = None,
    output_path: Optional[str] = None,
    balance_classes: bool = True,
    shuffle: bool = True
) -> Tuple[pd.DataFrame, str]:
    """
    Combine original and synthetic datasets for training.
    
    Args:
        original_data_path: Path to the original training data
        synthetic_data_path: Path to synthetic data CSV file (optional)
        synthetic_data: DataFrame containing synthetic data (optional)
        output_path: Path to save the combined dataset (optional)
        balance_classes: Whether to balance class distribution
        shuffle: Whether to shuffle the combined dataset
        
    Returns:
        Tuple of (combined_dataframe, output_file_path)
    """
    try:
        # Load original data
        logging.info(f"Loading original data from {original_data_path}")
        original_df = pd.read_csv(original_data_path)
        logging.info(f"Original dataset shape: {original_df.shape}")
        
        # Load synthetic data
        if synthetic_data is not None:
            synthetic_df = synthetic_data.copy()
        elif synthetic_data_path and os.path.exists(synthetic_data_path):
            logging.info(f"Loading synthetic data from {synthetic_data_path}")
            synthetic_df = pd.read_csv(synthetic_data_path)
        else:
            logging.info("No synthetic data provided, using original data only")
            combined_df = original_df.copy()
            if shuffle:
                combined_df = combined_df.sample(frac=1).reset_index(drop=True)
            
            if output_path:
                combined_df.to_csv(output_path, index=False)
                return combined_df, output_path
            else:
                return combined_df, original_data_path
        
        logging.info(f"Synthetic dataset shape: {synthetic_df.shape}")
        
        # Ensure column compatibility
        if not all(col in synthetic_df.columns for col in original_df.columns):
            logging.warning("Column mismatch between original and synthetic data")
            # Align columns
            synthetic_df = synthetic_df.reindex(columns=original_df.columns, fill_value=0)
        
        # Combine datasets
        logging.info("Combining original and synthetic datasets...")
        combined_df = pd.concat([original_df, synthetic_df], ignore_index=True)
        
        # Balance classes if requested
        if balance_classes and 'class' in combined_df.columns:
            logging.info("Balancing class distribution...")
            combined_df = balance_class_distribution(combined_df)
        
        # Shuffle if requested
        if shuffle:
            logging.info("Shuffling combined dataset...")
            combined_df = combined_df.sample(frac=1).reset_index(drop=True)
        
        logging.info(f"Combined dataset shape: {combined_df.shape}")
        
        # Save combined dataset
        if output_path is None:
            output_path = os.path.join(config.BASE_DIR, 'data', 'processed', 'combined_training_data.csv')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        combined_df.to_csv(output_path, index=False)
        logging.info(f"Combined dataset saved to {output_path}")
        
        return combined_df, output_path
        
    except Exception as e:
        logging.error(f"Error combining datasets: {e}")
        raise

def balance_class_distribution(df: pd.DataFrame, target_column: str = 'class') -> pd.DataFrame:
    """
    Balance the class distribution in the dataset using oversampling.
    
    Args:
        df: Input dataframe
        target_column: Name of the target column
        
    Returns:
        Balanced dataframe
    """
    try:
        if target_column not in df.columns:
            logging.warning(f"Target column '{target_column}' not found. Skipping class balancing.")
            return df
        
        # Get class counts
        class_counts = df[target_column].value_counts()
        logging.info(f"Original class distribution:\n{class_counts}")
        
        # Find the maximum class count
        max_count = class_counts.max()
        
        # Oversample minority classes
        balanced_dfs = []
        for class_label in class_counts.index:
            class_df = df[df[target_column] == class_label]
            current_count = len(class_df)
            
            if current_count < max_count:
                # Oversample this class
                n_samples_needed = max_count - current_count
                oversampled = class_df.sample(n=n_samples_needed, replace=True)
                balanced_dfs.append(pd.concat([class_df, oversampled]))
            else:
                balanced_dfs.append(class_df)
        
        # Combine all balanced classes
        balanced_df = pd.concat(balanced_dfs, ignore_index=True)
        
        # Log new distribution
        new_class_counts = balanced_df[target_column].value_counts()
        logging.info(f"Balanced class distribution:\n{new_class_counts}")
        
        return balanced_df
        
    except Exception as e:
        logging.error(f"Error balancing class distribution: {e}")
        return df

def get_dataset_statistics(df: pd.DataFrame) -> dict:
    """
    Get comprehensive statistics about the dataset.
    
    Args:
        df: Input dataframe
        
    Returns:
        Dictionary containing dataset statistics
    """
    stats = {
        'total_samples': len(df),
        'total_features': len(df.columns),
        'missing_values': df.isnull().sum().sum(),
        'duplicate_rows': df.duplicated().sum(),
        'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
    }
    
    # Class distribution if 'class' column exists
    if 'class' in df.columns:
        stats['class_distribution'] = df['class'].value_counts().to_dict()
        stats['num_classes'] = df['class'].nunique()
    
    # Data types
    stats['data_types'] = df.dtypes.value_counts().to_dict()
    
    return stats