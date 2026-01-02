import numpy as np
import pandas as pd
import os
import logging
from typing import List, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
import config
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Preprocessor:
    def __init__(self, output_dir: str = "../output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.train_df: Optional[pd.DataFrame] = None
        self.test_df: Optional[pd.DataFrame] = None
        self.train_labels: Optional[pd.Series] = None
        self.test_labels: Optional[pd.Series] = None
        self.scaler = StandardScaler()
        self.dummy_columns: Optional[pd.Index] = None #Store dummy column names
        self.numeric_columns: Optional[pd.Index] = config.NUMERIC #Store numeric column names
        self.svd = None
        logging.info("Preprocessor initialized.")

    def load_train_data(self, df: pd.DataFrame, label_col: str) -> None:
        logging.info("Loading training data...")
        try:
            if label_col not in df.columns:
                raise ValueError(f"Label column '{label_col}' not found in the dataset.")
            self.train_df = df.drop(columns=[label_col]).copy()
            self.train_labels = df[label_col]
            self.train_df.replace([np.inf, -np.inf], np.nan, inplace=True)
            logging.info(f"Training data loaded successfully with shape: {self.train_df.shape}")
        except Exception as e:
            logging.error(f"Error loading training data: {e}")
            raise

    def load_test_data(self, df: pd.DataFrame, label_col: str) -> None:
        logging.info("Loading test data...")
        try:
            if label_col not in df.columns:
                raise ValueError(f"Label column '{label_col}' not found in the dataset.")
            self.test_df = df.drop(columns=[label_col]).copy()
            self.test_labels = df[label_col]
            self.test_df.replace([np.inf, -np.inf], np.nan, inplace=True)
            logging.info(f"Test data loaded successfully with shape: {self.test_df.shape}")
        except Exception as e:
            logging.error(f"Error loading test data: {e}")
            raise

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.info("Handling missing values...")
        try:
            for col in df.columns:
                fill_value = df[col].mode()[0] if df[col].dtype == 'object' else df[col].median()
                df[col].fillna(fill_value, inplace=True)
            logging.info("Missing values handled successfully.")
            return df
        except Exception as e:
            logging.error(f"Error handling missing values: {e}")
            raise

    def normalize_data(self, df: pd.DataFrame, left_skewed: List[str], right_skewed: List[str]) -> pd.DataFrame:
        logging.info("Normalizing data...")
        try:
            for col in right_skewed:
                if col in df.columns:
                    df[col] = np.log1p(df[col])
            for col in left_skewed:
                if col in df.columns:
                    df[col] = df[col] ** 2
            logging.info("Data normalization completed.")
            return df
        except Exception as e:
            logging.error(f"Error normalizing data: {e}")
            raise

    def drop_unnecessary_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.info("Dropping unnecessary columns...")
        try:
            cols_to_drop = df.nunique()[df.nunique() == 1].index.tolist()
            df.drop(columns=cols_to_drop, inplace=True)
            logging.info("Unnecessary columns dropped successfully.")
            return df
        except Exception as e:
            logging.error(f"Error dropping unnecessary columns: {e}")
            raise

    def convert_edecimal_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert EDecimal values to regular Python types to avoid unhashable type errors."""
        logging.info("Converting EDecimal values to regular Python types...")
        try:
            df_copy = df.copy()
            for col in df_copy.columns:
                # Check if column contains EDecimal values
                if df_copy[col].dtype == 'object':
                    # Convert EDecimal values to float, keep other values as is
                    def convert_value(val):
                        if hasattr(val, '__class__') and 'EDecimal' in str(type(val)):
                            try:
                                return float(val)
                            except (ValueError, TypeError):
                                return val
                        elif isinstance(val, Decimal):
                            return float(val)
                        return val
                    
                    df_copy[col] = df_copy[col].apply(convert_value)
            
            return df_copy
        except Exception as e:
            logging.error(f"Error converting EDecimal values: {e}")
            raise

    def encode_categorical_features(self, df: pd.DataFrame, train_mode: bool = True) -> pd.DataFrame:
        logging.info(f"Encoding categorical features (train_mode={train_mode})...")
        try:
            # Convert EDecimal values before encoding
            df_converted = self.convert_edecimal_values(df)
            
            if train_mode:
                # When encoding training data, create the dummy columns and store them
                dummies = pd.get_dummies(df_converted, drop_first=True, dtype=int)
                self.dummy_columns = dummies.columns  # Store the column names
                return dummies
            else:
                # When encoding test data, ensure it has the same dummy columns as training data
                if self.dummy_columns is None:
                    raise ValueError("Training data must be processed first to determine the correct columns.")
                
                encoded_df = pd.get_dummies(df_converted, drop_first=True, dtype=int)
                missing_cols = set(self.dummy_columns) - set(encoded_df.columns)
                for col in missing_cols:
                    encoded_df[col] = 0  # Add missing columns with zeros

                # Ensure the order of columns is the same as the training data
                encoded_df = encoded_df.reindex(columns=self.dummy_columns, fill_value=0)
                return encoded_df
        except Exception as e:
            logging.error(f"Error encoding categorical features: {e}")
            raise

    def standardize_features(self, df: pd.DataFrame, train_mode: bool = True) -> pd.DataFrame:
        logging.info("Standardizing features...")
        try:
            numeric_columns = df.select_dtypes(include=['number']).columns
            if train_mode:
                df[numeric_columns] = self.scaler.fit_transform(df[numeric_columns])
            else:
                df[numeric_columns] = self.scaler.transform(df[numeric_columns])
            logging.info("Feature standardization completed.")
            return df
        except Exception as e:
            logging.error(f"Error standardizing features: {e}")
            raise

    def remove_outliers(self, df: pd.DataFrame, labels: pd.Series, threshold: float = 3.0) -> tuple[pd.DataFrame, pd.Series]:
        logging.info("Removing outliers...")
        try:
            if self.numeric_columns is None:
                raise ValueError("drop_unnecessary_columns must be called before this function to know the numerical columns")
            mask = (np.abs(df[self.numeric_columns]) < threshold).all(axis=1)
            df = df[mask]
            labels = labels[mask]
            logging.info(f"Outliers removed successfully.")
            return df, labels
        except Exception as e:
            logging.error(f"Error removing outliers: {e}")
            raise

    def apply_svd(self, df: pd.DataFrame, train_mode: bool = True, n_components: int = 37) -> pd.DataFrame:
        logging.info("Applying SVD...")
        try:
            if train_mode:
                self.svd = TruncatedSVD(n_components=n_components)
                return pd.DataFrame(self.svd.fit_transform(df))
            else:
                if self.svd is None:
                    raise ValueError("Train data needs to be processed first, so the SVD can be fit")
                return pd.DataFrame(self.svd.transform(df))
        except Exception as e:
            logging.error(f"Error applying SVD: {e}")
            raise

    def process(self, n_components: int = 37) -> None:
        if self.train_df is None:
            raise ValueError("Training data not loaded.")
        logging.info("Starting data preprocessing pipeline for training data...")
        try:
            self.train_df = self.handle_missing_values(self.train_df)
            # self.train_df = self.normalize_data(self.train_df, left_skewed, right_skewed)
            # self.train_df = self.drop_unnecessary_columns(self.train_df)
            self.train_df = self.encode_categorical_features(self.train_df, train_mode=True)
            self.train_df = self.standardize_features(self.train_df, train_mode=True)
            self.train_df, self.train_labels = self.remove_outliers(self.train_df, self.train_labels)
            self.train_df = self.apply_svd(self.train_df, train_mode=True, n_components=n_components)
            logging.info("Data preprocessing pipeline completed successfully for training data.")
        except Exception as e:
            logging.error(f"Error during training preprocessing pipeline: {e}")
            raise

    def transform(self, n_components: int = 37) -> None:
        if self.test_df is None:
            raise ValueError("Test data not loaded.")
        logging.info("Starting data preprocessing pipeline for test data...")
        try:
            self.test_df = self.handle_missing_values(self.test_df)
            # self.test_df = self.normalize_data(self.test_df, left_skewed, right_skewed)
            # self.test_df = self.drop_unnecessary_columns(self.test_df)
            self.test_df = self.encode_categorical_features(self.test_df, train_mode=False)
            self.test_df = self.standardize_features(self.test_df, train_mode=False)
            self.test_df = self.apply_svd(self.test_df, train_mode=False, n_components=n_components)
            logging.info("Data preprocessing pipeline completed successfully for test data.")
        except Exception as e:
            logging.error(f"Error during test preprocessing pipeline: {e}")
            raise

    def save_data(self, filename: str = "processed_data.csv", mode: str = 'train') -> None:
        if mode == 'train' and self.train_df is None:
            raise ValueError("Training data not loaded.")
        if mode == 'test' and self.test_df is None:
            raise ValueError("Test data not loaded.")
        
        logging.info(f"Saving {mode} data...")
        try:
            if mode == 'train':
                self.train_df.to_csv(os.path.join(self.output_dir, filename), index=False)
            else:
                self.test_df.to_csv(os.path.join(self.output_dir, filename), index=False)
            logging.info(f"Data saved successfully at {os.path.join(self.output_dir, filename)}.")
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            raise