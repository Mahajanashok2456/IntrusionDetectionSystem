from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import logging
import os
import asyncio
from src.CTGAN.training.generate import generate_samples
from src.IDS.training.train_model import main as train_ids_model
from api.auth import get_current_active_user
import config

training_router = APIRouter()

class TrainingInput(BaseModel):
    num_synthetic_samples: int = 1000
    use_synthetic_data: bool = True
    retrain_ctgan: bool = False

@training_router.post("/", dependencies=[Depends(get_current_active_user)])
async def train_models(data: TrainingInput):
    """
    Train IDS models with optional synthetic data augmentation
    """
    try:
        logging.info(f"Starting training with {data.num_synthetic_samples} synthetic samples")
        
        # Step 1: Generate synthetic data if requested
        synthetic_data_path = None
        if data.use_synthetic_data:
            try:
                logging.info("Generating synthetic data...")
                synthetic_data = generate_samples(data.num_synthetic_samples, batch_size=500)
                
                # Save synthetic data to file
                synthetic_data_path = os.path.join(config.BASE_DIR, 'data', 'synthetic', 'synthetic_training_data.csv')
                os.makedirs(os.path.dirname(synthetic_data_path), exist_ok=True)
                
                synthetic_df = pd.DataFrame(synthetic_data)
                synthetic_df.to_csv(synthetic_data_path, index=False)
                logging.info(f"Synthetic data saved to {synthetic_data_path}")
                
            except Exception as e:
                logging.error(f"Error generating synthetic data: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to generate synthetic data: {str(e)}")
        
        # Step 2: Combine original and synthetic data
        try:
            logging.info("Preparing training data...")
            
            # Load original training data
            original_train_path = os.path.join(config.BASE_DIR, 'data', 'raw', 'KDDTrain+.csv')
            original_df = pd.read_csv(original_train_path)
            
            if data.use_synthetic_data and synthetic_data_path:
                # Combine original and synthetic data
                synthetic_df = pd.read_csv(synthetic_data_path)
                combined_df = pd.concat([original_df, synthetic_df], ignore_index=True)
                
                # Save combined dataset
                combined_data_path = os.path.join(config.BASE_DIR, 'data', 'processed', 'combined_training_data.csv')
                os.makedirs(os.path.dirname(combined_data_path), exist_ok=True)
                combined_df.to_csv(combined_data_path, index=False)
                
                logging.info(f"Combined dataset created with {len(original_df)} original + {len(synthetic_df)} synthetic samples")
                training_data_path = combined_data_path
            else:
                training_data_path = original_train_path
                logging.info(f"Using original dataset with {len(original_df)} samples")
                
        except Exception as e:
            logging.error(f"Error preparing training data: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to prepare training data: {str(e)}")
        
        # Step 3: Train IDS models
        try:
            logging.info("Starting IDS model training...")
            
            # Run training in a separate thread to avoid blocking
            await asyncio.to_thread(train_ids_model)
            
            logging.info("IDS model training completed successfully")
            
            return {
                "status": "success",
                "message": "IDS models trained successfully",
                "details": {
                    "synthetic_samples_used": data.num_synthetic_samples if data.use_synthetic_data else 0,
                    "original_samples": len(original_df),
                    "total_training_samples": len(combined_df) if data.use_synthetic_data else len(original_df),
                    "training_data_path": training_data_path,
                    "models_saved_to": config.MODEL_SAVE_PATH
                }
            }
            
        except Exception as e:
            logging.error(f"Error training IDS models: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to train IDS models: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in training pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Training pipeline failed: {str(e)}")

@training_router.get("/status", dependencies=[Depends(get_current_active_user)])
async def get_training_status():
    """
    Get the current status of trained models
    """
    try:
        model_files = [
            "gan_generator.pth",
            "data_transformer.pkl", 
            "CAE1.pth",
            "CAE2.pth", 
            "CAE3.pth",
            "SCAE_GC.pth",
            "preprocessor.pkl",
            "label_mapping.json"
        ]
        
        model_status = {}
        for model_file in model_files:
            model_path = os.path.join(config.MODEL_SAVE_PATH, model_file)
            model_status[model_file] = {
                "exists": os.path.exists(model_path),
                "path": model_path,
                "size_mb": round(os.path.getsize(model_path) / (1024*1024), 2) if os.path.exists(model_path) else 0
            }
        
        return {
            "models": model_status,
            "model_directory": config.MODEL_SAVE_PATH,
            "all_models_available": all(status["exists"] for status in model_status.values())
        }
        
    except Exception as e:
        logging.error(f"Error checking model status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check model status: {str(e)}")