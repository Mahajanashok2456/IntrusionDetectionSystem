from fastapi import APIRouter, Body, HTTPException, Response, Depends
from pydantic import BaseModel
import pandas as pd
import io
from src.CTGAN.training.generate import generate_samples
from api.auth import get_current_active_user

ctgan_router = APIRouter()

class GenerateInput(BaseModel):
    num_samples: int
    batch_size: int = 50

@ctgan_router.post("/", response_class=Response, dependencies=[Depends(get_current_active_user)])
async def generate(data: GenerateInput):
    try:
        generated_data = generate_samples(data.num_samples, data.batch_size)
        df = pd.DataFrame(generated_data)
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=synthetic_data.csv"})
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"CTGAN model not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating synthetic data: {str(e)}")
