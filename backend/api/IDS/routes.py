from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Depends
from pydantic import BaseModel
import pandas as pd
import io
import logging
from src.IDS.training.predict import predict_new_data
from src.Capture.processpcap import process_pcap
import os
import config
import tempfile
from api.auth import get_current_active_user

ids_router = APIRouter()

@ids_router.post("/", dependencies=[Depends(get_current_active_user)])
async def predict(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        contents = await file.read()
        
        # Try different encodings
        text_content = None
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                text_content = contents.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if text_content is None:
            raise HTTPException(status_code=400, detail="Unable to decode file. Please ensure it's a valid CSV file with proper encoding.")
        
        # Parse CSV with error handling
        try:
            new_df = pd.read_csv(io.StringIO(text_content))
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")
        except pd.errors.ParserError as e:
            raise HTTPException(status_code=400, detail=f"Error parsing CSV file: {str(e)}")
        
        # Validate data format
        if new_df.empty:
            raise HTTPException(status_code=400, detail="The uploaded CSV file contains no data.")
        
        # Expected columns (without 'class' column for prediction)
        expected_columns = [
            'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes', 
            'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in', 
            'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations', 
            'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login', 
            'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate', 
            'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate', 
            'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count', 
            'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate', 
            'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate', 
            'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'other'
        ]
        
        # Check if the data has the expected columns (allow for 'class' column to be present or missing)
        if 'class' in new_df.columns:
            # Remove class column if present (for prediction we don't need it)
            new_df = new_df.drop(columns=['class'])
        
        # Handle missing 'other' column (common in some KDD versions)
        if 'other' not in new_df.columns:
            new_df['other'] = 0

        missing_columns = set(expected_columns) - set(new_df.columns)
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(sorted(missing_columns))}. Please ensure your CSV file has the correct KDD Cup 99 format."
            )
        
        # Reorder columns to match expected format
        new_df = new_df[expected_columns]
        
        logging.info(f"Processing prediction for {len(new_df)} rows")
        predictions = predict_new_data(new_df, config.MODEL_SAVE_PATH, config.PREPROCESSOR_SAVE_PATH, config.MAPPING_SAVE_PATH, config.DEVICE)
        
        # Create response with predictions and row details
        result_data = []
        for i, (_, row) in enumerate(new_df.iterrows()):
            result_data.append({
                "row_id": i + 1,
                "prediction": predictions[i],
                "features": row.to_dict()
            })
        
        return {
            "filename": file.filename,
            "total_rows": len(predictions),
            "predictions": result_data,
            "summary": {
                "normal": sum(1 for p in predictions if 'normal' in p.lower()),
                "attacks": sum(1 for p in predictions if 'normal' not in p.lower())
            }
        }
        
    except HTTPException as he:
        logging.error(f"HTTP Exception in prediction: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@ids_router.post("/pcap", dependencies=[Depends(get_current_active_user)])
async def predict_pcap(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pcap', '.pcapng')):
            raise HTTPException(status_code=400, detail="Only PCAP/PCAPNG files are supported")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pcap') as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_pcap_path = temp_file.name
        
        try:
            # Process PCAP file to extract features
            logging.info(f"Processing PCAP file: {file.filename}")
            features = process_pcap(temp_pcap_path)
            
            if not features:
                raise HTTPException(status_code=400, detail="No network connections found in PCAP file")
            
            # Convert features to DataFrame
            new_df = pd.DataFrame(features)
            
            # Ensure 'other' column exists (model requirement)
            if 'other' not in new_df.columns:
                new_df['other'] = 0
            
            logging.info(f"Extracted {len(features)} connections from PCAP file")
            
            # Get predictions
            predictions = predict_new_data(new_df, config.MODEL_SAVE_PATH, config.PREPROCESSOR_SAVE_PATH, config.MAPPING_SAVE_PATH, config.DEVICE)
            
            # Create response with predictions and connection details
            result_data = []
            for i, (feature_row, prediction) in enumerate(zip(features, predictions)):
                result_data.append({
                    "connection_id": i + 1,
                    "src_ip": feature_row.get('src_ip', 'N/A'),
                    "dst_ip": feature_row.get('dst_ip', 'N/A'), 
                    "service": feature_row.get('service', 'N/A'),
                    "protocol": feature_row.get('protocol_type', 'N/A'),
                    "prediction": prediction,
                    "duration": feature_row.get('duration', 0),
                    "src_bytes": feature_row.get('src_bytes', 0),
                    "dst_bytes": feature_row.get('dst_bytes', 0)
                })
            
            return {
                "filename": file.filename,
                "total_connections": len(features),
                "predictions": result_data,
                "summary": {
                    "normal": sum(1 for p in predictions if 'normal' in p.lower()),
                    "attacks": sum(1 for p in predictions if 'normal' not in p.lower())
                }
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pcap_path):
                os.unlink(temp_pcap_path)
                
    except HTTPException as he:
        logging.error(f"HTTP Exception in PCAP prediction: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logging.error(f"PCAP prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PCAP file: {str(e)}")