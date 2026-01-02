import os
import json
import pickle
import logging
import torch
import numpy as np
import pandas as pd
from ..architectures.auto_encoder import ContractiveAutoEncoder
from ..architectures.SGAE_GC import SCAE_GC

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import config for dynamic paths
import config

# Constants
RIGHT_SKEWED = ['0', '491', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '0.10', '0.11', '0.12', '0.13', '0.14', '0.15', '0.16', '0.18', '2', '2.1', '0.00', '0.00.1', '0.00.2']
LEFT_SKEWED = ['20', '150', '1.00']
MODEL_SAVE_PATH = config.MODEL_SAVE_PATH
PREPROCESSOR_SAVE_PATH = config.PREPROCESSOR_SAVE_PATH
MAPPING_SAVE_PATH = config.MAPPING_SAVE_PATH
DEVICE = config.DEVICE

def load_preprocessor(save_path):
    try:
        with open(save_path, 'rb') as f:
            preprocessor = pickle.load(f)
        logging.info("Preprocessor loaded successfully.")
        return preprocessor
    except FileNotFoundError:
        logging.error("Preprocessor file not found.")
        raise
    except Exception as e:
        logging.error(f"Error loading preprocessor: {e}")
        raise

def load_mapping(save_path):
    try:
        with open(save_path, 'r') as f:
            mapping = json.load(f)
        logging.info("Label mapping loaded successfully.")
        return {int(v): k for k, v in mapping.items()}  # Reverse mapping for decoding
    except FileNotFoundError:
        logging.error("Label mapping file not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding JSON label mapping.")
        raise
    except Exception as e:
        logging.error(f"Error loading label mapping: {e}")
        raise

def load_model(model_class, model_path, device, *args):
    try:
        model = model_class(*args).to(device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        logging.info(f"Model {model_class.__name__} loaded successfully from {model_path}.")
        return model
    except FileNotFoundError:
        logging.error(f"Model file {model_path} not found.")
        raise
    except Exception as e:
        logging.error(f"Error loading model {model_class.__name__}: {e}")
        raise

def predict_new_data(new_df, model_save_path, preprocessor_save_path, mapping_save_path, device='cpu'):
    try:
        # Load Preprocessor
        preprocessor = load_preprocessor(preprocessor_save_path)
        
        # Load Label Mapping
        label_mapping = load_mapping(mapping_save_path)

        # For prediction, we don't have a class column, so we set test_df directly
        preprocessor.test_df = new_df.copy()
        preprocessor.test_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        preprocessor.test_labels = None  # No labels for prediction
        logging.info(f"Prediction data loaded successfully with shape: {preprocessor.test_df.shape}")
        
        preprocessor.transform()
        features = torch.tensor(preprocessor.test_df.values, dtype=torch.float32).to(device)
        logging.info("New data loaded and preprocessed successfully.")

        # Load trained autoencoders
        cae1 = load_model(ContractiveAutoEncoder, os.path.join(model_save_path, "CAE1.pth"), device, 37, 80)
        cae2 = load_model(ContractiveAutoEncoder, os.path.join(model_save_path, "CAE2.pth"), device, 80, 40)
        cae3 = load_model(ContractiveAutoEncoder, os.path.join(model_save_path, "CAE3.pth"), device, 40, 20)

        # Load SCAE-GC model
        scae_gc = load_model(SCAE_GC, os.path.join(model_save_path, "SCAE_GC.pth"), device, 37, cae1, cae2, cae3, 20, 20)

        # Get predictions
        with torch.no_grad():
            outputs = scae_gc(features)

        # Convert predictions to labels
        predicted_labels = np.argmax(outputs.cpu().numpy(), axis=1)
        decoded_labels = [label_mapping.get(label, "Unknown") for label in predicted_labels]

        logging.info("Predictions generated successfully.")
        return decoded_labels
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except pd.errors.EmptyDataError:
        logging.error("CSV file is empty.")
        raise
    except Exception as e:
        logging.error(f"Error in prediction process: {e}")
        raise

# if __name__ == "__main__":
#     new_data_path = r"C:\Users\Vishruth V Srivatsa\OneDrive\Desktop\IDS\data\raw\KDDTest+.csv"
#     new_df = pd.read_csv(new_data_path)
#     try:
#         predictions = predict_new_data(new_df, MODEL_SAVE_PATH, PREPROCESSOR_SAVE_PATH, MAPPING_SAVE_PATH, DEVICE)
#         print(predictions)
#     except Exception as e:
#         logging.error(f"Prediction failed: {e}")