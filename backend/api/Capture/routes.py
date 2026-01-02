from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel
import pandas as pd
from src.Capture.processpcap import process_pcap, save_to_arff
from src.Capture.capture import capture_packets_tshark, capture_packets_tshark_wrapper
import config
import io
import logging
import asyncio
from api.auth import get_current_active_user

class CaptureInput(BaseModel):
    duration: int

capture_router = APIRouter()

@capture_router.post("/", response_class=Response, dependencies=[Depends(get_current_active_user)])
async def capture_pcap_file(data: CaptureInput):
    try:
        await asyncio.to_thread(capture_packets_tshark_wrapper, data.duration)
        features = process_pcap(config.PCAP_SAVE_PATH)
        save_to_arff(features, config.PCAP_OUTPUT_PATH)
        df = pd.DataFrame(features)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=Captured_data.csv"})
    except Exception as e:
        logging.error(f"Error capturing pcap file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@capture_router.post("/analyze", response_model=dict, dependencies=[Depends(get_current_active_user)])
async def capture_and_analyze(data: CaptureInput):
    try:
        # 1. Capture Packets
        await asyncio.to_thread(capture_packets_tshark_wrapper, data.duration)
        
        # 2. Process Capture File
        features = process_pcap(config.PCAP_SAVE_PATH)
        if not features:
             raise HTTPException(status_code=400, detail="No network packets captured. Ensure traffic is flowing and Tshark is installed.")
             
        # 3. Prepare Data for Prediction
        from src.IDS.training.predict import predict_new_data
        
        new_df = pd.DataFrame(features)
        
        # Add required 'other' column (default 0 for KDD compatibility)
        if 'other' not in new_df.columns:
            new_df['other'] = 0
            
        logging.info(f"Analyzing {len(new_df)} captured connections...")

        # 4. Run Prediction Model
        predictions = predict_new_data(
            new_df, 
            config.MODEL_SAVE_PATH, 
            config.PREPROCESSOR_SAVE_PATH, 
            config.MAPPING_SAVE_PATH, 
            config.DEVICE
        )

        # 5. Compile Results
        result_data = []
        for i, (feature_row, prediction) in enumerate(zip(features, predictions)):
            result_data.append({
                "connection_id": i + 1,
                "src_ip": feature_row.get('src_ip', 'N/A'), # process_pcap might not return src/dst IPs, it returns features. 
                # Note: process_pcap returns features for the model. 
                # To show IPs, we might need to modify process_pcap or just show the prediction.
                # For now, let's just return the prediction.
                "service": feature_row.get('service', 'N/A'),
                "protocol": feature_row.get('protocol_type', 'N/A'),
                "prediction": prediction
            })

        return {
            "status": "success",
            "total_connections": len(features),
            "summary": {
                "normal": sum(1 for p in predictions if 'normal' in p.lower()),
                "attacks": sum(1 for p in predictions if 'normal' not in p.lower())
            },
            "details": result_data
        }

    except Exception as e:
        logging.error(f"Error during real-time analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))